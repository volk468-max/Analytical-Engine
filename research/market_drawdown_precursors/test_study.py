import hashlib,json,unittest
import numpy as np
import pandas as pd
from common import *
from anatomy import episodes
from study import fit_logit,predict,split_rows,task_rows
from evaluate import bootstrap_daily,holm,PRIMARY_REPS,ratio,primary_pair

class MarketResearchTests(unittest.TestCase):
    def test_protocol_and_raw_hashes(self):
        m=check_sources();self.assertEqual(len(m['sources']),6);self.assertFalse(m['original_PIT_certified'])
        reg=json.loads((OUT/'protocol-registration.json').read_text());self.assertEqual(hashlib.sha256((OUT/'protocol-market-baseline-addendum.md').read_bytes()).hexdigest(),reg['market_baseline_addendum_sha256'])
    def test_holm_resolution_and_known_values(self):
        self.assertLess(33/(PRIMARY_REPS+1),.05);np.testing.assert_allclose(holm([.01,.03,.04]),[.03,.06,.06])
    def test_primary_family_exactly_33(self):
        from evaluate import pairs
        n=sum(primary_pair('MARKET' if s in MARKET else 'STOCK',m,b) for s in SYMBOLS for m,b in pairs('MARKET' if s in MARKET else 'STOCK'))
        self.assertEqual(n,33)
    def test_synchronous_bootstrap_keeps_columns_together(self):
        num=np.arange(100,dtype=float);b=bootstrap_daily(np.column_stack([num,num]),np.ones((100,2)),99,40);np.testing.assert_array_equal(b[:,0],b[:,1])
    def test_bootstrap_constant_difference(self):
        b=bootstrap_daily(np.full((82,2),.125),np.ones((82,2)),99,20);np.testing.assert_allclose(b,.125)
    def test_zero_denominators_are_unknown(self):self.assertTrue(np.isnan(ratio(0,0)));self.assertEqual(ratio(1,2),.5)
    def test_feature_prefix_unchanged_by_future(self):
        dates=pd.bdate_range('2000-01-01',periods=310).strftime('%Y-%m-%d');df=pd.DataFrame({'close':100+np.arange(310)*.1},index=dates)
        a=feature_frame(df.iloc[:280]);changed=df.copy();changed.iloc[280:,0]=.001;b=feature_frame(changed).iloc[:280];pd.testing.assert_frame_equal(a,b)
    def test_constant_split_scale_invariant_features(self):
        dates=pd.bdate_range('2000-01-01',periods=300).strftime('%Y-%m-%d');df=pd.DataFrame({'close':np.exp(np.arange(300)*.003+np.sin(np.arange(300))*.01)},index=dates)
        a=feature_frame(df);b=feature_frame(df*100);np.testing.assert_allclose(a.select_dtypes('number'),b.select_dtypes('number'),atol=1e-12,equal_nan=True)
    def test_touch_terminal_distinct_and_anchor_excluded(self):
        df=pd.DataFrame({'close':[100,101,102],'low':[1,94,99],'available_at':['2020-01-02','2020-01-03','2020-01-04']},index=['2020-01-01','2020-01-02','2020-01-03'])
        self.assertEqual(label(df,'2020-01-01',5,2,'TOUCH')[0],1);self.assertEqual(label(df,'2020-01-01',5,2,'TERMINAL')[0],0)
        df.loc['2020-01-02','low']=99;self.assertEqual(label(df,'2020-01-01',5,2,'TOUCH')[0],0)
    def test_early_hit_does_not_mature_incomplete_label(self):
        df=pd.DataFrame({'close':[100,90],'low':[100,80],'available_at':['2020-01-02','2020-01-03']},index=['2020-01-01','2020-01-02'])
        self.assertEqual(label(df,'2020-01-01',5,10,'TOUCH'),(None,None))
    def test_training_standardization_and_coefficients_ignore_calibration(self):
        X=np.arange(120).reshape(60,2)/100;y=np.arange(60)%2;Z=X[:20]+1;cy=y[:20]
        a=fit_logit(X,y,Z,cy);b=fit_logit(X,y,Z+100,1-cy);np.testing.assert_array_equal(a['mean'],X.mean(0));np.testing.assert_array_equal(a['coef'],b['coef']);np.testing.assert_array_equal(a['scale'],b['scale'])
    def test_degenerate_class_backoff_finite(self):
        X=np.ones((30,2));f=fit_logit(X,np.zeros(30),X[:10],np.zeros(10));self.assertEqual(f['status'],'CONSTANT_CLASS_BETA_BACKOFF');p,q=predict(X,f);self.assertTrue(np.all(np.isfinite(q)));self.assertTrue(np.all((q>0)&(q<1)))
    def test_episode_nesting_equal_peaks_recovery(self):
        df=pd.DataFrame({'close':[100,100,98,90,95,85,100,99,94,101]},index=[str(i).zfill(2) for i in range(10)])
        es=episodes(df,'SPY');self.assertEqual(len(es),2);self.assertEqual(es[0]['peak_date'],'01');self.assertEqual(es[0]['onset_date'],'02');self.assertEqual(es[0]['trough_date'],'05');self.assertEqual(es[0]['recovery_date'],'06')
    def test_open_episode_censored(self):
        df=pd.DataFrame({'close':[100,98,90]},index=['a','b','c']);e=episodes(df,'SPY')[0];self.assertTrue(e['right_censored']);self.assertIsNone(e['recovery_date']);self.assertTrue(e['left_truncated'])
    def test_actual_fit_cutoffs_and_separation(self):
        audits=read('fit-audit.csv');fits=[r for r in audits if r['status']=='FIT'];self.assertTrue(fits)
        for r in fits:self.assertLessEqual(r['last_training_maturity'],r['training_cutoff']);self.assertLess(r['calibration_last_maturity'],r['test_first']);self.assertGreaterEqual(int(r['purge']),max(20,int(r['horizon'])))
    def test_actual_market_stock_labels_never_pooled(self):
        rows=read('predictive-evaluation.csv');p=[r for r in rows if r['primary']=='True'];self.assertEqual(len(p),33)
        for r in rows:self.assertEqual(r['population'],'MARKET' if r['symbol'] in MARKET else 'STOCK')
    def test_actual_pre_onset_and_control_boundary(self):
        snap=read('pre-onset-snapshots.csv');self.assertTrue(snap)
        for r in snap:
            if r['status']=='AVAILABLE':self.assertLess(r['snapshot_date'],r['onset_date'])
        ep=read('market-episodes.csv')
        for r in read('matched-controls.csv'):
            if r['match_status']=='MATCH':self.assertFalse(any(e['symbol']==r['symbol'] and e['onset_date']<=r['control_date']<=e['end_date'] for e in ep))
    def test_missing_factors_stopped_not_imputed(self):
        rs=read('missing-factors.csv');self.assertEqual(len(rs),6);self.assertTrue(all(r['decision']=='STOP_NO_GO' and r['imputed']=='False' for r in rs))
    def test_operating_thresholds_are_fixed(self):
        rs=read('metrics.csv.gz');self.assertEqual({r['operating_threshold'] for r in rs},{'0.2','0.5'})
    def test_pure_market_comparator_has_no_own_stock_features(self):
        rs=read('stock-market-only-weights.csv');self.assertTrue(rs)
        for r in rs:
            keys=json.loads(r['keys']);self.assertIn('qqq_log_rv20',keys);self.assertNotIn('log_rv20',keys);self.assertFalse(set(keys)&set(X_KEYS))
    def test_live_infrastructure_not_started(self):
        schema=json.loads((OUT/'shadow-log-schema.json').read_text());self.assertEqual(schema['mode'],'SPECIFICATION_ONLY');self.assertFalse(schema['infrastructure_started'])

if __name__=='__main__':unittest.main()
