"""Repeatable mocked services + explicit disposable SQL. Never calls Railway/EODHD."""
import copy,io,json,os,time,unittest,uuid
from contextlib import ExitStack,redirect_stdout
from datetime import datetime,timezone,timedelta
from unittest.mock import MagicMock,patch
from urllib.error import HTTPError
import psycopg
from cryptography.fernet import Fernet
from research.daily_shadow_v3.adapter import HTTPTransport,VendorError,EODHDAdapter
from research.daily_shadow_v3.fixtures import FixtureTransport,fixture_models,clock,SESSION,ISSUED
from research.daily_shadow_v3.legal import fixture_permit
from research.daily_shadow_v3.store import ResearchStore
from .diagnostics import RunAudit,exception_fields,redact
from .readiness import collect_stable,fingerprint
from .runtime import run_daily,issue_once,batch_result

class Response:
 status=200
 def __enter__(self):return self
 def __exit__(self,*a):return False
 def read(self,*a):return b'[]'

class HTTPTests(unittest.TestCase):
 def call(self,effects,**kwargs):
  events=[];delays=[];opener=MagicMock();opener.open.side_effect=effects
  client=HTTPTransport(observer=lambda **e:events.append(e),sleeper=delays.append,**kwargs)
  with patch('research.daily_shadow_v3.adapter.build_opener',return_value=opener):result=client.get('/api/eod/AMD.US',{'fmt':'json'},'SYNTHETIC_TOKEN')
  return result,events,delays,opener
 def test_transient_503_then_actual_http_200(self):
  _,events,delays,opener=self.call([HTTPError('https://eodhd.com/?api_token=SYNTHETIC_TOKEN',503,'private',{},None),Response()])
  self.assertEqual(opener.open.call_count,2);self.assertEqual(delays,[1]);self.assertTrue(any(e.get('http_status')==200 and e['status']=='RESPONSE' for e in events));self.assertNotIn('SYNTHETIC_TOKEN',json.dumps(events))
 def test_authentication_failures_are_not_retried(self):
  for code in (401,403):
   opener=MagicMock();opener.open.side_effect=HTTPError('https://eodhd.com/?api_token=SYNTHETIC_TOKEN',code,'private',{},None);sleep=MagicMock()
   with patch('research.daily_shadow_v3.adapter.build_opener',return_value=opener),self.assertRaisesRegex(VendorError,'HTTP_'+str(code)):
    HTTPTransport(sleeper=sleep).get('/api/user',{},'SYNTHETIC_TOKEN')
   self.assertEqual(opener.open.call_count,1);sleep.assert_not_called()
 def test_timeout_is_bounded_and_does_not_expose_url(self):
  opener=MagicMock();opener.open.side_effect=TimeoutError('https://eodhd.com/?api_token=SYNTHETIC_TOKEN');events=[];sleep=MagicMock()
  with patch('research.daily_shadow_v3.adapter.build_opener',return_value=opener),self.assertRaisesRegex(VendorError,'TRANSPORT_TIMEOUT'):
   HTTPTransport(sleeper=sleep,observer=lambda **e:events.append(e)).get('/api/user',{},'SYNTHETIC_TOKEN')
  self.assertEqual(opener.open.call_count,3);self.assertEqual(sleep.call_count,2);self.assertNotIn('SYNTHETIC_TOKEN',json.dumps(events));self.assertEqual(events[0]['exception_type'],'TimeoutError')
 def test_429_retry_after_is_honored(self):
  _,events,delays,_=self.call([HTTPError('https://eodhd.com/',429,'limit',{'Retry-After':'3'},None),Response()]);self.assertEqual(delays,[3]);self.assertEqual(events[0]['http_status'],429)
 def test_long_retry_after_is_not_retried_early(self):
  opener=MagicMock();opener.open.side_effect=HTTPError('https://eodhd.com/',429,'limit',{'Retry-After':'120'},None);sleep=MagicMock()
  with patch('research.daily_shadow_v3.adapter.build_opener',return_value=opener),self.assertRaises(VendorError):HTTPTransport(sleeper=sleep).get('/api/user',{},'SYNTHETIC')
  sleep.assert_not_called();self.assertEqual(opener.open.call_count,1)
 def test_run_deadline_prevents_more_network_requests(self):
  opener=MagicMock()
  with patch('research.daily_shadow_v3.adapter.build_opener',return_value=opener),self.assertRaisesRegex(VendorError,'RUN_DEADLINE'):
   HTTPTransport(deadline=time.monotonic()-1).get('/api/user',{},'SYNTHETIC')
  opener.open.assert_not_called()

class ReadinessTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  with patch.dict(os.environ,{'EODHD_API_TOKEN':'SYNTHETIC'}):cls.snapshot=EODHDAdapter(fixture_permit(),FixtureTransport(),clock).collect(SESSION)
 def stable(self,snapshots):
  adapter=MagicMock();adapter.permit=fixture_permit();adapter.collect.side_effect=snapshots;store=MagicMock();store.payload.side_effect=lambda *a:uuid.uuid4()
  with patch('research.daily_shadow_live.runtime.receipt') as receipt:
   result=collect_stable(adapter,store,uuid.uuid4(),SESSION,sleeper=lambda _:None,clock=clock)
   return result,store,receipt
 def test_global_directory_and_formatting_drift_do_not_block_inputs(self):
  changed=copy.deepcopy(self.snapshot);changed.raw_responses['GLOBAL_UNRELATED']=b'not a model input';changed.revision='f'*64
  self.assertEqual(fingerprint(changed),fingerprint(self.snapshot));_,store,receipt=self.stable([self.snapshot,changed]);self.assertEqual(store.payload.call_count,2);self.assertEqual(receipt.call_args.kwargs['status'],'RAW_ONLY_REVISION')
 def test_unused_total_return_adjustment_does_not_change_price_risk_inputs(self):
  changed=copy.deepcopy(self.snapshot);changed.bars['AMD'][0]['adjusted_close']*=.5;self.assertEqual(fingerprint(changed),fingerprint(self.snapshot))
 def test_ohlcv_and_action_changes_are_relevant(self):
  for field in ('close','low','volume'):
   changed=copy.deepcopy(self.snapshot);changed.bars['AMD'][0][field]*=.99;self.assertNotEqual(fingerprint(changed),fingerprint(self.snapshot))
  changed=copy.deepcopy(self.snapshot);changed.splits['NVDA']=[dict(date=SESSION,factor=10)];self.assertNotEqual(fingerprint(changed),fingerprint(self.snapshot))
  changed=copy.deepcopy(self.snapshot);changed.dividends['MU']=[dict(date=SESSION,unadjusted_value=.115)];self.assertNotEqual(fingerprint(changed),fingerprint(self.snapshot))
 def test_real_revision_retries_consecutively_then_stabilizes(self):
  changed=copy.deepcopy(self.snapshot);changed.bars['AMD'][0]['close']-=.1;changed.revision='e'*64
  result,store,receipt=self.stable([self.snapshot,changed,copy.deepcopy(changed)])
  self.assertEqual(store.payload.call_count,3);self.assertEqual(receipt.call_count,2);self.assertEqual(result[2],result[3])
 def test_persistent_instability_archives_all_pairs_and_fails(self):
  snaps=[]
  for i in range(4):
   s=copy.deepcopy(self.snapshot);s.bars['AMD'][0]['close']-=i*.1;s.revision=str(i)*64;snaps.append(s)
  adapter=MagicMock();adapter.permit=fixture_permit();adapter.collect.side_effect=snaps;store=MagicMock()
  with patch('research.daily_shadow_live.runtime.receipt') as receipt,self.assertRaisesRegex(VendorError,'SOURCE_STILL_REVISING'):
   collect_stable(adapter,store,uuid.uuid4(),SESSION,sleeper=lambda _:None,clock=clock)
  self.assertEqual(store.payload.call_count,4);self.assertEqual(receipt.call_count,3)
 def test_missing_or_stale_data_never_becomes_ready(self):
  adapter=MagicMock();adapter.permit=fixture_permit();adapter.collect.side_effect=VendorError('STALE_OR_MISSING_BAR')
  with self.assertRaisesRegex(VendorError,'STALE_OR_MISSING_BAR'):collect_stable(adapter,MagicMock(),uuid.uuid4(),SESSION,sleeper=lambda _:None,clock=clock)
  blocked=copy.deepcopy(self.snapshot);blocked.legal_reason='SUBSCRIPTION_EXPIRED';blocked.revision=None
  adapter.collect.side_effect=[self.snapshot,blocked]
  with self.assertRaisesRegex(VendorError,'SUBSCRIPTION_EXPIRED'):collect_stable(adapter,MagicMock(),uuid.uuid4(),SESSION,sleeper=lambda _:None,clock=clock)
 def test_next_local_day_never_backdates_readiness(self):
  adapter=MagicMock();adapter.permit=fixture_permit()
  with self.assertRaisesRegex(VendorError,'STALE_OR_BACKDATED_SESSION'):collect_stable(adapter,MagicMock(),uuid.uuid4(),SESSION,clock=lambda:datetime(2025,1,4,2,tzinfo=timezone.utc))
  adapter.collect.assert_not_called()

