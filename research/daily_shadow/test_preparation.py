"""Per-series artifacts, qualification boundaries and actual PostgreSQL staging."""
import copy,json,os,tempfile,unittest,uuid
from pathlib import Path
import psycopg
from .core import *
from .artifacts import freeze,load_artifact,OUT
from .runner import run_once,FixtureProvider
from .demo import MemoryStore
from .providers import UnavailableLiveProvider
from .store import Store
from .rehearsal import rehearse,local_dsn

class ArtifactTests(unittest.TestCase):
 def setUp(self):
  self.rows=[dict(session='2024-01-02',maturity='2024-03-29T00:00:00+00:00',y=0,regime='UP'),dict(session='2024-01-03',maturity='2024-04-01T00:00:00+00:00',y=1,regime='DOWN')];self.series=('SPY','EOD_CLOSE',10,60)
 def model(self,name='HIST'):return freeze(self.rows,self.series,name,{'fixture':'hash'},fit='2025-01-01T00:00:00+00:00')
 def test_future_labels_cannot_change_frozen_artifact(self):
  a=self.model();self.rows.append(dict(session='2024-12-31',maturity='2025-03-01T00:00:00+00:00',y=1,regime='UP'));self.assertEqual(a,self.model());self.rows[-1]['y']=0;self.assertEqual(a,self.model())
 def test_equality_at_cutoff_is_not_mature_support(self):
  self.rows.append(dict(session='2024-12-01',maturity='2025-01-01T00:00:00+00:00',y=1,regime='UP'));self.assertEqual(self.model()['count_bank']['n'],2)
 def test_task_and_model_versions_are_distinct(self):
  a=self.model();self.series=('AMD','EOD_CLOSE',10,60);self.assertNotEqual(a['version'],self.model()['version']);self.assertNotEqual(a['version'],self.model('REGIME')['version'])
 def test_qualification_flags_never_promoted_by_numerical_counts(self):
  m=self.model();self.assertFalse(m['qualified']);self.assertFalse(m['calibrated']);self.assertTrue(m['causal_code_verified']);self.assertIsNone(raw_estimate(m,'EOD_CLOSE:10:60','2025-01-02','2025-01-02T23:30:00+00:00','UP','SPY')[0])
 def test_count_bank_mathematics_only_under_explicit_synthetic_qualification(self):
  m=self.model('REGIME');m.update(qualified=True,qualification_scope='SYNTHETIC_ONLY');p,r=raw_estimate(m,'EOD_CLOSE:10:60','2025-01-02','2025-01-02T23:30:00+00:00','UP','SPY');self.assertIsNone(r);self.assertAlmostEqual(p,10/21)
 def test_model_creation_date_is_an_availability_gate(self):
  m=self.model();m.update(qualified=True,qualification_scope='SYNTHETIC_ONLY',created_at='2025-01-03T00:00:00+00:00');self.assertEqual(raw_estimate(m,'EOD_CLOSE:10:60','2025-01-02','2025-01-02T23:30:00+00:00','UP','SPY')[1],'MODEL_NOT_YET_AVAILABLE')
 def test_missing_regime_returns_null(self):
  m=self.model('REGIME');m['qualified']=True;self.assertEqual(raw_estimate(m,'EOD_CLOSE:10:60','2025-01-02','2025-01-02T23:30:00+00:00',None,'SPY')[1],'MISSING_REGIME_FEATURE')
 def test_cross_symbol_counts_rejected(self):
  m=self.model();m['qualified']=True;self.assertEqual(raw_estimate(m,'EOD_CLOSE:10:60','2025-01-02','2025-01-02T23:30:00+00:00','UP','AMD')[1],'WRONG_MODEL_SYMBOL')
 def test_artifact_tampering_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'m.json';m=self.model();m['count_bank']['hits']=2;p.write_text(json.dumps(m))
   with self.assertRaises(ValueError):load_artifact(p)
 def test_duplicate_training_session_rejected(self):
  self.rows.append(self.rows[0].copy())
  with self.assertRaises(ValueError):self.model()
 def test_registered222_artifacts_are_unqualified_and_maturity_checked(self):
  index=json.loads((OUT/'model-index.json').read_text());self.assertEqual(len(index['models']),222);seen=set()
  for row in index['models']:
   m=load_artifact(OUT/row['file']);self.assertFalse(m['qualified']);self.assertFalse(m['calibrated']);self.assertLess(utc(m['count_bank']['last_maturity']),utc(m['fit_cutoff']));self.assertEqual(m['count_bank']['n'],sum(g['n'] for g in m['count_bank']['groups'].values()));seen.add((m['name'],*m['series'].values()))
  self.assertEqual(len(seen),222)
 def test_unavailable_source_never_invents_timestamp(self):
  v=UnavailableLiveProvider('NO_VERIFIED_CONTRACT').collect('2026-11-06');self.assertIsNone(v['publication_at']);self.assertIsNone(v['ingestion_at']);self.assertFalse(v['source_present'])
 def test_runner_per_series_routing_preserves222_versions_without_network(self):
  from unittest.mock import patch
  models=[load_artifact(OUT/x['file']) for x in json.loads((OUT/'model-index.json').read_text())['models']];store=MemoryStore()
  with patch('socket.socket',side_effect=AssertionError('NO_NETWORK')):
   result=run_once('2026-11-06',UnavailableLiveProvider('NO_CONTRACT'),models,store,'2026-11-06T23:30:00+00:00','2026-11-06T23:30:00+00:00')
  self.assertEqual(result['records'],222);self.assertEqual(len({r['model_version'] for r in store.events}),222);self.assertTrue(all(r['probability_raw'] is None for r in store.events))

