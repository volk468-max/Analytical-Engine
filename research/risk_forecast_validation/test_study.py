import unittest
from types import SimpleNamespace
from datetime import datetime,timezone,timedelta
import numpy as np
import csv,json,gzip
from pathlib import Path
from study import split_allowed,terminal_label,regime_at,scores,confusion,bootstrap_losses,lot


class ValidationTests(unittest.TestCase):
    def test_actual_fit_cutoffs_and_calibration_separation(self):
        out=Path(__file__).resolve().parents[2]/'reports/risk-forecast-v2-predictive-validation'
        with (out/'fit-audit.csv').open() as f:audits=list(csv.DictReader(f))
        self.assertEqual(len(audits),162)
        self.assertTrue(all(r['last_training_maturity']<=r['cutoff'] and r['last_training_anchor']<r['cutoff'] for r in audits))
        with (out/'metrics.csv').open() as f:metrics=list(csv.DictReader(f))
        self.assertEqual(len(metrics),504)
        groups={}
        for r in metrics:groups.setdefault((r['symbol'],r['target'],r['horizon'],r['threshold_pct']),set()).add(r['n'])
        self.assertTrue(all(len(ns)==1 for ns in groups.values()))
        s=json.loads((out/'summary.json').read_text());self.assertFalse(s['independent_untouched_holdout']);self.assertFalse(s['source_vintage_verified'])

    def test_full_maturity_required(self):
        self.assertFalse(split_allowed('2022-01-01',None,'2023-01-01',1,300))
        self.assertFalse(split_allowed('2022-01-01','2023-01-02','2023-01-01',1,300))

    def test_embargo_boundary(self):
        self.assertTrue(split_allowed('2022-01-01','2022-02-01','2023-01-01',279,300))
        self.assertFalse(split_allowed('2022-01-01','2022-02-01','2023-01-01',280,300))

    def test_cutoff_anchor_excluded(self):self.assertFalse(split_allowed('2023-01-01','2023-01-02','2023-01-01',1,300))
    def test_terminal_not_touch(self):
        # A future intrawindow low80 on anchor100 hits10%; final close99 does not.
        self.assertTrue(80<=100*(1-.1));self.assertFalse(terminal_label(-1,.1))
        self.assertTrue(terminal_label(-10,.1));self.assertIsNone(terminal_label(None,.1))

    def test_regime_excludes_future_prices(self):
        start=datetime(2020,1,1,tzinfo=timezone.utc)
        bars=[SimpleNamespace(available_at=start+timedelta(days=i),close=100+i) for i in range(200)]
        result=regime_at(bars,start+timedelta(days=199));self.assertEqual(result,'UP')
        bars.append(SimpleNamespace(available_at=start+timedelta(days=200),close=.001))
        self.assertEqual(regime_at(bars,start+timedelta(days=199)),result)

    def test_regime_missing_warmup_not_fabricated(self):self.assertIsNone(regime_at([],datetime.now(timezone.utc)))
    def test_scores_hand_computation(self):
        b,l=scores([0,1],[.25,.75]);np.testing.assert_allclose(b,[.0625,.0625]);np.testing.assert_allclose(l,[-np.log(.75)]*2)
    def test_invalid_probability(self):
        with self.assertRaises(ValueError):scores([0,1],[.2,1.1])
    def test_confusion_denominators(self):
        r=confusion([1,1,0,0],[.9,.2,.8,.1],.5);self.assertEqual((r['tp'],r['fp'],r['fn'],r['tn']),(1,1,1,1));self.assertEqual(r['recall'],.5);self.assertEqual(r['false_positive_rate'],.5)
    def test_empty_alert_precision_undefined(self):self.assertIsNone(confusion([0,1],[.1,.2],.5)['precision'])
    def test_synchronous_panel_resampling(self):
        # Both stocks on selected date0 are sampled together, unlike IID row sampling.
        a,b=bootstrap_losses([0,1,0,1],[.2,.7,.4,.8],np.array([0,0,1,1]),2,np.array([[2,0],[0,2],[1,1]]))
        self.assertAlmostEqual(a[0],(.04+.09)/2);self.assertAlmostEqual(a[1],(.16+.04)/2)
    def test_lot_no_cash_topup(self):
        r=lot(100,120);self.assertLess(r['restored_qty'],1);self.assertAlmostEqual(r['cash_left'],0);self.assertLess(r['relative_mark'],0)
    def test_lot_surplus_is_cash_not_extra_shares(self):
        r=lot(100,80);self.assertEqual(r['restored_qty'],1);self.assertGreater(r['cash_left'],0);self.assertAlmostEqual(r['relative_mark'],r['cash_left'])


if __name__=='__main__':unittest.main()
