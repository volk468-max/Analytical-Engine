import csv,hashlib,json
import unittest
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from pathlib import Path
import numpy as np
from aae.backtest.simulator import Bar,utc
from aae.research.drawdown_anatomy import catalogue,build_features,sector_features,hypotheses,future_label,PRIMARY
from aae.research.drawdown_anatomy_models import RidgeLogit,fit_predict,predictors
from aae.research.drawdown_anatomy_study import controls_and_snapshots,sample_panel


def candles(prices,symbol='AMD',base=datetime(2021,1,1,14,30,tzinfo=timezone.utc)):
    return [Bar(symbol,base+timedelta(days=i),base+timedelta(days=i,hours=6,minutes=30),
        base.replace(hour=0,minute=0)+timedelta(days=i+1),p,p,p,p,'synthetic unit-test fixture only',False) for i,p in enumerate(prices)]


def feature_pack(prices):
    stock=candles(prices);qqq=candles([100+i*.1 for i in range(len(prices))],'QQQ')
    sox=candles([100+i*.05 for i in range(len(prices))],'^SOX')
    volume={b.open_at.date().isoformat():1000 for b in stock}
    return stock,qqq,sox,volume


def row(target=False,maturity='2022-12-20T00:00:00+00:00',**kw):
    return dict(decision_at=kw.get('decision_at','2022-12-01T00:00:00+00:00'),label_available_at=maturity,
        target=target,rv20=kw.get('rv20',30),current_drawdown60=-5,relative_qqq20=-2,relative_sox20=-1,
        v3_state='WATCH',H1=kw.get('H1',False),H2=False,H3=False,H5=False)


