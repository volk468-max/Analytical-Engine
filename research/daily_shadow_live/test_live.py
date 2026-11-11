import unittest,os,json,uuid,copy
from datetime import datetime,timezone
from dataclasses import replace
from unittest.mock import patch,MagicMock
import numpy as np,pandas as pd
import psycopg
from cryptography.fernet import Fernet
from research.daily_shadow.core import calendar,canonical
from research.daily_shadow_v3.legal import fixture_permit
from research.daily_shadow_v3.store import ResearchStore
from research.daily_shadow_v3.fixtures import fixture_models,FixtureTransport,clock,SESSION,ISSUED
from research.daily_shadow_v3.adapter import EODHDAdapter,VendorError
from .config import identity,models,PROJECT,ENVIRONMENT,WORKER,vault_key,ConfigurationError
from .runtime import latest_completed,paid_status,acceptance,issue_once
from .historical import annual_predictions,label
from .reporting import scores,weekly_report

class LiveTests(unittest.TestCase):
 def test_exact_isolation_and_no_trading(self):
  env=dict(RAILWAY_PROJECT_ID=PROJECT,RAILWAY_ENVIRONMENT_ID=ENVIRONMENT,RAILWAY_SERVICE_ID=WORKER,ALPHA_RUN_MODE='RESEARCH_FORECAST',ALPHA_LIVE_TRADING='false');identity(env)
  for key in ('RAILWAY_PROJECT_ID','RAILWAY_ENVIRONMENT_ID','RAILWAY_SERVICE_ID','ALPHA_RUN_MODE','ALPHA_LIVE_TRADING'):
   with self.subTest(key=key),self.assertRaises(ConfigurationError):identity(dict(env,**{key:'WRONG'}))
 def test_frozen_real_models_not_fixture_and_no_flag_promotion(self):
  bank=models();self.assertEqual(len(bank),222);self.assertTrue(all(not m.get('fixture',False) and not m['qualified'] and not m['calibrated'] for m in bank));self.assertEqual({m['name'] for m in bank},{'HIST','REGIME'})
 def test_paid_metadata_no_token_logged(self):
  class Transport:
   def get(self,path,params,secret):return b'{"subscriptionType":"monthly","dailyRateLimit":100000,"email":"SYNTHETIC_PRIVATE"}'
  with patch.dict(os.environ,{'EODHD_API_TOKEN':'SYNTHETIC_TEST_KEY'}):self.assertTrue(paid_status(Transport()))
 def test_free_or_unknown_subscription_blocked(self):
  for plan in ('FREE','EOD TRIAL','DEMO EOD','', 'PERSONAL'):
   class Transport:
    def get(self,*args):return json.dumps(dict(subscriptionType=plan,dailyRateLimit=100000)).encode()
   with patch.dict(os.environ,{'EODHD_API_TOKEN':'SYNTHETIC'}),self.assertRaises(VendorError):paid_status(Transport())
 def test_missing_credential_safe(self):
  with patch.dict(os.environ,{},clear=True),self.assertRaisesRegex(VendorError,'MISSING_CREDENTIALS'):paid_status()
 def test_latest_session_preclose_holiday_early_close_dst(self):
  for now,want in [('2026-11-11T14:00:00Z','2026-11-10'),('2026-11-12T02:00:00Z','2026-11-11'),('2025-01-01T23:00:00Z','2024-12-31'),('2025-07-03T18:00:00Z','2025-07-03'),('2025-03-11T02:00:00Z','2025-03-10')]:self.assertEqual(latest_completed(datetime.fromisoformat(now)),want)
 def test_existing_paid_authorization_does_not_invent_invoice(self):
  p=replace(fixture_permit(),total_monthly_usd=None);self.assertEqual(p.reason(ISSUED,fixture=True),'TOTAL_PRICE_TAXES_UNCONFIRMED')
  approved=replace(p,existing_paid_owner_authorized=True,authorized_vendor_cap_usd='50');self.assertIsNone(approved.reason(ISSUED,fixture=True));self.assertIsNone(approved.total_monthly_usd)
  self.assertEqual(replace(approved,authorized_vendor_cap_usd='51').reason(ISSUED,fixture=True),'VENDOR_BUDGET_EXCEEDED')
 def test_vault_key_deterministic_and_secret_separate_from_dump(self):
  with patch.dict(os.environ,{},clear=True):
   a=vault_key('postgresql://user:SYNTHETIC_A@localhost/alpha_shadow_research');b=vault_key('postgresql://user:SYNTHETIC_A@localhost/alpha_shadow_research');self.assertEqual(a,b);self.assertNotEqual(a,vault_key('postgresql://user:SYNTHETIC_B@localhost/alpha_shadow_research'))
 def test_calibration_empty_and_exact_scores(self):
  self.assertIsNone(scores([])['brier']);s=scores([(0.25,1),(0.75,0)]);self.assertAlmostEqual(s['brier'],.5625);self.assertEqual(s['event_frequency'],.5);self.assertEqual(len(s['calibration']),2);self.assertIsNone(s['confidence_interval'])
 def test_future_labels_cannot_train_same_year(self):
  days=calendar().sessions_in_range('2014-01-02','2020-12-31').strftime('%Y-%m-%d').to_numpy();y=np.arange(len(days))%2;r=np.array(['MIXED']*len(days),dtype=object);valid=np.ones(len(days),dtype=bool)
  before=annual_predictions(y,r,valid,days,60);poison=y.copy();poison[days>='2017-01-01']=1-poison[days>='2017-01-01'];after=annual_predictions(poison,r,valid,days,60);mask=(days>='2017-01-01')&(days<'2018-01-01')
  for a,b in zip(before,after):self.assertTrue(np.allclose(a[mask],b[mask],equal_nan=True))
 def test_source_failure_still_runs_retention_cleanup(self):
  from .runtime import run_daily
  store=MagicMock()
  with patch('research.daily_shadow_live.runtime.identity'),patch('research.daily_shadow_live.runtime.dsn',return_value='SYNTHETIC'),patch('research.daily_shadow_live.runtime.vault_key',return_value=Fernet.generate_key()),patch('research.daily_shadow_live.runtime.ResearchStore',return_value=store),patch('research.daily_shadow_live.runtime.acceptance',return_value={}),patch('research.daily_shadow_live.runtime.receipt'),patch('research.daily_shadow_live.runtime.continue_paid_access',side_effect=VendorError('SYNTHETIC_FAILURE')):
   self.assertEqual(run_daily(),1)
  store.expire.assert_called_once()
 def test_idempotent_retry_does_not_collect_again(self):
  store=MagicMock();conn=store.connect.return_value.__enter__.return_value
  conn.execute.return_value.fetchone.side_effect=[(True,),(222,216)]
  adapter=MagicMock();r=issue_once(store,adapter,[],SESSION);self.assertEqual(r['status'],'IDEMPOTENT_ALREADY_RECORDED');adapter.collect.assert_not_called()
 def test_identical_sources_have_identical_historical_scores(self):
  from .historical import compare_frames
  from research.daily_shadow_v3.adapter import SYMBOLS
  days=calendar().sessions_in_range('2014-01-02','2018-12-31').strftime('%Y-%m-%d');v=100+np.sin(np.arange(len(days))/10)*15
  frames={s:pd.DataFrame(dict(close=v,low=v-1),index=days) for s in SYMBOLS};result=compare_frames(frames,frames)
  self.assertEqual(len(result['events']),108)
  for event in result['events']:
   self.assertEqual(event['label_disagreements'],0)
   for name in ('HIST','REGIME'):self.assertEqual(event['metrics']['previous_'+name],event['metrics']['EODHD_'+name])
 def test_future_window_not_compressed_or_terminal_only(self):
  f=pd.DataFrame(dict(close=[100,89,100,100,100],low=[99,85,99,99,99]));y=label(f,2,10,'close');self.assertEqual(y[0],1);self.assertEqual(y[1],0);f.loc[1,'close']=np.nan;self.assertTrue(np.isnan(label(f,2,10,'close')[0]))