class DiagnosticTests(unittest.TestCase):
 def test_secret_redaction_and_traceback_without_locals(self):
  env=dict(EODHD_API_TOKEN='SYNTHETIC_TOKEN',ALPHA_SHADOW_DATABASE_URL='postgresql://alice:p%40ss@private/alpha_shadow_research')
  with patch.dict(os.environ,env),redirect_stdout(io.StringIO()) as output:
   local_secret='NEVER_CAPTURE_LOCALS'
   try:raise ValueError('SYNTHETIC_TOKEN p@ss https://host/a?api_token=OTHER Authorization=Bearer_OTHER')
   except ValueError as exc:RunAudit().failure('TEST',exc,persist=False)
  text=output.getvalue()
  for forbidden in ('SYNTHETIC_TOKEN','p@ss','p%40ss','OTHER','NEVER_CAPTURE_LOCALS','https://host'):self.assertNotIn(forbidden,text)
  self.assertEqual(redact({'X-API-Key':'UNKNOWN_PRIVATE_API_KEY'}),{'X-API-Key':'[REDACTED]'})
  record=json.loads(text);self.assertEqual(record['exception_type'],'ValueError');self.assertIn('test_worker_fix.py',record['traceback']);self.assertTrue(record['message']);uuid.UUID(record['run_id']);self.assertIsNotNone(datetime.fromisoformat(record['timestamp']).tzinfo)
 def run_mock(self,*,now=None,issue=None,history_error=None,connection_error=None,issue_error=None):
  store=MagicMock();store.verify.return_value=True
  if connection_error:store.connect.side_effect=connection_error
  now=now or datetime(2026,11,13,2,tzinfo=timezone.utc)
  with ExitStack() as stack:
   for name,value in [('identity',None),('dsn','SYNTHETIC'),('vault_key',Fernet.generate_key()),('ResearchStore',store),('acceptance',{}),('continue_paid_access',True),('effective_permit',fixture_permit()),('models',fixture_models()),('resolve_due',dict(checked=0,unresolved=0))]:stack.enter_context(patch('research.daily_shadow_live.runtime.'+name,return_value=value))
   date=stack.enter_context(patch('research.daily_shadow_live.runtime.datetime'));date.now.return_value=now
   issue_mock=stack.enter_context(patch('research.daily_shadow_live.runtime.issue_once',return_value=issue or batch_result('2026-11-12',222,216)))
   issue_mock.side_effect=issue_error
   stack.enter_context(patch('research.daily_shadow_live.reporting.weekly_report',return_value=dict(pending=216,week='2026-11-09')))
   stack.enter_context(patch.dict(os.environ,{'ALPHA_COMPARE_HISTORY_ONCE':'true' if history_error else 'false'}))
   if history_error:stack.enter_context(patch('research.daily_shadow_live.historical.run_once',side_effect=history_error))
   output=stack.enter_context(redirect_stdout(io.StringIO()));code=run_daily();records=[json.loads(l) for l in output.getvalue().splitlines()]
  return code,records,issue_mock
 def test_success_has_one_run_id_and_explicit_completion(self):
  code,records,_=self.run_mock();self.assertEqual(code,0);self.assertEqual(records[0]['status'],'RUN_STARTED');self.assertEqual(records[-1]['status'],'SUCCESS');self.assertEqual(len({r['run_id'] for r in records}),1)
 def test_partial_issue_is_not_success(self):
  code,records,_=self.run_mock(issue=batch_result(SESSION,222,210));self.assertEqual(code,2);self.assertEqual(records[-1]['status'],'PARTIAL_FAILURE')
 def test_optional_history_failure_is_partial_and_has_trace(self):
  code,records,_=self.run_mock(history_error=TimeoutError('SYNTHETIC'));self.assertEqual(code,2);self.assertTrue(any(r.get('exception_type')=='TimeoutError' and r.get('traceback') for r in records));self.assertEqual(records[-1]['exit_code'],2)
 def test_database_connection_failure_has_failure_completion(self):
  code,records,_=self.run_mock(connection_error=psycopg.OperationalError('private connection detail'));self.assertEqual(code,1);self.assertEqual(records[-1]['status'],'FAILED');self.assertNotIn('private connection detail',json.dumps(records))
 def test_holiday_does_not_call_forecast_issuer(self):
  code,records,issue=self.run_mock(now=datetime(2025,1,2,2,tzinfo=timezone.utc));self.assertEqual(code,0);issue.assert_not_called();self.assertTrue(any(r.get('status')=='NON_TRADING_DAY' for r in records))
 def test_missing_identity_has_startup_failure_not_unhandled_trace(self):
  with patch.dict(os.environ,{},clear=True),redirect_stdout(io.StringIO()) as output:self.assertEqual(run_daily(),1)
  records=[json.loads(l) for l in output.getvalue().splitlines()];self.assertEqual(records[-1]['status'],'FAILED');self.assertEqual(records[1]['exception_type'],'ConfigurationError')
 def test_existing_partial_batch_is_not_reported_as_success(self):
  store=MagicMock();store.connect.return_value.__enter__.return_value.execute.return_value.fetchone.side_effect=[(True,),(100,98)];adapter=MagicMock()
  self.assertEqual(issue_once(store,adapter,[],SESSION)['status'],'PARTIAL_FAILURE');adapter.collect.assert_not_called()
 def test_mocked_generation_uses_genuine_engine_and_utc_issue(self):
  with patch.dict(os.environ,{'EODHD_API_TOKEN':'SYNTHETIC'}):snap=EODHDAdapter(fixture_permit(),FixtureTransport(),clock).collect(SESSION)
  store=MagicMock();store.payload.return_value=uuid.uuid4();store.forecasts.return_value=[uuid.uuid4() for _ in range(222)]
  def connect():
   context=MagicMock();connection=context.__enter__.return_value
   def execute(sql,params=None):
    cur=MagicMock();cur.fetchone.return_value=(True,) if 'pg_try_advisory' in sql else ((0,0) if ('count(' in sql) else ((datetime.fromisoformat(ISSUED)+timedelta(minutes=4),) if 'clock_timestamp' in sql else (None,)))
    return cur
   connection.execute.side_effect=execute;return context
  store.connect.side_effect=connect;adapter=MagicMock();adapter.permit=fixture_permit()
  with patch('research.daily_shadow_live.runtime.collect_stable',return_value=(snap,copy.deepcopy(snap),'a'*64,'a'*64)),patch('research.daily_shadow_live.runtime.verify_actions',return_value=({},[])):
   result=issue_once(store,adapter,fixture_models(),SESSION,clock=clock)
  self.assertEqual(result['issued'],216);self.assertEqual(result['blocked'],6)
  args=store.forecasts.call_args;rows=args.args[1];self.assertTrue(all(datetime.fromisoformat(r['issued_at']).utcoffset()==timedelta(0) for r in rows));self.assertTrue(all(r['probability_calibrated'] is None for r in rows))

