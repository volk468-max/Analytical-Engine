import ast,types,sys,copy,os,unittest,uuid
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock,patch
import numpy as np
import pandas as pd
from research.daily_shadow.core import canonical,sha,utc
from research.daily_shadow_v3.legal import fixture_permit
from . import market_precursors_daily as mdp
from . import market_precursors_reference as frozen
from . import test_vol as vt
from .test_vol import sample,SESSION,NOW

def bundle():
 s=sample()
 for symbol in mdp.SYMBOLS+('NBIS',):
  s.bars[symbol]=copy.deepcopy(s.bars['AMD']);s.currency[symbol]='USD';s.splits[symbol]=[];s.dividends[symbol]=[]
 return s

def reference(path,names):
 source=(Path(__file__).resolve().parents[2]/'reports/market-precursors-daily-v1'/path).read_text();tree=ast.parse(source);tree.body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
 from scipy.special import expit,logit
 from scipy.optimize import minimize_scalar
 from sklearn.linear_model import LogisticRegression
 env=dict(np=np,pd=pd,expit=expit,logit=logit,minimize_scalar=minimize_scalar,LogisticRegression=LogisticRegression);exec(compile(tree,'frozen_mdp','exec'),env);return env

class MarketPrecursorsTests(unittest.TestCase):
 def test_exact_original_features_and_raw_fit(self):
  ref=reference('reference_common.py.txt',('feature_frame',));df=pd.DataFrame({'close':100*np.exp(np.random.default_rng(12).normal(0,.02,350).cumsum())})
  pd.testing.assert_frame_equal(frozen.feature_frame(df),ref['feature_frame'](df))
  original=reference('reference_study.py.txt',('fit_logit','predict','loss'));rng=np.random.default_rng(14);X=rng.normal(size=(500,14));y=rng.integers(0,2,500);Z=rng.normal(size=(80,14));cy=rng.integers(0,2,80)
  a=frozen.fit_raw(X,y);b=original['fit_logit'](X,y,Z,cy)
  for k in ('mean','scale','coef'):np.testing.assert_array_equal(a[k],b[k])
  self.assertEqual(a['intercept'],b['intercept'])
  m=dict(params=a,feature_keys=tuple(str(i) for i in range(14)),created_at=NOW,fit_cutoff='2026-01-01T00:00:00+00:00',last_maturity='2025-12-01T00:00:00+00:00');raw,cal=original['predict'](Z,b)
  for i in range(80):self.assertAlmostEqual(mdp.probability(m,Z[i],NOW)[0],raw[i],places=14)
 def test_manifest_and_required_benchmarks(self):
  self.assertEqual(len(mdp.series()),156);self.assertEqual(mdp.STOCKS,vt.vol.SYMBOLS);self.assertEqual(len(mdp.keys('SPY')),10);self.assertEqual(len(mdp.keys('AMD')),14)
  for symbol in mdp.SYMBOLS:self.assertEqual(len(mdp.required(symbol)),len(set(mdp.required(symbol))))
  for symbol in mdp.MARKET:
   s=bundle();del s.bars[symbol]
   with self.assertRaisesRegex(ValueError,'REQUIRED_MARKET_INPUT_UNAVAILABLE'):mdp.frame(s,'AMD')
 def test_feature_panel_parity_and_causal_future_poisoning(self):
  s=bundle();df=mdp.frame(s,'AMD');own=frozen.feature_frame(vt.vol.frame(s,'AMD'));q=frozen.feature_frame(vt.vol.frame(s,'QQQ'))
  np.testing.assert_allclose(df.stock_relative20,own.r20-q.r20,equal_nan=True)
  task=mdp.series(('AMD',))[1];cut='2026-01-01T00:00:00+00:00';a=mdp.artifact(df,task,cut,NOW,'a'*64)
  poison=copy.deepcopy(s)
  for rows in poison.bars.values():
   for row in rows:
    if row['date']>='2026-01-01':
     for k in ('open','high','low','close','adjusted_close'):row[k]*=3
  b=mdp.artifact(mdp.frame(poison,'AMD'),task,cut,NOW,'b'*64)
  for k in ('n','hits','params','training_rows_sha256','last_maturity'):self.assertEqual(a[k],b[k])
  self.assertLess(a['last_maturity'],a['fit_cutoff']);self.assertFalse(a['calibrated'])
 def test_block_nbis_short_history_and_asof_gates(self):
  s=bundle()
  with self.assertRaisesRegex(ValueError,'UNSUPPORTED_MDP_SYMBOL'):mdp.artifact(mdp.frame(s,'NBIS'),mdp.series(('NBIS',))[0],SESSION+'T00:00:00+00:00',NOW,'a'*64)
  task=mdp.series(('AMD',))[0];m=mdp.artifact(mdp.frame(s,'AMD'),task,SESSION+'T00:00:00+00:00',NOW,s.revision,fixture=True);r=mdp.rows(SESSION,NOW,s,[m],fixture_permit(),reviewed=True)[0];self.assertIsNotNone(r['probability_raw']);self.assertEqual(r['model_name'],'MARKET_PRECURSORS')
  s.retrieved_at='2026-11-18T00:00:00+00:00';self.assertEqual(mdp.rows(SESSION,NOW,s,[m],fixture_permit(),reviewed=True)[0]['reason'],'FUTURE_SOURCE_RETRIEVAL')
 def test_preclose_idempotency_and_partial_manifest(self):
  from .market_precursors_runtime import run_market_precursors
  store=MagicMock();r=run_market_precursors(store,fixture_permit(),MagicMock(),SESSION,clock=lambda:datetime.fromisoformat('2026-11-16T18:00:00+00:00'));self.assertEqual(r['status'],'WAITING_VALID_SESSION_WINDOW');store.connect.assert_not_called()
  for n,status in ((156,'ALREADY_RECORDED'),(12,'PARTIAL_FAILURE')):
   store=MagicMock();c=store.connect.return_value.__enter__.return_value;c.execute.return_value.fetchone.side_effect=[(True,),(n,n)];collector=MagicMock();r=run_market_precursors(store,fixture_permit(),MagicMock(),SESSION,clock=lambda:datetime.fromisoformat(NOW),collector=collector);self.assertEqual(r['status'],status);collector.assert_not_called()
 def test_old_phase_failure_does_not_suppress_precursors(self):
  from .test_worker_fix import DiagnosticTests
  from research.daily_shadow_v3.adapter import VendorError
  with patch.dict(os.environ,{'ALPHA_MARKET_PRECURSORS_ENABLED':'true','ALPHA_MARKET_PRECURSORS_PREFLIGHT_ONCE':'false'}),patch('research.daily_shadow_live.market_precursors_runtime.run_market_precursors',return_value=dict(phase='MARKET_PRECURSORS',status='RECORDED',issued=156,blocked=0)) as issue,patch('research.daily_shadow_live.market_precursors_runtime.inspect_market_precursors',return_value=dict(phase='MARKET_PRECURSORS_SQL_AUDIT',status='DIRECT_READ_ONLY_SQL')):
   code,records,_=DiagnosticTests().run_mock(issue_error=VendorError('SOURCE_STILL_REVISING'))
  issue.assert_called_once();self.assertEqual(code,2)

