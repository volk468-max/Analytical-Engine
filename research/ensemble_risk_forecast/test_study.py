import csv,gzip,hashlib,json,unittest
from pathlib import Path
import numpy as np
import study
from economics import restore

class EnsembleTests(unittest.TestCase):
    def test_regime_metadata_separate_from_probability(self):
        with gzip.open(study.OUT/'predictions.csv.gz','rt') as f:rows=list(csv.DictReader(f))
        self.assertEqual({r['market_regime'] for r in rows},{'UP','DOWN','MIXED'})
        self.assertTrue(all(0<=float(r['regime'])<=1 for r in rows))
        with (study.OUT/'metrics.csv').open() as f:ms=list(csv.DictReader(f))
        self.assertEqual({r['value'] for r in ms if r['dimension']=='regime'},{'UP','DOWN','MIXED'})

    def test_primary_bootstrap_can_resolve_holm_family(self):
        self.assertLess(162/(study.PRIMARY_REPS+1),.05)
        r=json.loads((study.OUT/'protocol-registration.json').read_text())
        self.assertEqual(hashlib.sha256((study.OUT/'protocol-numerical-addendum.md').read_bytes()).hexdigest(),r['addendum_sha256'])

    def test_published_protocol_frozen(self):
        reg=json.loads((study.OUT/'protocol-registration.json').read_text())
        self.assertEqual(hashlib.sha256((study.OUT/'protocol.md').read_bytes()).hexdigest(),reg['sha256'])
    def test_synchronous_blocks_and_gaps(self):
        c=study.counts(81,50,40);self.assertTrue(np.all(c.sum(axis=1)==81))
        # Same date weights shared across stocks, gaps stay in sampled calendar.
        idx=np.array([0,0,80]);w=c[:,idx];np.testing.assert_array_equal(w[:,0],w[:,1])
        self.assertFalse(np.array_equal(w[:,0],w[:,2]))
    def test_confusion_denominators(self):
        r=study.metric_arrays(np.array([1,1,0,0]),np.array([.9,.2,.8,.1]),np.array([1,0,1,0]),np.ones((1,4)))
        for k in ('precision','recall','false_positive_rate','warning_frequency'):self.assertEqual(r[k][0],.5)
    def test_no_alert_precision_unknown(self):
        r=study.metric_arrays(np.array([0,1]),np.array([.1,.2]),np.zeros(2),np.ones((1,2)))
        self.assertTrue(np.isnan(r['precision'][0]));self.assertEqual(r['recall'][0],0)
    def test_consensus_uses_count_not_mapped_probability(self):
        self.assertEqual(study.alert([{'votes':3,'A3':.1}], 'A3')[0],1)
    def test_meta_label_maturity(self):
        import datetime
        dates=[(datetime.date(2023,1,1)+datetime.timedelta(days=i)).isoformat() for i in range(200)]
        rs=[dict(date=d,decision_at=d+'T00:00',label_available_at=dates[min(i+20,199)]+'T00:00') for i,d in enumerate(dates)]
        tr,cal=study.meta_split(rs)
        self.assertLess(max(r['label_available_at'] for r in tr),min(r['decision_at'] for r in cal))
        self.assertGreaterEqual(cal[0]['date'],dates[120])
    def test_stack_future_labels_cannot_change_fit(self):
        rs=[dict({k:.15+.7*((i+j)%7)/6 for j,k in enumerate(study.VOTES)},y=float(i%3==0)) for i in range(60)]
        a=study.fit_stack(rs[:30],rs[30:45]);b=study.fit_stack(rs[:30],rs[30:45]);np.testing.assert_allclose(a[0],b[0]);self.assertEqual(a[1:],b[1:])
        changed=[dict(r,y=1-r['y']) for r in rs[45:]]
        # Predictions depend on features only, never test labels.
        np.testing.assert_allclose(study.predict_stack(rs[45:],a),study.predict_stack(changed,a))
    def test_constant_class_backoff(self):
        rs=[dict({k:.2 for k in study.VOTES},y=0.) for _ in range(30)]
        fit=study.fit_stack(rs[:20],rs[20:]);self.assertTrue(np.all(fit[0]==0));self.assertTrue(np.all(np.isfinite(study.predict_stack(rs,fit))))
    def test_holm_known_values(self):np.testing.assert_allclose(study.holm([.01,.03,.04]),[.03,.06,.06])
    def test_restore_cash_conservation(self):
        q,left=restore(10,1000,120);self.assertLess(q,10);self.assertAlmostEqual(q*120*1.0005**2+left,1000)
        q,left=restore(10,1000,80);self.assertEqual(q,10);self.assertGreater(left,0)
    def test_cluster_merges_common_stock_shocks(self):
        study.CALENDAR=[str(i) for i in range(100)]
        rs=[dict(date='1',horizon=20,y=1),dict(date='1',horizon=20,y=1),dict(date='15',horizon=20,y=1),dict(date='50',horizon=20,y=1)]
        self.assertEqual(study.clusters(rs,[1]*4),2)
    def test_actual_fold_maturity(self):
        with (study.OUT/'fit-audit.csv').open() as f:rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),54)
        for r in rows:
            self.assertLess(r['meta_maturity_max'],r['cal_first']);self.assertLess(r['cal_maturity_max'],r['test_first'])
    def test_published_predictions_and_equal_average(self):
        with gzip.open(study.OUT/'predictions.csv.gz','rt') as f:rs=list(csv.DictReader(f))
        self.assertEqual(len(rs),34200)
        for r in rs:
            self.assertAlmostEqual(float(r['B']),np.mean([float(r[k]) for k in study.VOTES]))
            self.assertEqual(int(r['votes']),sum(float(r[k])>=.5 for k in study.VOTES))
            for k in study.MODELS:self.assertTrue(0<=float(r[k])<=1)
    def test_economic_ledger_reconciles(self):
        with gzip.open(study.OUT/'economic-daily.csv.gz','rt') as f:rows=list(csv.DictReader(f))
        for r in rows:
            self.assertAlmostEqual(float(r['nav']),float(r['price_only_nav'])+float(r['dividend_receivable']),places=7)
            self.assertGreaterEqual(float(r['free_cash']),0);self.assertGreaterEqual(float(r['reserved_cash']),0)
        with (study.OUT/'economic-summary.csv').open() as f:sums=list(csv.DictReader(f))
        self.assertEqual(len(sums),36)
        for r in sums:self.assertAlmostEqual(float(r['delta_nav']),float(r['final_nav'])-float(r['bh_final_nav']),places=7)

if __name__=='__main__':unittest.main()