DSN=os.environ.get('ALPHA_SHADOW_STAGE_DSN')
@unittest.skipUnless(DSN,'Explicit disposable least-privilege staging DSN required')
class PostgreSQLPreparationTests(unittest.TestCase):
 def setUp(self):self.store=Store(local_dsn(DSN))
 def test_complete_rehearsal(self):
  r=rehearse(DSN);self.assertTrue(r['hash_chain_valid']);self.assertTrue(r['actual_backend_disconnect_rollback']);self.assertEqual(r['prospective_rows_created'],0)
  if os.environ.get('ALPHA_EXPECT_PG_MAJOR'):self.assertTrue(r['postgres_version'].startswith(os.environ['ALPHA_EXPECT_PG_MAJOR']+'.'))
 def test_writer_cannot_register_real_qualified_model(self):
  m=dict(name='HIST',version='bad-'+str(uuid.uuid4()),qualified=True)
  with self.assertRaisesRegex(psycopg.Error,'Separate model registrar'):
   with self.store.connect() as c:self.store.append(c,'model',m['version'],m)
 def test_inner_function_cannot_bypass_contract_guard(self):
  with self.assertRaises(psycopg.errors.InsufficientPrivilege):
   with self.store.connect() as c:c.execute('select alpha_shadow_v1.append_event_v1(%s,%s,%s,%s)',(uuid.uuid4(),'health',str(uuid.uuid4()),'{}'))
 def test_staging_login_is_not_admin_or_registrar(self):
  with self.store.connect() as c:
   self.assertFalse(c.execute("select pg_has_role(session_user,'alpha_shadow_model_registrar','MEMBER')").fetchone()[0]);self.assertFalse(c.execute('select rolsuper or rolcreatedb or rolcreaterole from pg_roles where rolname=session_user').fetchone()[0])
 def fixture(self):
  from .runner import blocked_models
  m=blocked_models()[0];m.update(version='test-'+str(uuid.uuid4()),series=dict(symbol='SPY',label_type='EOD_CLOSE',threshold_pct=10,horizon=10),qualification_scope='SYNTHETIC_ONLY',qualified=True,supported_tasks=['EOD_CLOSE:10:10'],fit_cutoff='2024-01-01T00:00:00+00:00',training=[dict(task='EOD_CLOSE:10:10',symbol='SPY',y=1,regime='UP',maturity='2023-01-01T00:00:00+00:00')])
  v=archive(b'SYNTHETIC', '2025-01-02','2025-01-02T22:00:00+00:00','2025-01-02T22:01:00+00:00',qualification='QUALIFIED_PIT',basis='SPLIT_NORMALIZED_PRICE',anchors={'SPY':100},actions_qualified=True,synthetic=True)
  f=forecast('2025-01-02','SPY','EOD_CLOSE',10,10,m,v,'2025-01-02T23:30:00+00:00','2025-01-02T23:30:00+00:00');f.update(model_name=m['name'],model_version=m['version']);return m,v,f
 def test_synthetic_model_cannot_become_prospective(self):
  m,v,f=self.fixture()
  with self.assertRaisesRegex(psycopg.Error,'Synthetic input/model is not prospective'):self.store.job(str(uuid.uuid4()),'2025-01-02',[m],v,[f],mode='PROSPECTIVE')
 def test_sql_rejects_model_created_after_issuance(self):
  m,v,f=self.fixture();m['created_at']='2025-01-03T00:00:00+00:00'
  with self.assertRaisesRegex(psycopg.Error,'Unsupported or unavailable forecast inputs'):self.store.job(str(uuid.uuid4()),'2025-01-02',[m],v,[f])
 def test_sql_rejects_model_from_another_series(self):
  m,v,f=self.fixture();f['symbol']='AMD'
  with self.assertRaisesRegex(psycopg.Error,'Wrong model series'):self.store.job(str(uuid.uuid4()),'2025-01-02',[m],v,[f])
 def test_wrong_database_or_remote_rehearsal_rejected(self):
  for dsn in ('host=example.com dbname=alpha_shadow_research user=alpha_shadow_test_app','host=127.0.0.1 dbname=production user=alpha_shadow_test_app'):
   with self.assertRaises(ValueError):local_dsn(dsn)
if __name__=='__main__':unittest.main()
