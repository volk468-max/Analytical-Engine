"""Real PostgreSQL 16/18 role, transaction, TTL and immutable-vault separation tests."""
import os,copy,uuid,json,unittest,concurrent.futures
from dataclasses import replace
from unittest.mock import patch
import psycopg
import pandas as pd
from cryptography.fernet import Fernet
from research.daily_shadow.core import canonical
from .store import ResearchStore
from .fixtures import *
from .legal import fixture_permit,Permit
from .adapter import EODHDAdapter
from .engine import candidates
from .runner import run
DSN=os.environ.get('ALPHA_SHADOW_TEST_DSN')
@unittest.skipUnless(DSN,'Explicit disposable local PostgreSQL required; not run')
class DatabaseTests(unittest.TestCase):
 def setUp(self):
  info=psycopg.conninfo.conninfo_to_dict(DSN)
  if info.get('host') not in ('127.0.0.1','localhost') or info.get('dbname')!='alpha_shadow_research':raise ValueError('LOCAL_DISPOSABLE_ONLY')
  self.s=ResearchStore(DSN,Fernet.generate_key());self.p=fixture_permit();self.models=fixture_models();self.key=str(uuid.uuid4());self.t=FixtureTransport()
  for m in self.models:m['version']+=':'+self.key
  with patch.dict(os.environ,{'EODHD_API_TOKEN':'synthetic-fixture-only'}):self.snap=EODHDAdapter(self.p,self.t,clock).collect(SESSION)
  self.cid=self.s.register(self.p);self.ref=self.s.payload(self.cid,self.snap,self.p.raw_until)
  self.rows=candidates(SESSION,ISSUED,ISSUED,self.snap,self.models,self.p,data_reviewed=True)
 def job(self):return self.s.forecasts(self.key,self.rows,self.models,self.cid,self.ref,self.snap)
 def body(self,fid):
  with self.s.connect() as c:return c.execute('select body from alpha_research_v3.journal where id=%s',(fid,)).fetchone()[0]
 def attempt(self,b):
  with self.s.connect() as c:return self.s.append(c,'FORECAST',str(uuid.uuid4()),b)
 def test_atomic_full_batch_retry_and_chain(self):
  ids=self.job();self.assertEqual(len(ids),222);self.assertEqual(ids,self.job());self.assertTrue(self.s.verify());self.assertTrue(self.s.legacy.verify())
 def test_concurrent_idempotent_retry(self):
  with concurrent.futures.ThreadPoolExecutor(2) as pool:ids=list(pool.map(lambda _:self.job(),range(2)))
  self.assertEqual(ids[0],ids[1])
 def test_fixture_scores_excluded_from_paired_live_metrics(self):
  self.job();self.assertEqual(self.s.metrics()['paired_dates'],0)
 def test_no_raw_in_journal_private_plane_encrypted(self):
  ids=self.job();self.assertEqual(self.s.private(self.ref)['bars']['AMD'][-1]['close'],100)
  with self.s.connect() as c:
   b=c.execute('select body_text from alpha_research_v3.journal where id=%s',(ids[0],)).fetchone()[0]
   self.assertNotIn('raw_responses',b);self.assertNotIn('anchor_price',b)
   with self.assertRaises(psycopg.errors.InsufficientPrivilege):c.execute('select * from alpha_licensed_v3.payloads')
 def test_no_raw_immutable_escape(self):
  b=self.body(self.job()[0]);b['anchor_price']=100
  with self.assertRaisesRegex(psycopg.Error,'IMMUTABLE_PAYLOAD'):self.attempt(b)
 def test_validation_trading_backfill_forbidden(self):
  b=self.body(self.job()[0])
  for mode in ('VALIDATED','TRADING','BACKFILL','PROSPECTIVE'):
   with self.subTest(mode=mode),self.assertRaises(psycopg.Error):self.attempt(dict(b,run_mode=mode))
 def test_fixture_cannot_be_live_forecast(self):
  b=self.body(self.job()[0]);b['run_mode']='RESEARCH_FORECAST'
  with self.assertRaisesRegex(psycopg.Error,'FIXTURE_LIVE'):self.attempt(b)
 def test_app_cannot_self_approve_live_contract(self):
  with self.assertRaisesRegex(psycopg.Error,'LEGAL_REVIEWER'):self.s.register(replace(self.p,scope='LIVE'))
 def test_immutable_contract_and_forecast(self):
  self.job()
  with self.assertRaisesRegex(psycopg.Error,'CONTRACT_IMMUTABLE'):self.s.register(replace(self.p,paid=False),self.cid)
  for statement in ('update alpha_research_v3.forecasts set probability_raw=.5','delete from alpha_research_v3.journal','truncate alpha_research_v3.outcomes','delete from alpha_research_v3.contracts'):
   with self.assertRaises(psycopg.errors.InsufficientPrivilege):
    with self.s.connect() as c:c.execute(statement)
 def test_owner_trigger_defense(self):
  self.job()
  with self.assertRaisesRegex(psycopg.Error,'APPEND_ONLY'):
   with psycopg.connect(DSN) as c:c.execute('update alpha_research_v3.forecasts set probability_raw=probability_raw')
 def test_offboarding_purges_vault_but_not_allowed_audit(self):
  ids=self.job();self.assertEqual(self.s.offboard(self.cid),1)
  with self.assertRaises(psycopg.Error):self.s.private(self.ref)
  with self.assertRaises(psycopg.Error):self.s.payload(self.cid,self.snap,self.p.raw_until)
  self.assertTrue(self.s.permit(self.cid).revoked);self.assertEqual(self.body(ids[0])['status'],'RESEARCH_FORECAST');self.assertTrue(self.s.verify())
  with self.s.connect() as c:self.assertEqual(c.execute("select count(*) from alpha_research_v3.lifecycle where contract_id=%s and action='PURGE_CONFIRMED'",(self.cid,)).fetchone()[0],0)
 def test_app_cannot_claim_backup_purge(self):
  with self.assertRaises(psycopg.errors.InsufficientPrivilege):
   with self.s.connect() as c:c.execute('select alpha_research_v3.confirm_purge(%s,%s)',(self.cid,'fake receipt'))
 def test_ttl_expired_raw_is_unreadable_and_purged(self):
  # Only test owner simulates passage of time in deletable plane, never touches audit.
  with psycopg.connect(DSN) as c:c.execute("update alpha_licensed_v3.payloads set expires_at=clock_timestamp()-interval '1 second' where id=%s",(self.ref,))
  with self.assertRaisesRegex(psycopg.Error,'TTL_BLOCK'):self.s.private(self.ref)
  self.assertGreaterEqual(self.s.expire(),1)
 def test_revisions_separate_first_snapshot_and_anchor(self):
  ids=self.job();self.t.revision=1
  with patch.dict(os.environ,{'EODHD_API_TOKEN':'synthetic-only'}):new=EODHDAdapter(self.p,self.t,clock).collect(SESSION)
  newref=self.s.payload(self.cid,new,self.p.raw_until);self.assertNotEqual(newref,self.ref);self.assertEqual(self.s.private(self.ref)['bars']['AMD'][-1]['close'],100);self.assertEqual(self.s.private(newref)['bars']['AMD'][-1]['close'],101)
  self.assertEqual(self.body(ids[0])['anchor_ref'],str(self.ref))
  self.s.correction(self.key+':revision',ids[0],newref,new);self.assertTrue(self.s.verify())
  with self.assertRaisesRegex(psycopg.Error,'IDEMPOTENCY_CONFLICT'):self.s.forecasts(self.key,self.rows,self.models,self.cid,newref,new)
 def test_tampered_model_hash_and_future_model(self):
  b=self.body(self.job()[0])
  with self.assertRaisesRegex(psycopg.Error,'FROZEN_MODEL_HASH'):self.attempt(dict(b,model_hash='0'*64))
 def test_exact_horizon_and_no_fake_calibration(self):
  b=self.body(self.job()[0])
  with self.assertRaisesRegex(psycopg.Error,'EXACT_FUTURE'):self.attempt(dict(b,horizon_end_at=ISSUED))
  with self.assertRaises(psycopg.Error):self.attempt(dict(b,probability_calibrated=.25))
 def test_no_future_source_and_short_retention(self):
  b=self.body(self.job()[0])
  with self.assertRaisesRegex(psycopg.Error,'ASOF'):self.attempt(dict(b,source_retrieved_at='2030-01-01T00:00:00Z'))
  with self.assertRaisesRegex(psycopg.Error,'FUTURE_INPUT'):self.attempt(dict(b,source_publication_at='2030-01-01T00:00:00Z'))
 def test_outcome_append_correction_full_window(self):
  fid=self.job()[0];b=dict(forecast_id=str(fid),status='IMMATURE',outcome=None,completed_sessions=0,last_publication_at=None,reason='FULL_HORIZON_NOT_MATURE')
  self.s.outcome(self.key+'i',b)
  with self.assertRaises(psycopg.Error):self.s.outcome(self.key+'bad',dict(b,status='MATURED',outcome=True))
  end=self.body(fid)['horizon_end_at'];m=dict(b,status='MATURED',outcome=False,completed_sessions=10,last_publication_at=end,reason=None)
  oid=self.s.outcome(self.key+'m',m);self.s.outcome(self.key+'c',dict(m,outcome=True,supersedes_id=str(oid)))
  with self.s.connect() as c:self.assertEqual(c.execute('select count(*) from alpha_research_v3.outcomes where forecast_id=%s',(fid,)).fetchone()[0],3)
  self.assertTrue(self.s.verify())
 def test_illegal_raw_not_stored_and_all_null(self):
  p=Permit('EODHD');cid=self.s.register(p);rows=candidates(SESSION,ISSUED,ISSUED,self.snap,self.models,p,data_reviewed=True)
  ids=self.s.forecasts(self.key,rows,self.models,cid,None,self.snap)
  self.assertEqual(sum(self.body(i)['probability_raw'] is not None for i in ids),0)
  with self.assertRaises(psycopg.Error):self.s.payload(cid,self.snap,self.p.raw_until)
 def test_resolver_reads_original_anchor_not_revised_anchor(self):
  from .resolver import resolve_once
  ids=self.job();i=next(i for i,r in enumerate(self.rows) if r['symbol']=='SPY' and r['label_type']=='EOD_CLOSE' and r['threshold_pct']==10 and r['horizon']==10)
  self.t.revision=1
  with patch.dict(os.environ,{'EODHD_API_TOKEN':'synthetic-only'}):revised=EODHDAdapter(self.p,self.t,clock).collect(SESSION)
  ref=self.s.payload(self.cid,revised,self.p.raw_until);self.s.correction(self.key+'c',ids[i],ref,revised)
  window=outcome_window(self.snap,self.rows[i]);r=resolve_once(self.s,ids[i],window,'2025-06-02T00:00:00Z',data_reviewed=True)
  self.assertEqual(r['status'],'MATURED');self.assertFalse(r['outcome']);self.assertEqual(r,resolve_once(self.s,ids[i],window,'2025-06-02T00:00:00Z',data_reviewed=True))
 def test_resolver_blocks_offboarded_anchor(self):
  from .resolver import resolve_once
  ids=self.job();self.s.offboard(self.cid);window=outcome_window(self.snap,self.rows[0]);r=resolve_once(self.s,ids[0],window,'2025-06-02T00:00:00Z',data_reviewed=True);self.assertEqual(r['status'],'UNRESOLVED');self.assertIsNone(r['outcome'])
 def test_missing_models_record_nulls_not_invented_counts(self):
  with self.s.connect() as c:session=c.execute("select session_date from alpha_research_v3.calendar_sessions s where session_date between '2025-01-02' and '2030-01-01' and not exists(select 1 from alpha_research_v3.forecasts f join alpha_shadow_v1.model_registry m on m.id=f.model_id where f.session_date=s.session_date and m.version like 'UNAVAILABLE-%') order by session_date limit 1").fetchone()[0].isoformat()
  issued=pd.Timestamp(session+' 20:31:00',tz='America/New_York').tz_convert('UTC').isoformat();self.snap.session=session;self.snap.retrieved_at=issued
  for bars in self.snap.bars.values():bars[-1]['date']=session
  self.models=[];self.rows=candidates(session,issued,issued,self.snap,self.models,self.p,data_reviewed=True);ids=self.job();self.assertEqual(len(ids),222);self.assertTrue(all(self.body(i)['probability_raw'] is None for i in ids));self.assertEqual(self.rows[0]['reason'],'MODEL_UNAVAILABLE')
 def test_atomic_rollback_on_mid_batch_failure(self):
  self.rows[120]['model_hash']='0'*64
  with self.assertRaises(psycopg.Error):self.job()
  with self.s.connect() as c:self.assertEqual(c.execute('select count(*) from alpha_research_v3.journal where event_key like %s',(self.key+'%',)).fetchone()[0],0)
if __name__=='__main__':unittest.main()
