import copy,os,unittest
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock,patch
import numpy as np
from research.daily_shadow.core import canonical
from research.daily_shadow_v3.legal import fixture_permit
from . import ensemble_daily as ens,test_vol as vt
from .test_vol import sample,SESSION,NOW
from . import test_risk_forecast_daily as reference_tests

def bundle(symbol='AMD'):
 s=sample(symbol);s.bars['QQQ']=copy.deepcopy(s.bars[symbol]);s.currency['QQQ']='USD';s.splits['QQQ']=[];s.dividends['QQQ']=[];return s

class EnsembleTests(unittest.TestCase):
 def test_frozen_v3_exact_body(self):
  root=Path(__file__).resolve().parents[2]
  self.assertEqual((root/'research/daily_shadow_live/frozen_v3.py').read_text(),(root/'reports/ensemble-daily-v1/reference_v3.py.txt').read_text().replace('from aae.backtest.simulator import utc','from research.daily_shadow.core import utc'))
 def test_five_original_probability_formulas_and_mean(self):
  ref=reference_tests.RiskForecastTests().reference();rng=np.random.default_rng(52);rows=[];counts={k:{} for k in ens.COMPONENTS};hits=0
  for i in range(700):
   f=ref.ForecastFeatures(('HOLD','WATCH','REDUCE','CRITICAL')[i%4],i%12,-float(rng.uniform(0,30)),float(rng.uniform(10,150)),100.,float(rng.uniform(80,120)),float(rng.uniform(0,100)));y=bool(rng.integers(0,2));hits+=y
   cells=f.cells();cells['regime']=(('UP','DOWN','MIXED')[i%3],)
   for k in ens.COMPONENTS:
    v=counts[k].setdefault(canonical(cells[k]),[0,0,set()]);v[0]+=1;v[1]+=y;v[2].add(i//40)
   rows.append(dict(features=f,target=y,decision_at='2024-01-01T00:00:00+00:00',label_available_at='2024-02-01T00:00:00+00:00',calendar_index=i,regime=cells['regime']))
  original=ref.ProbabilityBank('2025-01-01T00:00:00+00:00').fit(rows)
  m=dict(created_at=NOW,fit_cutoff='2025-01-01T00:00:00+00:00',last_maturity='2024-02-01T00:00:00+00:00',n=700,hits=hits,component_banks={k:{c:[v[0],v[1],len(v[2])] for c,v in bank.items()} for k,bank in counts.items()})
  for row in rows[:40]:
   feature=row['features'].cells();feature={k:feature[k] for k in ens.COMPONENTS if k!='regime'};feature['regime']=row['regime'];actual=ens.component_predictions(m,feature);expected=original.predict(row['features'])
   for k in ens.COMPONENTS[:-1]:self.assertEqual(actual[k]['probability'],expected[k]['probability'])
   n,pos,_=m['component_banks']['regime'][canonical(row['regime'])];self.assertEqual(actual['regime']['probability'],(pos+20*(hits+1)/702)/(n+20))
   self.assertEqual(ens.probability(m,feature,NOW)[0],float(np.mean([actual[k]['probability'] for k in ens.COMPONENTS])))
  del feature['v3_state']
  with self.assertRaisesRegex(ValueError,'FIVE_COMPONENTS_REQUIRED'):ens.component_predictions(m,feature)
 def test_required_qqq_missing_and_future_poisoning(self):
  with self.assertRaisesRegex(ValueError,'REQUIRED_QQQ_UNAVAILABLE'):ens.frame(sample(),'AMD')
  snap=bundle();df=ens.frame(snap,'AMD');task=ens.series(('AMD',))[1];cut='2026-01-01T00:00:00+00:00';a=ens.artifact(df,task,cut,NOW,'a'*64)
  poisoned=copy.deepcopy(snap)
  for symbol,rows in poisoned.bars.items():
   for row in rows:
    if row['date']>='2026-01-01':
     for k in ('open','high','low','close','adjusted_close'):row[k]*=99
  b=ens.artifact(ens.frame(poisoned,'AMD'),task,cut,NOW,'b'*64)
  for k in ('n','hits','training_rows_sha256','component_banks','last_maturity'):self.assertEqual(a[k],b[k])
  model=ens.artifact(df,task,SESSION+'T00:00:00+00:00',NOW,snap.revision,fixture=True);row=ens.rows(SESSION,NOW,snap,[model],fixture_permit(),reviewed=True)[0]
  self.assertEqual(row['model_name'],'ENSEMBLE_RISK');self.assertIsNotNone(row['probability_raw']);self.assertEqual(len(model['component_banks']),5);self.assertLess(model['last_maturity'],model['fit_cutoff'])
  nbis=bundle('NBIS');m=ens.artifact(ens.frame(nbis,'NBIS'),ens.series(('NBIS',))[0],SESSION+'T00:00:00+00:00',NOW,'a'*64);self.assertTrue(m['unavailable'])
 def test_preclose_and_idempotency(self):
  from .ensemble_runtime import run_ensemble
  store=MagicMock();r=run_ensemble(store,fixture_permit(),MagicMock(),SESSION,clock=lambda:datetime.fromisoformat('2026-11-16T18:00:00+00:00'));self.assertEqual(r['status'],'WAITING_VALID_SESSION_WINDOW');store.connect.assert_not_called()
  c=store.connect.return_value.__enter__.return_value;c.execute.return_value.fetchone.side_effect=[(True,),(120,108)];collector=MagicMock();r=run_ensemble(store,fixture_permit(),MagicMock(),SESSION,clock=lambda:datetime.fromisoformat(NOW),collector=collector);self.assertEqual(r['status'],'ALREADY_RECORDED');collector.assert_not_called()
 def test_legacy_failure_does_not_suppress_ensemble(self):
  from .test_worker_fix import DiagnosticTests
  from research.daily_shadow_v3.adapter import VendorError
  with patch.dict(os.environ,{'ALPHA_ENSEMBLE_RISK_ENABLED':'true','ALPHA_ENSEMBLE_RISK_PREFLIGHT_ONCE':'false'}),patch('research.daily_shadow_live.ensemble_runtime.run_ensemble',return_value=dict(phase='ENSEMBLE_RISK',status='RECORDED',issued=120,blocked=0)) as issue,patch('research.daily_shadow_live.ensemble_runtime.inspect_ensemble',return_value=dict(phase='ENSEMBLE_RISK_SQL_AUDIT',status='DIRECT_READ_ONLY_SQL')):
   code,records,_=DiagnosticTests().run_mock(issue_error=VendorError('SOURCE_STILL_REVISING'))
  issue.assert_called_once();self.assertEqual(code,2);self.assertTrue(any(r.get('phase')=='ENSEMBLE_RISK' for r in records))

@unittest.skipUnless(os.environ.get('ALPHA_SHADOW_TEST_DSN'),'Disposable local SQL required')
class EnsembleSQLTests(vt.SQLTests):
 def setUp(self):
  super().setUp();self.snap.bars['QQQ']=self.snap.bars['AMD'];self.snap.currency['QQQ']='USD';self.snap.splits['QQQ']=[];self.snap.dividends['QQQ']=[];self.ref=self.store.payload(self.cid,self.snap,self.permit.raw_until);self.models=[];self.rows=[]
  for symbol in ens.SYMBOLS:
   df=ens.frame(self.snap,symbol);bank=[ens.artifact(df,t,SESSION+'T00:00:00+00:00',NOW,self.snap.revision,fixture=True) for t in ens.series((symbol,))];self.models.extend(bank);self.rows.extend(ens.rows(SESSION,NOW,self.snap,bank,self.permit,reviewed=True))
 def test_inspector_starts_readonly_after_store_setup_transaction(self):
  from .ensemble_runtime import inspect_ensemble
  self.assertEqual(inspect_ensemble(self.store)['checked'],0)
