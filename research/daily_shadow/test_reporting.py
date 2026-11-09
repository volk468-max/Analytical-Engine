import unittest
from .reporting import report
class ReportingTests(unittest.TestCase):
 def test_no_fake_scores(self):self.assertIsNone(report([],[])['brier'])
 def test_synthetic_never_counted_prospective(self):
  f=dict(id='x',mode='SYNTHETIC',status='FORECAST',probability_raw=.5,symbol='SPY',label_type='EOD_CLOSE',threshold_pct=5,horizon=10,model_version='x',session='2026-11-06');self.assertIsNone(report([f],[dict(forecast_id='x',status='MATURED',outcome=True)])['brier'])
 def test_different_series_not_pooled(self):
  f=dict(id='x',status='STATUS_BLOCKED',symbol='SPY',label_type='EOD_CLOSE',threshold_pct=5,horizon=10,model_version='x')
  with self.assertRaises(ValueError):report([f,dict(f,symbol='QQQ')],[])
 def test_metrics_with_supported_calendar(self):
  from .core import calendar
  ds=calendar().sessions[3000:4400];fs=[dict(id=str(i),mode='PROSPECTIVE',status='FORECAST',probability_raw=.5,symbol='SPY',label_type='EOD_CLOSE',threshold_pct=5,horizon=10,model_version='fixture',session=str(d.date())) for i,d in enumerate(ds)];os=[dict(forecast_id=str(i),status='MATURED',outcome=bool(i%2)) for i in range(len(ds))];r=report(fs,os);self.assertEqual(r['brier'],.25);self.assertEqual(len(r['intervals']),3);self.assertAlmostEqual(r['logloss'],.69314718056)