@unittest.skipUnless(os.environ.get('ALPHA_SHADOW_TEST_DSN'),'Disposable local SQL required')
class MarketPrecursorsSQLTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.template=bundle();cls.prototypes=[]
  for symbol in mdp.SYMBOLS:
   df=mdp.frame(cls.template,symbol);cls.prototypes.extend(mdp.artifact(df,t,SESSION+'T00:00:00+00:00',NOW,cls.template.revision,fixture=True) for t in mdp.series((symbol,)))
 def setUp(self):
  import psycopg
  from cryptography.fernet import Fernet
  from research.daily_shadow_v3.store import ResearchStore
  url=os.environ['ALPHA_SHADOW_TEST_DSN'];info=psycopg.conninfo.conninfo_to_dict(url)
  if info.get('host') not in ('127.0.0.1','localhost') or info.get('dbname')!='alpha_shadow_research':raise ValueError('LOCAL_ONLY')
  self.store=ResearchStore(url,Fernet.generate_key());self.permit=fixture_permit();self.cid=self.store.register(self.permit);self.snap=copy.deepcopy(self.template);self.snap.revision=sha(str(uuid.uuid4()).encode());self.ref=self.store.payload(self.cid,self.snap,self.permit.raw_until);self.models=copy.deepcopy(self.prototypes)
  # Numerical inputs identical to class fixture; only per-test source receipt changes.
  for m in self.models:
   m.pop('version');m['source_hash']=self.snap.revision;m['version']='mdp-daily-v1-'+sha(canonical(m).encode())
  self.rows=mdp.rows(SESSION,NOW,self.snap,self.models,self.permit,reviewed=True);self.key='MDP_TEST:'+str(uuid.uuid4())
 def test_atomic156_idempotent_and_market_stock_targets_separate(self):
  ids=self.store.forecasts(self.key,self.rows,self.models,self.cid,self.ref,self.snap);self.assertEqual(len(ids),156);self.assertEqual(ids,self.store.forecasts(self.key,self.rows,self.models,self.cid,self.ref,self.snap));self.assertTrue(self.store.verify())
  with self.store.connect() as c:self.assertEqual(c.execute("select count(*) filter(where symbol in('SPY','QQQ','SOXX')),count(*) filter(where horizon=30) from alpha_research_v3.forecasts where id=any(%s)",(ids,)).fetchone(),(36,78))
 def test_last_bad_row_rolls_back(self):
  import psycopg
  bad=copy.deepcopy(self.rows);bad[-1]['model_hash']='0'*64
  with self.assertRaises(psycopg.Error):self.store.forecasts(self.key,bad,self.models,self.cid,self.ref,self.snap)
  with self.store.connect() as c:self.assertEqual(c.execute('select count(*) from alpha_research_v3.journal where event_key like %s',(self.key+'%',)).fetchone()[0],0)
 def test_fixture_cannot_become_live_and_raw_fields_rejected(self):
  import psycopg
  with self.assertRaises(psycopg.Error):self.store.forecasts(self.key,self.rows,self.models,self.cid,self.ref,self.snap,run_mode='RESEARCH_FORECAST')
  bad=copy.deepcopy(self.rows);bad[-1]['price']=123
  with self.assertRaises(psycopg.Error):self.store.forecasts(self.key,bad,self.models,self.cid,self.ref,self.snap)
 def test_readonly_audit_and_previous_models_keep_guards(self):
  import psycopg
  from .market_precursors_runtime import inspect_market_precursors
  self.assertEqual(inspect_market_precursors(self.store)['reason'],'DUPLICATES=0')
  # Existing VOL must still reject a stock outside its owner's ten-stock manifest.
  s=self.snap;task=vt.vol.series(('SPY',))[0];m=vt.vol.artifact(vt.vol.frame(s,'SPY'),task,SESSION+'T00:00:00+00:00',NOW,s.revision,fixture=True);row=vt.vol.rows(SESSION,NOW,s,[m],self.permit,reviewed=True)
  with self.assertRaises(psycopg.Error):self.store.forecasts(self.key+':VOL',row,[m],self.cid,self.ref,s)
