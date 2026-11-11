"""Must use explicit disposable local PostgreSQL. Never reads DATABASE_URL."""
import unittest,os,uuid,concurrent.futures,json
import psycopg
from .core import *
from .runner import *
from .store import Store
DSN=os.environ.get('ALPHA_SHADOW_TEST_DSN')
@unittest.skipUnless(DSN,'Explicit local test DSN not supplied; integration NOT run')
class PostgresTests(unittest.TestCase):
 def setUp(self):
  # Even a mistaken test environment cannot target Railway/remote production.
  info=psycopg.conninfo.conninfo_to_dict(DSN)
  if info.get('host') not in ('127.0.0.1','localhost') or info.get('dbname')!='alpha_shadow_research':raise ValueError('LOCAL_DISPOSABLE_TEST_ONLY')
  self.store=Store(DSN);self.session='2025-11-06';self.now='2025-11-06T23:30:00+00:00';self.models=blocked_models();version=str(uuid.uuid4())
  for m in self.models:m['version']=version
  self.v=archive(b'LOCAL_SYNTHETIC_NOT_LIVE',self.session,'2025-11-06T22:00:00+00:00','2025-11-06T22:01:00+00:00',basis='SPLIT_NORMALIZED_PRICE',actions_qualified=False);self.key=str(uuid.uuid4())
 def data(self):
  return [dict(forecast(self.session,'SPY','EOD_CLOSE',10,10,self.models[0],self.v,self.now,self.now),model_name='HIST')]
 def job(self):return self.store.job(self.key,self.session,self.models,self.v,self.data())
 def test_real_postgres_roundtrip_and_chain(self):
  a=self.job();self.assertEqual(a,self.job());self.assertTrue(self.store.verify())
 def test_concurrent_duplicate(self):
  with concurrent.futures.ThreadPoolExecutor(2) as pool:r=list(pool.map(lambda _:self.job(),range(2)))
  self.assertEqual(r[0],r[1])
 def test_atomic_rollback(self):
  with self.store.connect() as c:before=c.execute('select count(*) from alpha_shadow_v1.audit_events').fetchone()[0]
  bad=self.data();bad[0]['probability_raw']=.5
  with self.assertRaises(psycopg.Error):self.store.job(self.key,self.session,self.models,self.v,bad)
  with self.store.connect() as c:self.assertEqual(before,c.execute('select count(*) from alpha_shadow_v1.audit_events').fetchone()[0])
 def test_update_delete_truncate_denied(self):
  self.job()
  for sql in ('update alpha_shadow_v1.audit_events set event_key=event_key','delete from alpha_shadow_v1.forecast_records','truncate alpha_shadow_v1.job_health'):
   with self.assertRaises(psycopg.errors.InsufficientPrivilege):
    with self.store.connect() as c:c.execute(sql)
 def test_owner_trigger_defense(self):
  self.job()
  with self.assertRaises(psycopg.Error):
   with psycopg.connect(DSN) as c:c.execute('update alpha_shadow_v1.audit_events set event_key=event_key')
 def test_model_version_immutable(self):
  self.job();self.models[0]['params']['changed']=True
  with self.assertRaises(psycopg.Error):self.job()
 def test_correction_does_not_edit_forecast(self):
  fid=self.job()[0];self.store.correction(self.key+'c',fid,'explicit source revision',dict(probability_raw=None))
  with self.store.connect() as c:self.assertEqual(c.execute('select status from alpha_shadow_v1.forecast_records where id=%s',(fid,)).fetchone()[0],'STATUS_BLOCKED')
 def test_outcome_appends(self):
  fid=self.job()[0];self.store.outcome(self.key+'i',dict(forecast_id=str(fid),status='IMMATURE',outcome=None));self.store.outcome(self.key+'m',dict(forecast_id=str(fid),status='MATURED',completed_sessions=10,last_publication_at='2026-11-01T00:00:00+00:00',outcome=False),vintage=self.v)
  with self.store.connect() as c:self.assertEqual(c.execute('select count(*) from alpha_shadow_v1.outcome_records where forecast_id=%s',(fid,)).fetchone()[0],2)
 def test_missing_maturity_cannot_pass_sql(self):
  fid=self.job()[0]
  with self.assertRaises(psycopg.Error):self.store.outcome(self.key+'bad',dict(forecast_id=str(fid),status='MATURED',outcome=True))
 def test_source_hash_verified_in_sql(self):
  self.v['source_hash']='f'*64
  with self.assertRaises(psycopg.Error):self.job()
 def test_source_revision_not_silent_retry(self):
  self.job();self.v=archive(b'revised',self.session,self.v['publication_at'],self.v['ingestion_at'])
  with self.assertRaises(ValueError):self.job()
 def test_duplicate_unique_tuple_not_bypassed_by_key(self):
  fid=self.job()[0]
  with self.store.connect() as c:body=c.execute('select body from alpha_shadow_v1.audit_events where id=%s',(fid,)).fetchone()[0]
  with self.assertRaises(psycopg.errors.UniqueViolation):
   with self.store.connect() as c:self.store.append(c,'forecast',str(uuid.uuid4()),body)
 def test_prospective_cannot_be_backdated(self):
  with self.assertRaises(psycopg.Error):self.store.job(self.key,self.session,self.models,self.v,self.data(),mode='PROSPECTIVE')
 def test_full_batch_is_atomic_and_idempotent(self):
  a=run_once(self.session,FixtureProvider(self.v),self.models,self.store,self.now,self.now)
  b=run_once(self.session,FixtureProvider(self.v),self.models,self.store,self.now,self.now)
  self.assertEqual(a['ids'],b['ids']);self.assertEqual(a['records'],222);self.assertTrue(self.store.verify())
 def test_outcome_publication_before_horizon_end_denied(self):
  fid=self.job()[0]
  with self.assertRaises(psycopg.Error):self.store.outcome(self.key+'early',dict(forecast_id=str(fid),status='MATURED',completed_sessions=10,last_publication_at=self.now,outcome=True),vintage=self.v)
 def test_resolver_uses_original_anchor(self):
  from .resolver import resolve_once
  fid=self.job()[0];v=self.v
  class Provider:
   def collect_window(self,original):return v,[]
  resolve_once(self.store,fid,Provider(),self.now)
  with self.store.connect() as c:
   self.assertEqual(c.execute("select e.body->>'reason' from alpha_shadow_v1.outcome_records o join alpha_shadow_v1.audit_events e on e.id=o.id where forecast_id=%s",(fid,)).fetchone()[0],'NO_FROZEN_ANCHOR')
 def test_reader_cannot_append(self):
  with self.assertRaises(psycopg.errors.InsufficientPrivilege):
   with psycopg.connect(DSN) as c:c.execute('set role alpha_shadow_reader');self.store.append(c,'health',str(uuid.uuid4()),dict(status='x'))
if __name__=='__main__':unittest.main()
