"""Supervised disposable PostgreSQL rehearsal. No migrations or live network source."""
import os,json,uuid
from pathlib import Path
import psycopg
from psycopg.conninfo import conninfo_to_dict
from .core import *
from .store import Store
from .runner import run_once,FixtureProvider,blocked_models
from .resolver import resolve_once
from .providers import UnavailableLiveProvider
from .artifacts import OUT,load_artifact

def local_dsn(dsn):
 info=conninfo_to_dict(dsn)
 if info.get('host') not in ('127.0.0.1','localhost') or info.get('dbname')!='alpha_shadow_research':raise ValueError('EXPLICIT_DISPOSABLE_LOOPBACK_ONLY')
 if info.get('user')!='alpha_shadow_test_app':raise ValueError('LEAST_PRIVILEGE_SYNTHETIC_LOGIN_REQUIRED')
 return dsn

class WindowFixture:
 def __init__(self,forecast,complete):
  dates=future_sessions(forecast['session'],forecast['horizon']);dates=dates if complete else dates[:1]
  bare=[dict(session=d,close=89 if i==0 else 101,publication_at=d+'T23:00:00+00:00') for i,d in enumerate(dates)];raw=canonical(dict(mode='SYNTHETIC_OUTCOME_BUNDLE',bars=bare)).encode();pub=bare[-1]['publication_at']
  self.v=archive(raw,forecast['session'],pub,pub,qualification='QUALIFIED_PIT',basis='SPLIT_NORMALIZED_PRICE',synthetic=True,actions_qualified=True)
  self.rows=[dict(r,source_hash=self.v['source_hash']) for r in bare]
 def collect_window(self,original):return self.v,self.rows

class BrokenProvider:
 def collect(self,session):raise ConnectionError('SYNTHETIC_PROVIDER_FAILURE')
 def collect_window(self,original):raise TimeoutError('SYNTHETIC_OUTCOME_PROVIDER_FAILURE')

class DisconnectStore(Store):
 @staticmethod
 def append(c,kind,key,payload):
  result=Store.append(c,kind,key,payload)
  if kind=='forecast':
   c.execute('reset role')  # Own LOGIN only, no signal privilege for other sessions.
   c.execute('select pg_terminate_backend(pg_backend_pid())')
  return result

