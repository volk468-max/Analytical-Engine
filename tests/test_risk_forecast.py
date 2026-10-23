import csv
import hashlib
import json
import unittest
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from pathlib import Path
import numpy as np
from aae.backtest.simulator import Bar,utc
from aae.research.risk_forecast import ForecastFeatures,ProbabilityBank,barrier_label,MODELS
from aae.research.risk_forecast_statistics import block_counts,metric_samples,ci,effective_n,paired_difference,holm,score_slope


def bars(prices):
    start=datetime(2022,12,1,14,30,tzinfo=timezone.utc)
    return [Bar('AMD',start+timedelta(days=i),start+timedelta(days=i,hours=6,minutes=30),
        start.replace(hour=0,minute=0)+timedelta(days=i+1),p,p,p,p,'synthetic unit test only',False) for i,p in enumerate(prices)]


def features(state='HOLD',score=1,**kw):
    return ForecastFeatures(state,score,kw.get('drawdown_20_pct',-1),kw.get('rv20_pct',30),100,95,55)


def training(target=False,decision='2022-12-01T00:00:00+00:00',maturity='2022-12-20T00:00:00+00:00',feature=None,index=0):
    return dict(features=feature or features(),target=target,decision_at=decision,label_available_at=maturity,calendar_index=index)


