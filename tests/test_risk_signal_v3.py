import csv,gzip,hashlib,json
import unittest
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from pathlib import Path
from aae.research.risk_signal_v3 import evaluate,RiskV3Config,catalogue,REQUIRED,OPTIONAL
from aae.research.risk_v3_features import build_features,wilder_rsi
from aae.research.risk_v3_evaluation import significant_events,event_table,entry_outcomes,score_run,training_objective
from aae.research.risk_v3_study import run,choose
from aae.backtest.simulator import Bar,Observation

NOW=datetime(2026,10,2,tzinfo=timezone.utc)


def indicators(**changes):
    values=dict(close=100,ma20=98,ma50=95,ma200=90,drawdown_20_pct=-1,drawdown_60_pct=-1,
        return_5_pct=1,return_10_pct=3,fall_acceleration_5_pp=1,
        ma20_slope_5_pct=1,ma50_slope_5_pct=1,ma20_slope_change_pp=.1,ma50_slope_change_pp=.1,
        rsi14=60,relative_return_qqq20_pp=1,relative_return_sox20_pp=1,
        rv20_pct=20,rv60_pct=20,rv20_change_5_ratio=0,vix=15,support=80)
    values.update(changes);return values


def quality():
    return {**{prefix+'_observed_at':NOW-timedelta(hours=4) for prefix in ('quote','qqq','sox','vix')},
            **{prefix+'_available_at':NOW for prefix in ('quote','qqq','sox','vix')},'publication_vintage_verified':False}


def deteriorating(**changes):
    return indicators(**dict(dict(close=90,ma20=98,ma50=95,drawdown_20_pct=-9,drawdown_60_pct=-15,
        return_5_pct=-6,fall_acceleration_5_pp=-4,ma20_slope_5_pct=-1,ma50_slope_5_pct=-.5,
        ma20_slope_change_pp=-1,rsi14=38,relative_return_qqq20_pp=-5,relative_return_sox20_pp=-3),**changes))


def candle_pack(prices,base=datetime(2021,1,1,tzinfo=timezone.utc),symbol='AMD'):
    return [Bar(symbol,base+timedelta(days=i,hours=14),base+timedelta(days=i,hours=20),base+timedelta(days=i,hours=21),
                p,p+1,p-1,p,'synthetic tests only') for i,p in enumerate(prices)]


def labelled_signals(prices,levels,base=datetime(2021,1,1,tzinfo=timezone.utc)):
    return [dict(symbol='AMD',date=(base+timedelta(days=i)).date().isoformat(),risk_level=level,
        indicators={'close':p,'vix':15},conditions={'support_broken':False},active_conditions=[],
        decision_at=(base+timedelta(days=i,hours=21)).isoformat()) for i,(p,level) in enumerate(zip(prices,levels))]