class AnatomyTests(unittest.TestCase):
    def test_nested_drawdowns_one_episode_until_true_recovery(self):
        data=candles([100,95,80,90,70,85,100,110,100,95,90])
        events=catalogue(data,end='2021-12-31')
        self.assertEqual(len(events),2)
        self.assertAlmostEqual(events[0]['depth_pct'],30)
        self.assertEqual(events[0]['recovery_date'],'2021-01-07')
        self.assertEqual(events[0]['trough_date'],'2021-01-05')
        self.assertEqual(events[1]['status'],'OPEN_AT_CUTOFF')
        self.assertLess(events[0]['end_index'],events[1]['onset_index'])

    def test_equal_high_latest_peak_and_no_duplicate_zero_events(self):
        events=catalogue(candles([100,100,90,100,100,80,100]),end='2021-12-31')
        self.assertEqual(len(events),2)
        self.assertEqual(events[0]['peak_date'],'2021-01-02')
        self.assertEqual(events[1]['peak_date'],'2021-01-05')

    def test_severity_boundary_buckets(self):
        events=catalogue(candles([100,90,100,85,100,75,100,74,100]),end='2021-12-31')
        self.assertEqual([r['severity'] for r in events],['10-15','15-25','15-25','>25'])

    def test_crossings_and_unfinished_episode(self):
        events=catalogue(candles([100,96,94,89,84,79]),end='2021-12-31')
        self.assertEqual(events[0]['minus_5_date'],'2021-01-03')
        self.assertEqual(events[0]['minus_10_date'],'2021-01-04')
        self.assertEqual(events[0]['minus_20_date'],'2021-01-06')
        self.assertIsNone(events[0]['recovery_date'])

    def test_future_recovery_cannot_complete_cutoff_event(self):
        data=candles([100,85,80,100])
        early=catalogue(data,end='2021-01-03')[0]
        self.assertEqual(early['status'],'OPEN_AT_CUTOFF')
        self.assertEqual(early['trough_date'],'2021-01-03')
        self.assertEqual(catalogue(data,end='2021-01-04')[0]['status'],'RECOVERED')

    def test_episode_definition_sensitivity_invariants(self):
        data=candles([100,95,80,70,85,100])
        for options in ({},{'extrema':'high_low'},{'recovery':.98},{'minimum':.12}):
            result=catalogue(data,end='2021-12-31',**options)
            self.assertEqual(len(result),1)
            self.assertAlmostEqual(result[0]['depth_pct'],30)
        data=candles([100,90,100,85,100])
        base=catalogue(data,end='2021-12-31');strict=catalogue(data,end='2021-12-31',minimum=.12)
        self.assertTrue({e['episode_id'] for e in strict}<={e['episode_id'] for e in base})

    def test_price_split_units_do_not_create_extra_episode(self):
        a=candles([100,85,75,100,110,90])
        b=[replace(r,open=r.open/10,high=r.high/10,low=r.low/10,close=r.close/10) for r in a]
        x=catalogue(a,end='2021-12-31');y=catalogue(b,end='2021-12-31')
        self.assertEqual([e['onset_date'] for e in x],[e['onset_date'] for e in y])
        for r,s in zip(x,y):self.assertAlmostEqual(r['depth_pct'],s['depth_pct'])

    def test_causal_features_future_price_and_volume_prefix(self):
        prices=[100+i*.05+np.sin(i/7) for i in range(260)]
        stock,q,s,v=feature_pack(prices)
        before=build_features(stock,v,q,s)
        changed=list(stock);changed[250]=replace(changed[250],open=500,high=500,low=500,close=500)
        v2=dict(v);v2[stock[250].open_at.date().isoformat()]=999999
        after=build_features(changed,v2,q,s)
        self.assertEqual(before[:240],after[:240])
        self.assertTrue(all(r['confirmed_low_known_at'] is None or r['confirmed_low_known_at']<=r['decision_at'] for r in before))

    def test_confirmed_low_not_known_before_five_right_sessions(self):
        prices=[120]*21+[115,110,100,105,110,115,116,117,118,120]
        stock,q,s,v=feature_pack(prices)
        rows=build_features(stock,v,q,s)
        self.assertIsNone(rows[27]['prior_confirmed_low_date'])
        self.assertEqual(rows[28]['prior_confirmed_low_date'],stock[23].open_at.date().isoformat())

    def test_missing_benchmark_and_warmup_not_imputed(self):
        stock,q,s,v=feature_pack([100+i for i in range(50)])
        rows=build_features(stock,v,[],[])
        self.assertIsNone(rows[-1]['ma200']);self.assertIsNone(rows[-1]['return120'])
        self.assertIsNone(rows[-1]['relative_qqq20'])
        self.assertEqual(rows[-1]['market_regime'],'DATA_UNAVAILABLE')
        self.assertIsNone(hypotheses(rows[-1])['H4'])
        self.assertIsNone(hypotheses(rows[-1])['H5'])

    def test_future_yield_publication_excluded(self):
        stock,q,s,v=feature_pack([100+i for i in range(30)])
        rate=dict(yield_pct=9,observed_at='2021-01-01T20:00:00+00:00',available_at='2022-01-01T00:00:00+00:00')
        rows=build_features(stock,v,q,s,rates=[rate])
        self.assertTrue(all(r['yield10'] is None for r in rows))

    def test_sector_excludes_target_and_requires_five_peers(self):
        names=('AMD','NVDA','MU','AVGO','AMAT','LRCX')
        def item(s):return dict(symbol=s,date='2021-01-01',decision_at='2021-01-02T00:00:00+00:00',
            index=20,return20=-5,return10=-3,relative_qqq20=-4,qqq_return10=0)
        data={s:[item(s)] for s in names};sector_features(data)
        self.assertEqual(data['AMD'][0]['sector_peers'],5)
        self.assertEqual(data['AMD'][0]['sector_weak_fraction'],1)
        short={s:[item(s)] for s in names[:3]};sector_features(short)
        self.assertIsNone(short['AMD'][0]['sector_weak_fraction'])

    def test_future_labels_censored_and_not_terminal_only(self):
        data=candles([100,80,100,100])
        self.assertTrue(future_label(data,0,3)['target'])
        self.assertEqual(future_label(data,0,3)['terminal_return'],0)
        label=future_label(data,0,20)
        self.assertIsNone(label['target']);self.assertEqual(label['control_class'],'CENSORED')

    def test_chronological_training_purges_complete_horizon(self):
        cutoff='2023-01-01T00:00:00+00:00'
        training=[row(False),row(True),row(True,maturity='2023-01-02T00:00:00+00:00')]
        p,audit=fit_predict(training,[row()], 'joint_H1',cutoff)
        self.assertEqual(audit['training_n'],2)
        self.assertLessEqual(utc(audit['last_horizon_available']),utc(cutoff))
        self.assertTrue(0<p[0]<1)

    def test_future_labels_and_peak_metadata_cannot_change_prediction(self):
        train=[row(False),row(True),row(True,maturity='2024-01-01T00:00:00+00:00')]
        test=[row(),row(H1=True,rv20=50)]
        a,_=fit_predict(train,test,'joint_H1','2023-01-01T00:00:00+00:00')
        changed=[dict(r,eventual_trough=0,eventual_peak=10000,target=not r['target']) for r in test]
        train[-1]['target']=False
        b,_=fit_predict(train,changed,'joint_H1','2023-01-01T00:00:00+00:00')
        self.assertEqual(a,b)

    def test_standardization_fitted_on_training_not_test_batch(self):
        x=np.array([[0,10],[1,20],[2,30],[3,40]],float)
        m=RidgeLogit().fit(x,[0,0,1,1]);before=m.mean.copy()
        p=m.predict([[1,20]])[0];q=m.predict([[1,20],[999999,999999]])[0]
        self.assertAlmostEqual(p,q)
        self.assertTrue(np.array_equal(before,m.mean))
        with self.assertRaises(ValueError):m.fit(x,[1,0,1,0])

    def test_missing_hypothesis_not_false_prediction(self):
        train=[row(False),row(True)];test=[dict(row(),H5=None)]
        p,_=fit_predict(train,test,'joint_H5','2023-01-01T00:00:00+00:00')
        self.assertIsNone(p[0])
        self.assertIsNone(predictors(test[0],'joint_H5'))

    def test_sparse_grid_blocks_use_real_calendar_not_compressed_dates(self):
        start=datetime(2021,1,1)
        calendar=[(start+timedelta(days=i)).date().isoformat() for i in range(240)]
        rows=[{'date':calendar[i]} for i in range(0,240,20)]
        index,weights,N=sample_panel(rows,calendar,length=120,resamples=10)
        self.assertEqual(N,221)
        self.assertEqual(index[1]-index[0],20)
        self.assertTrue(np.all(weights.sum(axis=1)==N))

    def test_future_benchmark_publication_cannot_enter_features(self):
        stock,q,s,v=feature_pack([100+i*.1 for i in range(240)])
        q[205]=replace(q[205],available_at=q[230].available_at)
        r=build_features(stock,v,q,s)[205]
        self.assertIsNone(r['relative_qqq20'])
        self.assertEqual(r['market_regime'],'DATA_UNAVAILABLE')

    def test_inconsistent_future_yield_observation_not_used(self):
        stock,q,s,v=feature_pack([100+i for i in range(30)])
        rate=dict(yield_pct=9,observed_at='2022-01-01T20:00:00+00:00',available_at='2021-01-01T00:00:00+00:00')
        self.assertTrue(all(r['yield10'] is None for r in build_features(stock,v,q,s,rates=[rate])))

    def test_impossible_maturity_before_anchor_rejected(self):
        bad=row(True,maturity='2022-11-01T00:00:00+00:00')
        with self.assertRaises(ValueError):fit_predict([bad],[row()],'historical','2023-01-01T00:00:00+00:00')

    def test_actual_control_filters_and_reuse_audited(self):
        root=Path('reports/historical-drawdown-anatomy')
        snapshots={(r['episode_id'],r['offset']):r for r in csv.DictReader((root/'pre-drawdown-features.csv').open())}
        controls=list(csv.DictReader((root/'control-periods.csv').open()))
        self.assertTrue(any(r['match_status']=='NO_MATCH' for r in controls))
        self.assertTrue(any(r['match_status']=='MATCHED' and int(r['reuse_count'])>1 for r in controls))
        for r in controls:
            if r['match_status']!='MATCHED':continue
            s=snapshots[(r['episode_id'],r['offset'])]
            self.assertEqual(r['symbol'],s['symbol']);self.assertEqual(r['market_regime'],s['market_regime'])
            self.assertEqual((int(r['date'][:4])-2021)//2,(int(s['date'][:4])-2021)//2)
            self.assertGreater(abs(int(r['index'])-int(s['index'])),20)
            if r['date']<'2023-01-01':self.assertLessEqual(utc(r['label_available_at']),utc('2023-01-01T00:00:00+00:00'))
            self.assertAlmostEqual(float(r['inverse_reuse_weight']),1/int(r['reuse_count']))

    def test_future_path_decline_differs_from_anchor_loss_without_feature_leak(self):
        data=candles([100,120,108,110])
        label=future_label(data,0,3)
        self.assertFalse(label['target'])
        self.assertTrue(label['path_target'])
        self.assertAlmostEqual(label['path_drawdown_pct'],10)
        self.assertIsNone(future_label(data,0,20)['path_target'])

    def test_missing_branch_and_nonfinite_volume_remain_unknown(self):
        r={'relative_qqq20':0,'qqq_return20':1}
        self.assertIsNone(hypotheses(r)['H2'])
        r['relative_qqq20']=-6
        self.assertTrue(hypotheses(r)['H2'])
        stock,q,s,v=feature_pack([100+i for i in range(30)])
        v[stock[-1].open_at.date().isoformat()]=float('nan')
        last=build_features(stock,v,q,s)[-1]
        self.assertIsNone(last['volume']);self.assertIsNone(last['volume_ratio'])

    def test_actual_catalogue_nonoverlap_and_snapshots_before_onset(self):
        root=Path('reports/historical-drawdown-anatomy')
        events=list(csv.DictReader((root/'drawdown-catalog.csv').open()))
        for symbol in {e['symbol'] for e in events}:
            rows=sorted([e for e in events if e['symbol']==symbol],key=lambda e:e['onset_date'])
            for a,b in zip(rows,rows[1:]):self.assertLess(a['event_end'],b['onset_date'])
            for e in rows:
                if e['status']=='OPEN_AT_CUTOFF':self.assertEqual(e['recovery_date'],'')
        for r in csv.DictReader((root/'pre-drawdown-features.csv').open()):
            if r['status']=='OBSERVED_CAUSAL_SNAPSHOT':
                self.assertLess(r['date'],r['event_onset'])
                if r['confirmed_low_known_at']:self.assertLessEqual(r['confirmed_low_known_at'],r['decision_at'])

    def test_actual_training_and_unavailable_fundamentals(self):
        root=Path('reports/historical-drawdown-anatomy')
        for name in ('fit-audit.csv','path-fit-audit.csv'):
            for r in csv.DictReader((root/name).open()):
                if r['last_horizon_available']:self.assertLessEqual(utc(r['last_horizon_available']),utc(r['cutoff']))
                if r['last_anchor']:self.assertLess(utc(r['last_anchor']),utc(r['cutoff']))
        rows=list(csv.DictReader((root/'hypothesis-comparison.csv').open()))
        self.assertTrue(all(r['status']=='DATA_UNAVAILABLE' for r in rows if r['hypothesis']=='H4'))
        old=json.loads(Path('reports/risk-signal-v3/run.json').read_text())
        for name,h in old['source_sha256'].items():self.assertEqual(hashlib.sha256(Path(name).read_bytes()).hexdigest(),h)


if __name__=='__main__':unittest.main()