class ForecastTests(unittest.TestCase):
    def test_anchor_extremes_do_not_count(self):
        data=bars([100]*7);data[0]=replace(data[0],low=50,high=150)
        label=barrier_label(data,0,5,.1)
        self.assertFalse(label['down_hit']);self.assertFalse(label['up_hit'])

    def test_barrier_hit_not_terminal_return(self):
        data=bars([100,90,100,100,100,100])
        label=barrier_label(data,0,5,.1)
        self.assertTrue(label['down_hit']);self.assertEqual(label['terminal_return_pct'],0)

    def test_both_barriers_and_order_different_dates(self):
        label=barrier_label(bars([100,89,111,105,100,100]),0,5,.1)
        self.assertTrue(label['down_hit']);self.assertTrue(label['up_hit'])
        self.assertEqual(label['hit_order'],'DOWN_FIRST')

    def test_same_bar_order_explicitly_unknown(self):
        data=bars([100]*6);data[1]=replace(data[1],low=89,high=111)
        label=barrier_label(data,0,5,.1)
        self.assertEqual(label['hit_order'],'UNKNOWN_INTRADAY')
        self.assertTrue(label['down_hit']);self.assertTrue(label['up_hit'])

    def test_opening_gap_resolves_same_bar_order(self):
        for opened,expected in ((88,'DOWN_FIRST_AT_OPEN'),(112,'UP_FIRST_AT_OPEN')):
            data=bars([100]*6);data[1]=replace(data[1],open=opened,low=85,high=115)
            self.assertEqual(barrier_label(data,0,5,.1)['hit_order'],expected)

    def test_incomplete_horizon_not_positive_training_label(self):
        label=barrier_label(bars([100,80]),0,20,.1)
        self.assertTrue(label['observed_down_hit'])
        self.assertIsNone(label['down_hit']);self.assertIsNone(label['terminal_return_pct'])
        self.assertIsNone(label['label_available_at'])

    def test_future_outside_horizon_irrelevant(self):
        data=bars([100]*7);before=barrier_label(data,0,5,.1)
        data[6]=replace(data[6],open=10,high=300,low=1,close=10)
        self.assertEqual(before,barrier_label(data,0,5,.1))

    def test_label_unit_scaling_invariant(self):
        data=bars([100,90,110,100,85,105])
        scaled=[replace(b,open=b.open/10,high=b.high/10,low=b.low/10,close=b.close/10) for b in data]
        self.assertEqual(barrier_label(data,0,5,.1),barrier_label(scaled,0,5,.1))

    def test_training_purges_immature_even_if_hit_already_true(self):
        cutoff='2023-01-01T00:00:00+00:00'
        pending=training(True,maturity='2023-01-02T00:00:00+00:00')
        bank=ProbabilityBank(cutoff).fit([training(False),pending])
        self.assertEqual(bank.n,1);self.assertEqual(bank.positives,0)
        self.assertLessEqual(bank.last_maturity,utc(cutoff))

    def test_publication_timestamp_not_horizon_date_gates_training(self):
        bank=ProbabilityBank('2023-01-01T00:00:00+00:00').fit([
            training(True,maturity='2023-01-01T01:00:00+00:00'),training(False)])
        self.assertEqual(bank.n,1)
        boundary=ProbabilityBank('2023-01-01T00:00:00+00:00').fit([
            training(True,maturity='2023-01-01T00:00:00+00:00')])
        self.assertEqual(boundary.n,1)

    def test_no_current_or_future_anchor_training(self):
        bank=ProbabilityBank('2023-01-01T00:00:00+00:00').fit([
            training(True,decision='2023-01-01T00:00:00+00:00',maturity='2023-01-02T00:00:00+00:00'),training(False)])
        self.assertEqual(bank.n,1)

    def test_unseen_cell_backoff_and_low_support(self):
        bank=ProbabilityBank('2023-01-01T00:00:00+00:00').fit([training(False),training(True)])
        pred=bank.predict(features('CRITICAL',10,drawdown_20_pct=-30,rv20_pct=100))
        self.assertTrue(pred['v3_state']['backoff']);self.assertEqual(pred['v3_state']['status'],'LOW_SUPPORT')
        self.assertEqual(pred['v3_state']['probability'],.5)
        self.assertEqual(pred['technical_plus_v3']['probability'],pred['technical_combined']['probability'])

    def test_fit_frozen_and_predict_whitelist(self):
        bank=ProbabilityBank('2023-01-01T00:00:00+00:00').fit([training()])
        with self.assertRaises(ValueError):bank.fit([training(True)])
        with self.assertRaises(TypeError):bank.predict({'target':True})
        with self.assertRaises(TypeError):ForecastFeatures('HOLD',1,-1,30,100,95,55,future_return=10)

    def test_training_future_mutation_does_not_change_forecast(self):
        old=training(False)
        future=training(True,maturity='2023-01-05T00:00:00+00:00')
        a=ProbabilityBank('2023-01-01T00:00:00+00:00').fit([old,future]).predict(features())
        future=dict(future,target=False,features=features('CRITICAL',10))
        b=ProbabilityBank('2023-01-01T00:00:00+00:00').fit([old,future]).predict(features())
        self.assertEqual(a,b)

    def test_independent_up_down_probabilities_may_sum_above_one(self):
        bank=ProbabilityBank('2023-01-01T00:00:00+00:00').fit([training(True) for _ in range(20)])
        p=bank.predict(features())['historical']['probability']
        self.assertGreater(p+p,1)

    def test_probability_score_known_values_and_ties(self):
        result=metric_samples([0,1],[.2,.8],np.ones((1,2)))
        self.assertAlmostEqual(result['brier'][0],.04)
        self.assertAlmostEqual(result['log_loss'][0],-np.log(.8))
        self.assertEqual(result['roc_auc'][0],1);self.assertEqual(result['pr_auc_ap'][0],1)
        tied=metric_samples([0,1],[.5,.5],np.ones((1,2)))
        self.assertEqual(tied['roc_auc'][0],.5);self.assertEqual(tied['pr_auc_ap'][0],.5)

    def test_weighted_partial_ties_have_correct_roc_and_average_precision(self):
        result=metric_samples([1,0,1,0],[.9,.9,.2,.1],np.array([[1,2,3,4]]))
        self.assertAlmostEqual(result['roc_auc'][0],17/24)
        self.assertAlmostEqual(result['pr_auc_ap'][0],7/12)
        imperfect=metric_samples([0,1,1,0],[.1,.4,.35,.8],np.ones((1,4)))
        self.assertAlmostEqual(imperfect['roc_auc'][0],.5)
        self.assertAlmostEqual(imperfect['pr_auc_ap'][0],7/12)

    def test_single_class_metrics_not_applicable(self):
        result=metric_samples([1,1],[.5,.8],np.ones((1,2)))
        self.assertTrue(np.isnan(result['roc_auc'][0]));self.assertTrue(np.isnan(result['pr_auc_ap'][0]))
        self.assertEqual(ci(np.full(100,np.nan)),(None,None))

    def test_synchronous_bootstrap_keeps_cross_stock_shocks_together(self):
        n=80;counts=block_counts(n,100,20)
        index=np.repeat(np.arange(n),2)
        y=np.tile([0,1],n)
        result=metric_samples(y,np.full(2*n,.5),counts[:,index])
        self.assertTrue(np.allclose(result['frequency'],.5))
        self.assertTrue(np.all(counts.sum(axis=1)==n))

    def test_bootstrap_is_contiguous_circular_block_not_iid(self):
        counts=block_counts(20,50,20,seed=7)
        self.assertTrue(np.all(counts==1))
        self.assertTrue(np.array_equal(block_counts(100,10,20),block_counts(100,10,20)))

    def test_effective_n_reduces_for_serial_dependence(self):
        y=np.tile(np.repeat([0,1],40),5)
        neff=effective_n(y,np.arange(len(y)),len(y))
        self.assertLess(neff,len(y)/4)
        self.assertLessEqual(neff,len(y))
        self.assertIsNone(effective_n([0,1],[0,2],3))

    def test_paired_identical_models_no_false_improvement(self):
        n=80;counts=block_counts(n,100,20)
        result=paired_difference(np.tile([0,1],40),np.full(n,.5),np.full(n,.5),np.arange(n),n,counts)
        self.assertEqual(result['brier_difference'],0)
        self.assertEqual(result['brier_difference_low'],0)
        self.assertEqual(result['brier_p_one_sided'],1)
        self.assertEqual(holm([.001,.04,.02]),[.003,.04,.04])

    def test_score_slope_is_not_forced_monotone(self):
        s=score_slope([1,2,3,4],[1,1,0,0],np.ones((1,4)))
        self.assertLess(s[0],0)

    def test_invalid_future_bar_availability_rejected(self):
        data=bars([100]*6)
        data[0]=replace(data[0],available_at=data[1].close_at)
        with self.assertRaises(ValueError):barrier_label(data,0,5,.1)

    def test_empty_fit_stays_frozen_and_unavailable(self):
        bank=ProbabilityBank('2023-01-01T00:00:00+00:00').fit([])
        self.assertIsNone(bank.predict(features())['v3_state']['probability'])
        with self.assertRaises(ValueError):bank.fit([training()])

    def test_actual_training_maturity_and_horizon_censoring(self):
        root=Path('reports/risk-forecast-v1')
        rows=list(csv.DictReader((root/'fit-audit.csv').open()))
        self.assertEqual(len(rows),216)
        for row in rows:
            self.assertLessEqual(utc(row['last_horizon_publication']),utc(row['probability_cutoff']))
            self.assertLess(utc(row['last_anchor']),utc(row['probability_cutoff']))
            self.assertGreater(int(row['excluded_unmatured_anchors']),0)
        for row in csv.DictReader((root/'forecast-daily.csv').open()):
            if row['role']=='TRAINING_DESCRIPTIVE_ONLY':self.assertEqual(row['p_down_v3_state'],'')
            if row['complete']=='False':
                self.assertEqual(row['down_hit'],'');self.assertEqual(row['terminal_return_pct'],'')

    def test_actual_primary_family_and_original_rules_unchanged(self):
        root=Path('reports/risk-forecast-v1')
        rows=list(csv.DictReader((root/'baseline-comparison.csv').open()))
        self.assertEqual(sum(r['primary']=='True' for r in rows),18)
        old=json.loads(Path('reports/risk-signal-v3/run.json').read_text())
        for path,digest in old['source_sha256'].items():
            self.assertEqual(hashlib.sha256(Path(path).read_bytes()).hexdigest(),digest)
        self.assertEqual(hashlib.sha256(Path('reports/risk-signal-v3/daily-signals.jsonl.gz').read_bytes()).hexdigest(),old['output_sha256']['daily-signals.jsonl.gz'])


if __name__=='__main__':unittest.main()