class RiskSignalTests(unittest.TestCase):
    def test_normal_market_holds_all_variants(self):
        for variant in ('A','B','C'):
            self.assertEqual(evaluate('AMD',NOW,indicators(),quality(),variant=variant)['risk_level'],'HOLD')

    def test_reduce_without_high_vix_or_support_break(self):
        for variant in ('A','B','C'):
            result=evaluate('AMD',NOW,deteriorating(),quality(),variant=variant)
            self.assertEqual(result['risk_level'],'REDUCE')
            self.assertFalse(result['conditions']['vix_stress'])
            self.assertFalse(result['conditions']['support_broken'])

    def test_critical_requires_stronger_evidence(self):
        result=evaluate('AMD',NOW,deteriorating(rv20_pct=40,rv20_change_5_ratio=.5),quality(),variant='B')
        self.assertEqual(result['risk_level'],'CRITICAL')

    def test_missing_required_indicators_never_reduce(self):
        for field in REQUIRED:
            values=deteriorating();values[field]=None
            result=evaluate('AMD',NOW,values,quality())
            self.assertEqual(result['data_status'],'DATA_UNAVAILABLE')
            self.assertIsNone(result['risk_level'])

    def test_stale_mandatory_quote_suppresses_level(self):
        q=quality();q['quote_observed_at']=NOW-timedelta(days=7)
        result=evaluate('AMD',NOW,deteriorating(),q)
        self.assertEqual(result['data_status'],'STALE');self.assertIsNone(result['risk_level'])

    def test_future_publication_is_unavailable(self):
        q=quality();q['qqq_available_at']=NOW+timedelta(seconds=1)
        self.assertEqual(evaluate('AMD',NOW,deteriorating(),q)['data_status'],'DATA_UNAVAILABLE')

    def test_missing_optional_vix_is_not_a_gate(self):
        q=quality();q.pop('vix_available_at')
        result=evaluate('AMD',NOW,deteriorating(vix=100),q)
        self.assertEqual(result['risk_level'],'REDUCE');self.assertIsNone(result['indicators']['vix'])
        self.assertEqual(result['quality']['optional_sources']['vix'],'DATA_UNAVAILABLE')

    def test_stale_vix_cannot_contribute_to_score(self):
        q=quality();q['vix_observed_at']=NOW-timedelta(days=7)
        result=evaluate('AMD',NOW,deteriorating(vix=100),q,variant='C')
        self.assertIsNone(result['conditions']['vix_stress'])
        self.assertNotIn('vix_stress',result['score_contributions']['volatility']['active'])

    def test_vix_alone_cannot_reduce(self):
        for variant in ('A','B','C'):
            self.assertNotIn(evaluate('AMD',NOW,indicators(vix=100),quality(),variant=variant)['risk_level'],('REDUCE','CRITICAL'))

    def test_correlated_trend_is_one_confirmation_group(self):
        result=evaluate('AMD',NOW,deteriorating(relative_return_qqq20_pp=1,relative_return_sox20_pp=1),quality(),variant='B')
        self.assertEqual(sum(result['confirmation_groups'].values()),2)
        self.assertEqual(result['risk_level'],'WATCH')

    def test_score_contributions_are_capped_and_reconcile(self):
        result=evaluate('AMD',NOW,deteriorating(ma200=110,rv20_pct=50,vix=40,support=95),quality(),variant='C')
        self.assertEqual(result['score'],sum(v['points'] for v in result['score_contributions'].values()))
        self.assertLessEqual(result['score_contributions']['trend']['points'],3)
        self.assertTrue(result['score_used_for_decision'])

    def test_change_explanations_include_activation(self):
        old=evaluate('AMD',NOW,indicators(),quality())
        new=evaluate('AMD',NOW,deteriorating(),quality(),previous=old)
        self.assertIn('HOLD -> REDUCE',new['change_reasons'])
        self.assertTrue(any('Activated:' in s for s in new['change_reasons']))

    def test_forward_fields_cannot_enter_engine(self):
        with self.assertRaises(ValueError):
            evaluate('AMD',NOW,dict(deteriorating(),forward_20_pct=-20),quality())

    def test_no_sizing_or_orders_in_payload(self):
        result=evaluate('AMD',NOW,deteriorating(),quality())
        self.assertFalse({'position_multiplier','target_weight_pct','shares','order','quantity'} & set(result))
        self.assertTrue(result['research_only'])

    def test_invalid_values_and_configuration(self):
        for change in ({'rsi14':150},{'rv20_pct':-1},{'close':float('nan')},{'ma20':0}):
            self.assertIsNone(evaluate('AMD',NOW,deteriorating(**change),quality())['risk_level'])
        with self.assertRaises(ValueError):RiskV3Config(score_reduce=12)

    def test_wilder_rsi_flat_up_down(self):
        self.assertEqual(wilder_rsi([100]*30),50)
        self.assertEqual(wilder_rsi(list(range(100,130))),100)
        self.assertEqual(wilder_rsi(list(range(130,100,-1))),0)

    def test_future_prices_do_not_change_feature_prefix(self):
        data=candle_pack([100+i*.1 for i in range(205)]+[90])
        changed=data[:-1]+[replace(data[-1],open=80,high=81,low=79,close=80)]
        qqq=candle_pack([100]*206,symbol='QQQ')
        a=build_features(data,[],qqq);b=build_features(changed,[],qqq)
        self.assertEqual(a[:-1],b[:-1])
        self.assertEqual(a[-1]['prior_peak_20'],data[-2].close)

    def test_future_benchmark_is_not_available(self):
        data=candle_pack([100]*205);qqq=candle_pack([100]*205,symbol='QQQ')
        qqq[-1]=replace(qqq[-1],available_at=qqq[-1].available_at+timedelta(days=1))
        row=build_features(data,[],qqq)[-1]
        result=evaluate('AMD',row['decision_at'],row['indicators_v3'],row['quality_v3'])
        self.assertIsNone(result['risk_level'])

    def test_split_scale_does_not_change_signal_state(self):
        data=candle_pack([100+i*.1 for i in range(200)]+[100,95,90,85,80])
        qqq=candle_pack([100]*205,symbol='QQQ')
        scaled=[replace(b,open=b.open/10,high=b.high/10,low=b.low/10,close=b.close/10) for b in data]
        for a,b in zip(build_features(data,[],qqq)[-5:],build_features(scaled,[],qqq)[-5:]):
            x=evaluate('AMD',a['decision_at'],a['indicators_v3'],a['quality_v3'],variant='C')
            y=evaluate('AMD',b['decision_at'],b['indicators_v3'],b['quality_v3'],variant='C')
            self.assertEqual(x['risk_level'],y['risk_level'])

    def test_forward_outcomes_are_separate_and_censored(self):
        signals=labelled_signals([100]*30,['HOLD']*5+['REDUCE']*25)
        outcomes=entry_outcomes(signals,'2021-01-01','2021-01-30')
        self.assertEqual(len(outcomes),1)
        self.assertEqual(outcomes[0]['forward_20_pct'],0)
        shorter=entry_outcomes(signals,'2021-01-01','2021-01-15')
        self.assertTrue(shorter[0]['censored_20']);self.assertIsNone(shorter[0]['forward_20_pct'])

    def test_false_reduce_definition_after_growth(self):
        signals=labelled_signals(list(range(100,130)),['HOLD']*2+['REDUCE']*28)
        self.assertTrue(entry_outcomes(signals,'2021-01-01','2021-01-30')[0]['false_reduce_followed_by_growth'])

    def test_no_duplicate_entry_at_reporting_boundary(self):
        signals=labelled_signals([100]*40,['HOLD']+['REDUCE']*39)
        self.assertEqual(entry_outcomes(signals,'2021-01-10','2021-02-09'),[])

    def test_event_leads_can_be_late(self):
        prices=[100]*21+[98,94,89,84,79,81]
        features=[dict(symbol='AMD',date=s['date'],close=p) for p,s in zip(prices,labelled_signals(prices,['HOLD']*len(prices)))]
        signals=labelled_signals(prices,['HOLD']*24+['REDUCE']*3)
        events=event_table(features,signals,'2021-01-01','2021-02-28')
        self.assertEqual(events[0]['reduce_lead_10_sessions'],-1)
        self.assertEqual(events[0]['reduce_lead_20_sessions'],1)

    def test_event_censoring_cannot_use_future_trough(self):
        prices=[100]*21+[98,94,89,84,79,50]
        signals=labelled_signals(prices,['HOLD']*len(prices))
        features=[dict(symbol='AMD',date=s['date'],close=p) for s,p in zip(signals,prices)]
        events=event_table(features,signals,'2021-01-01','2021-01-25')
        self.assertEqual(events[0]['trough_date'],'2021-01-25')
        self.assertIsNone(events[0]['drawdown_20_date'])

    def test_actual_fold_training_precedes_testing(self):
        rows=list(csv.DictReader(open('reports/risk-signal-v3/training-candidates.csv')))
        self.assertEqual(len(rows),36)
        for row in rows:
            self.assertLess(row['training_end'],row['test_start'])
        self.assertEqual(sum(row['selected']=='True' for row in rows),12)

    def test_actual_signal_dates_and_quality(self):
        manifest=json.loads(Path('reports/risk-signal-v3/run.json').read_text())
        self.assertEqual(manifest['daily_rows'],21717)
        with gzip.open('reports/risk-signal-v3/daily-signals.jsonl.gz','rt') as file:
            for line in file:
                signal=json.loads(line)
                self.assertLessEqual(signal['date'],'2026-10-22')
                self.assertNotIn('forward_20_pct',signal['indicators'])
                if signal['data_status']!='OK':self.assertIsNone(signal['risk_level'])
                self.assertFalse(signal['quality']['publication_vintage_verified'])

    def test_original_modules_unchanged(self):
        source=json.loads(Path('reports/risk-backtest-v1/run.json').read_text())['source_sha256']
        for suffix in ('aae/engines/decision_engine.py','aae/engines/tactical_risk_overlay.py','aae/backtest/simulator.py'):
            digest=next(h for name,h in source.items() if name.endswith(suffix))
            self.assertEqual(hashlib.sha256(Path(suffix).read_bytes()).hexdigest(),digest)
        diagnostic=json.loads(Path('reports/risk-diagnostics/run.json').read_text())['source_sha256']
        self.assertEqual(hashlib.sha256(Path('aae/backtest/diagnostics.py').read_bytes()).hexdigest(),next(h for name,h in diagnostic.items() if name.endswith('aae/backtest/diagnostics.py')))


if __name__=='__main__':unittest.main()