def rehearse(dsn):
 store=Store(local_dsn(dsn));session='2025-01-02';issued='2025-01-02T23:30:00+00:00';tag=str(uuid.uuid4())
 with store.connect() as c:
  prospective_before=c.execute("select count(*) from alpha_shadow_v1.forecast_runs where mode='PROSPECTIVE'").fetchone()[0]
  version=c.execute('show server_version').fetchone()[0];assert not c.execute("select rolsuper from pg_roles where rolname=session_user").fetchone()[0]
 index=json.loads((OUT/'model-index.json').read_text());models=[load_artifact(OUT/r['file']) for r in index['models']]
 # Artifacts fit after this synthetic session, so probabilities remain blocked as required.
 blocked=run_once(session,UnavailableLiveProvider('COLLECTOR_NO_PUBLICATION_ACTION_LICENSE_CONTRACT'),models,store,issued,issued)
 assert blocked['records']==222
 with store.connect() as c:
  nulls=c.execute('select count(*) from alpha_shadow_v1.forecast_records where id=any(%s::uuid[]) and probability_raw is null and probability_calibrated is null',(blocked['ids'],)).fetchone()[0]
 assert nulls==222
 # Different explicit synthetic versions avoid collisions with the real replay artifacts.
 fixture_models=[]
 for name in ('HIST','REGIME'):
  m=dict(name=name,version='SYNTHETIC-'+tag+'-'+name,series=dict(symbol='SPY',label_type='EOD_CLOSE',threshold_pct=10,horizon=10),qualified=True,qualification_scope='SYNTHETIC_ONLY',calibrated=False,fit_cutoff='2024-12-31T00:00:00+00:00',supported_tasks=['EOD_CLOSE:10:10'],training=[dict(task='EOD_CLOSE:10:10',symbol='SPY',y=y,regime='UP',maturity='2024-11-01T23:00:00+00:00') for y in (0,1)],params=dict(beta=[1,1],regime_shrinkage=20),code_sha256=sha(Path(__file__).read_bytes()))
  fixture_models.append(m)
 v=archive(canonical(dict(mode='SYNTHETIC_ONLY',anchor=100)).encode(),session,'2025-01-02T22:00:00+00:00','2025-01-02T22:01:00+00:00',qualification='QUALIFIED_PIT',basis='SPLIT_NORMALIZED_PRICE',actions_qualified=True,synthetic=True,anchors={'SPY':100},regime='UP')
 fs=[dict(forecast(session,'SPY','EOD_CLOSE',10,10,m,v,issued,issued),model_name=m['name'],model_version=m['version']) for m in fixture_models]
 assert all(f['probability_raw']==.5 and f['probability_calibrated'] is None for f in fs)
 key='SYNTHETIC-REHEARSAL:'+tag
 # Actual backend termination inside a transaction; only this own connection is killed.
 with store.connect() as c:before=c.execute('select count(*) from alpha_shadow_v1.audit_events').fetchone()[0]
 try:DisconnectStore(dsn).job(key,session,fixture_models,v,fs)
 except psycopg.OperationalError:pass
 else:raise AssertionError('EXPECTED_CONNECTION_FAILURE')
 with store.connect() as c:assert c.execute('select count(*) from alpha_shadow_v1.audit_events').fetchone()[0]==before
 ids=store.job(key,session,fixture_models,v,fs);assert ids==store.job(key,session,fixture_models,v,fs)
 original=store.read_forecast(ids[0]);assert original['mode']=='SYNTHETIC'
 revised=dict(v,raw_b64=base64.b64encode(b'SYNTHETIC_REVISED_SOURCE').decode(),source_hash=sha(b'SYNTHETIC_REVISED_SOURCE'))
 try:store.job(key,session,fixture_models,revised,fs)
 except ValueError as e:assert str(e)=='SOURCE_REVISION_REQUIRES_CORRECTION'
 else:raise AssertionError('SOURCE_REVISION_NOT_REJECTED')
 correction=store.correction(key+':revision',ids[0],'SYNTHETIC source revision; original preserved',dict(source_hash=revised['source_hash']),vintage=revised)
 failed=resolve_once(store,ids[0],BrokenProvider(),issued)
 early=WindowFixture(original,False);immature=resolve_once(store,ids[0],early,early.rows[-1]['publication_at'])
 full=WindowFixture(original,True);mature=resolve_once(store,ids[0],full,full.rows[-1]['publication_at'])
 assert mature==resolve_once(store,ids[0],full,full.rows[-1]['publication_at'])
 with store.connect() as c:
  outcomes=c.execute('select status,outcome from alpha_shadow_v1.outcome_records where forecast_id=%s',(ids[0],)).fetchall();assert ('IMMATURE',None) in outcomes and ('MATURED',True) in outcomes and ('UNRESOLVED',None) in outcomes
  assert c.execute('select count(*) from alpha_shadow_v1.forecast_records where id=any(%s::uuid[]) and probability_raw=.5',(ids,)).fetchone()[0]==2
 for sql in ('update alpha_shadow_v1.forecast_records set status=status','delete from alpha_shadow_v1.forecast_records','truncate alpha_shadow_v1.forecast_records'):
  try:
   with store.connect() as c:c.execute(sql)
  except psycopg.errors.InsufficientPrivilege:pass
  else:raise AssertionError('MUTATION_NOT_REJECTED')
 assert store.verify()
 failed_run=run_once('2025-01-03',BrokenProvider(),blocked_models(),store,'2025-01-03T23:30:00+00:00','2025-01-03T23:30:00+00:00')
 assert failed_run['records']==222 and store.verify()
 with store.connect() as c:assert c.execute("select count(*) from alpha_shadow_v1.forecast_runs where mode='PROSPECTIVE'").fetchone()[0]==prospective_before
 return dict(status='NOT RUNNING',mode='SYNTHETIC_DISPOSABLE_REHEARSAL_ONLY',postgres_version=version,least_privilege_login=True,real_artifacts=222,real_live_eligible=0,blocked_rows=222,synthetic_contract_scores=2,baseline_and_research_preserved=True,retry_idempotent=True,source_revision_rejected=True,source_correction_archived=True,early_hit_immature=True,full_horizon_matured=True,outcome_retry_idempotent=True,provider_failure_recorded=True,actual_backend_disconnect_rollback=True,db_reconnect_recovery=True,append_only_verified=True,hash_chain_valid=True,prospective_rows_created=0,production_touched=False)

if __name__=='__main__':
 result=rehearse(os.environ['ALPHA_SHADOW_STAGE_DSN']);print(json.dumps(result,indent=2));(OUT/'staging-rehearsal.json').write_text(json.dumps(result,indent=2)+'\n')