DSN=os.environ.get('ALPHA_SHADOW_TEST_DSN')
@unittest.skipUnless(DSN,'Disposable explicit PostgreSQL required')
class LiveDatabaseTests(unittest.TestCase):
 def setUp(self):
  info=psycopg.conninfo.conninfo_to_dict(DSN)
  if info.get('host') not in ('localhost','127.0.0.1') or info.get('dbname')!='alpha_shadow_research':raise ValueError('LOCAL_ONLY')
  self.s=ResearchStore(DSN,Fernet.generate_key());self.p=fixture_permit();self.cid=self.s.register(self.p)
 def test_receipts_cannot_contain_raw_fields(self):
  with self.assertRaisesRegex(psycopg.Error,'SAFE_RECEIPT'):
   with self.s.connect() as c:c.execute('select alpha_operations_v4.receipt(%s,%s::jsonb)',(uuid.uuid4(),canonical(dict(anchor_price=100))))
 def test_acceptance_does_not_count_fixture(self):self.assertEqual(acceptance(self.s)['real_forecasts'],0)
 def test_weekly_empty_does_not_invent_accuracy(self):
  report=weekly_report(self.s,datetime.now(timezone.utc));self.assertEqual(report['checked'],0);self.assertEqual(report['pending'],0);self.assertEqual(report['metrics'],{})
 def test_renewal_requires_separate_role(self):
  with self.assertRaises(psycopg.Error):
   with self.s.connect() as c:c.execute("select alpha_operations_v4.renew(%s,clock_timestamp()+interval '30 days','SYNTHETIC_RECEIPT')",(self.cid,))
 def test_readiness_rejects_short_gap_or_changed_source(self):
  for rev1,rev2,stamp in [('a'*64,'a'*64,'2025-01-03T01:31:30Z'),('a'*64,'b'*64,'2025-01-03T01:33:00Z')]:
   with self.assertRaisesRegex(psycopg.Error,'READINESS_NOT_VERIFIED'):
    with self.s.connect() as c:c.execute('select alpha_operations_v4.ready(%s,%s,%s,%s,%s,%s,%s)',(self.cid,SESSION,'f'*64,rev1,rev2,ISSUED,stamp))
 def test_baseline_failure_rolls_back_forecast_atomically(self):
  from research.daily_shadow_v3.engine import candidates
  bank=fixture_models()
  for m in bank:m['version']+=':'+str(uuid.uuid4())
  with patch.dict(os.environ,{'EODHD_API_TOKEN':'SYNTHETIC'}):snap=EODHDAdapter(self.p,FixtureTransport(),clock).collect(SESSION)
  ref=self.s.payload(self.cid,snap,self.p.raw_until);rows=candidates(SESSION,ISSUED,ISSUED,snap,bank,self.p,data_reviewed=True);key='baseline-rollback:'+str(uuid.uuid4())
  baselines={tuple(r[k] for k in ('symbol','label_type','threshold_pct','horizon')):(.5,0) for r in rows}
  with self.assertRaisesRegex(psycopg.Error,'PREISSUE_BASELINE_ONLY'):self.s.forecasts(key,rows,bank,self.cid,ref,snap,baselines=baselines,baseline_cutoff=ISSUED)
  with self.s.connect() as c:self.assertEqual(c.execute('select count(*) from alpha_research_v3.journal where event_key like %s',(key+'%',)).fetchone()[0],0)
 def test_readiness_positive_fixture_is_not_real_forecast(self):
  with self.s.connect() as c:c.execute('select alpha_operations_v4.ready(%s,%s,%s,%s,%s,%s,%s)',(self.cid,SESSION,'f'*64,'a'*64,'a'*64,ISSUED,'2025-01-03T01:33:00Z'))
  self.assertEqual(acceptance(self.s)['real_forecasts'],0)
 def test_issue_before_close_records_no_forecast(self):
  a=EODHDAdapter(self.p,FixtureTransport(),clock)
  r=issue_once(self.s,a,fixture_models(),SESSION,datetime.fromisoformat('2025-01-02T20:00:00Z'),ready_gap=0);self.assertEqual(r['status'],'STATUS_BLOCKED');self.assertEqual(acceptance(self.s)['real_forecasts'],0)
if __name__=='__main__':unittest.main()
