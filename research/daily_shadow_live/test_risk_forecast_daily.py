import ast,types,sys,unittest,os,json,copy
from pathlib import Path
import numpy as np
from . import risk_forecast_daily as rf
from .test_vol import sample,SESSION,NOW
from . import test_vol as vt
from research.daily_shadow.core import utc,canonical
from research.daily_shadow_v3.legal import fixture_permit

class RiskForecastTests(unittest.TestCase):
 def reference(self):
  source=(Path(__file__).resolve().parents[2]/'reports/risk-forecast-daily-v1/reference_risk_forecast.py.txt').read_text()
  import hashlib
  manifest=json.loads((Path(__file__).resolve().parents[2]/'reports/risk-forecast-daily-v1/reference-manifest.json').read_text());self.assertEqual(hashlib.sha256(source.encode()).hexdigest(),manifest['sha256'])
  tree=ast.parse(source);tree.body=[n for n in tree.body if not(isinstance(n,ast.ImportFrom) and n.module=='aae.backtest.simulator')]
  module=types.ModuleType('rf_frozen_reference');module.utc=utc;sys.modules[module.__name__]=module;exec(compile(tree,'frozen_rf','exec'),module.__dict__);return module
 def test_exact_source_parity_including_empty_and_low_support_cells(self):
  ref=self.reference();rng=np.random.default_rng(22);rows=[];cells={};hits=0
  for i in range(700):
   f=ref.ForecastFeatures('HOLD',0,-float(rng.uniform(0,30)),float(rng.uniform(10,150)),100.,float(rng.uniform(80,120)),float(rng.uniform(0,100)))
   y=bool(rng.integers(0,2));key=f.cells()['technical_combined'];entry=cells.setdefault(canonical(key),[0,0,set()]);entry[0]+=1;entry[1]+=y;entry[2].add(i//40);hits+=y
   rows.append(dict(features=f,target=y,decision_at='2024-01-01T00:00:00+00:00',label_available_at='2024-02-01T00:00:00+00:00',calendar_index=i))
  bank=ref.ProbabilityBank('2025-01-01T00:00:00+00:00').fit(rows)
  model=dict(created_at=NOW,fit_cutoff='2025-01-01T00:00:00+00:00',last_maturity='2024-02-01T00:00:00+00:00',n=700,hits=hits,count_cells={k:[v[0],v[1],len(v[2])] for k,v in cells.items()})
  for f in [r['features'] for r in rows[:40]]+[ref.ForecastFeatures('CRITICAL',11,-99.,300.,100.,100.,99.)]:
   from types import SimpleNamespace
   self.assertEqual(rf.cell(SimpleNamespace(drawdown_20_pct=f.drawdown_20_pct,rv20_pct=f.rv20_pct,close=f.close,ma50=f.ma50,rsi14=f.rsi14)),f.cells()['technical_combined'])
   expected=bank.predict(f)['technical_combined'];actual,why=rf.probability(model,f.cells()['technical_combined'],NOW);self.assertEqual(actual,expected['probability']);self.assertIsNone(why)
   d=rf.diagnostics(model,f.cells()['technical_combined']);self.assertEqual(d['cell_n'],expected['cell_n']);self.assertEqual(d['status'],expected['status'])
 def test_frame_prior_peak_and_wilder_rsi(self):
  snap=sample();df=rf.frame(snap,'AMD');c=df.close.to_numpy()
  self.assertAlmostEqual(df.iloc[-1].drawdown_20_pct,min(0,(c[-1]/max(c[-21:-1])-1)*100))
  gain=np.maximum(np.diff(c)[:14],0).mean();loss=np.maximum(-np.diff(c)[:14],0).mean()
  for delta in np.diff(c)[14:]:gain=(gain*13+max(delta,0))/14;loss=(loss*13+max(-delta,0))/14
  self.assertAlmostEqual(df.iloc[-1].rsi14,100-100/(1+gain/loss))
 def test_forecast_and_future_poisoning(self):
  snap=sample();df=rf.frame(snap,'AMD');task=rf.series(('AMD',))[0];cut='2026-01-01T00:00:00+00:00'
  a=rf.artifact(df,task,cut,NOW,'a'*64,fixture=True);poison=df.copy();poison.loc[poison.index>='2026-01-01',['close','low']]=99999
  b=rf.artifact(poison,task,cut,NOW,'b'*64,fixture=True)
  for k in ('n','hits','count_cells','training_rows_sha256'):self.assertEqual(a[k],b[k])
  model=rf.artifact(df,task,SESSION+'T00:00:00+00:00',NOW,'a'*64,fixture=True)
  row=rf.rows(SESSION,NOW,snap,[model],fixture_permit(),reviewed=True)[0];self.assertEqual(row['model_name'],'RISK_FORECAST');self.assertIsNotNone(row['probability_raw']);self.assertIn(row['reason'],(None,'LOW_SUPPORT'));self.assertFalse(model['qualified'])
 def test_manifest_and_missing_support(self):
  self.assertEqual(len(rf.series()),120);self.assertEqual(rf.SYMBOLS[5],'GOOG')
  snap=sample('NBIS');df=rf.frame(snap,'NBIS');model=rf.artifact(df,rf.series(('NBIS',))[0],SESSION+'T00:00:00+00:00',NOW,'a'*64)
  self.assertTrue(model['unavailable']);self.assertIsNone(rf.probability(model,(0,0,False,0),NOW)[0])
 def test_preclose_does_not_touch_store(self):
  from unittest.mock import MagicMock
  from datetime import datetime
  from .risk_forecast_runtime import run_risk_forecast
  store=MagicMock();r=run_risk_forecast(store,fixture_permit(),MagicMock(),SESSION,clock=lambda:datetime.fromisoformat('2026-11-16T18:00:00+00:00'));self.assertEqual(r['status'],'WAITING_VALID_SESSION_WINDOW');store.connect.assert_not_called()

@unittest.skipUnless(os.environ.get('ALPHA_SHADOW_TEST_DSN'),'Disposable local SQL required')
class RiskForecastSQLTests(vt.SQLTests):
 def setUp(self):
  super().setUp();self.models=[];self.rows=[]
  for symbol in rf.SYMBOLS:
   df=rf.frame(self.snap,symbol);bank=[rf.artifact(df,t,SESSION+'T00:00:00+00:00',NOW,self.snap.revision,fixture=True) for t in rf.series((symbol,))];self.models.extend(bank);self.rows.extend(rf.rows(SESSION,NOW,self.snap,bank,self.permit,reviewed=True))
 def test_inspector_starts_readonly_after_store_setup_transaction(self):
  from .risk_forecast_runtime import inspect_risk_forecast
  self.assertEqual(inspect_risk_forecast(self.store)['checked'],0)