DSN=os.environ.get('ALPHA_SHADOW_TEST_DSN')
@unittest.skipUnless(DSN,'Explicit disposable local SQL required')
class DiagnosticSQLTests(unittest.TestCase):
 def test_inspection_is_read_only_and_separates_synthetic(self):
  from .inspect_persistence import inspect
  report=inspect(DSN,isolated_test=True);self.assertEqual(report['verification'],'DIRECT_READ_ONLY_SQL');self.assertEqual(report['totals']['numeric_research_forecasts'],0);self.assertEqual(report['successful_audited_run_ids'],0)
 def test_run_uuid_and_error_evidence_persist_in_receipt(self):
  from .runtime import receipt
  from .diagnostics import ACTIVE
  store=ResearchStore(DSN,Fernet.generate_key());audit=RunAudit();token=ACTIVE.set(audit)
  try:
   with redirect_stdout(io.StringIO()):receipt(store,phase='TEST',status='ERROR',exception_type='TimeoutError',traceback='SANITIZED_STACK')
  finally:ACTIVE.reset(token)
  with store.connect() as c:
   row=c.execute("select body from alpha_operations_v4.receipts where body->>'run_id'=%s",(audit.run_id,)).fetchone()[0]
  self.assertEqual(row['traceback'],'SANITIZED_STACK');self.assertTrue(row['message'])
if __name__=='__main__':unittest.main()
