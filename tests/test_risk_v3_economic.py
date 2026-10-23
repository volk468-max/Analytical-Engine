import hashlib
import json
import unittest
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from pathlib import Path
from aae.backtest.simulator import Bar,ExecutionConfig
from aae.research.risk_v3_economic import EconomicConfig,simulate,performance
from aae.research.risk_v3_economic_analysis import next_trough,signal_economics,economic_metrics


def fixture(prices,levels=None):
    first=datetime(2026,1,1,14,30,tzinfo=timezone.utc)
    bars=[];signals=[]
    for i,p in enumerate(prices):
        opened=first+timedelta(days=i)
        closed=opened+timedelta(hours=6,minutes=30)
        available=opened.replace(hour=0,minute=0)+timedelta(days=1)
        bars.append(Bar('AMD',opened,closed,available,p,p*1.01,p*.99,p,'synthetic unit-test fixture only',False))
        signals.append(dict(symbol='AMD',date=opened.date().isoformat(),decision_at=available.isoformat(),
            data_status='OK',risk_level=(levels or ['HOLD']*len(prices))[i],
            indicators={'close':p,'ma20':p*.95,'ma20_slope_5_pct':1}))
    return bars,signals


def cfg(**changes):
    execution=changes.pop('execution',ExecutionConfig(initial_cash=100000,commission_bps=0,slippage_bps=0))
    return EconomicConfig(execution=execution,**changes)


def run(prices,levels=None,config=None,**kwargs):
    bars,signals=fixture(prices,levels)
    return simulate(bars,signals,'2026-01-01','2026-12-31',config or cfg(),**kwargs)


class EconomicTests(unittest.TestCase):
    def test_next_open_only_and_actual_gap_price(self):
        r=run([100,90,70,80],['HOLD','REDUCE','REDUCE','WATCH'])
        sale=r['trades'][1]
        self.assertEqual(sale['date'],'2026-01-03')
        self.assertEqual(sale['fill'],70)
        self.assertGreater(sale['executed_at'],sale['signal_at'])

    def test_no_repeated_sales_unchanged_reduce(self):
        r=run([100]*20,['REDUCE']*20)
        self.assertEqual(len(r['lots']),1)
        self.assertAlmostEqual(r['daily'][-1]['shares_fraction'],.9)

    def test_reduce_to_critical_once(self):
        r=run([100]*7,['REDUCE','REDUCE','CRITICAL','REDUCE','CRITICAL','CRITICAL','HOLD'])
        self.assertEqual(len(r['lots']),2)
        self.assertAlmostEqual(r['daily'][-1]['shares_fraction'],.8)

    def test_direct_critical_combines_order_and_control_is_single(self):
        r=run([100]*3,['CRITICAL']*3)
        self.assertEqual(len(r['lots']),2)
        self.assertEqual(len(r['trades']),2)
        control=run([100]*3,['CRITICAL']*3,cfg(critical_extra=False))
        self.assertEqual(len(control['lots']),1)

    def test_short_low_chatter_cannot_rearm(self):
        r=run([100]*7,['REDUCE','WATCH','REDUCE','HOLD','WATCH','REDUCE','REDUCE'])
        self.assertEqual(len(r['lots']),1)

    def test_rearm_and_fifty_percent_floor(self):
        levels=(['CRITICAL','WATCH','WATCH','WATCH']*10)+['CRITICAL']
        r=run([100]*len(levels),levels,cfg(tranche=.25,recovery='TIME10'))
        self.assertAlmostEqual(min(d['shares_fraction'] for d in r['daily']),.5)
        self.assertTrue(any(d['status']=='SHARE_FLOOR' for d in r['decisions']))

    def test_hold3_restores_one_tranche_per_open(self):
        r=run([100]*9,['REDUCE','CRITICAL','HOLD','HOLD','HOLD','HOLD','HOLD','HOLD','HOLD'])
        buys=[t for t in r['trades'] if t['reason'].startswith('RECOVER')]
        self.assertEqual(buys[0]['signal_date'],'2026-01-05')
        self.assertEqual(buys[0]['date'],'2026-01-06')
        self.assertEqual(len(buys),2)
        self.assertAlmostEqual(r['daily'][-1]['shares_fraction'],1)

    def test_trend3_requires_all_three_trend_confirmations(self):
        bars,signals=fixture([100]*10,['REDUCE']+['WATCH']*9)
        signals[3]['indicators']['ma20_slope_5_pct']=-1
        r=simulate(bars,signals,'2026-01-01','2026-12-31',cfg(recovery='TREND3'))
        self.assertEqual(r['trades'][2]['signal_date'],'2026-01-07')

    def test_time10_waits_ten_valid_low_observations(self):
        r=run([100]*13,['REDUCE']+['WATCH']*12,cfg(recovery='TIME10'))
        self.assertEqual(r['trades'][2]['signal_date'],'2026-01-11')
        self.assertEqual(r['trades'][2]['date'],'2026-01-12')

    def test_cash_limited_recovery_no_injection(self):
        r=run([100,100,150,150,150,150,150],['REDUCE','HOLD','HOLD','HOLD','HOLD','HOLD','HOLD'])
        last=r['daily'][-1]
        self.assertGreater(last['share_deficit'],0)
        self.assertAlmostEqual(last['cash'],0)
        self.assertLess(last['shares_fraction'],1)
        self.assertTrue(all(d['cash']>=0 for d in r['daily']))
        self.assertFalse(signal_economics(r)[0]['cycle_completed'])

    def test_fees_and_adverse_slippage_exact(self):
        ex=ExecutionConfig(initial_cash=100000,commission_bps=5,slippage_bps=5)
        r=run([100]*4,['REDUCE']*4,cfg(execution=ex))
        initial,sale=r['trades']
        self.assertAlmostEqual(initial['fill'],100.05)
        self.assertAlmostEqual(initial['quantity'],100000/(100.05*1.0005))
        self.assertAlmostEqual(sale['fill'],99.95)
        self.assertAlmostEqual(sale['commission'],sale['quantity']*99.95*.0005)
        self.assertAlmostEqual(sale['cash'],sale['quantity']*99.95*.9995)

    def test_delays_one_two_additional_sessions(self):
        for delay in (1,2,3):
            ex=ExecutionConfig(initial_cash=100000,delay_sessions=delay)
            r=run([100]*8,['HOLD','REDUCE']+['REDUCE']*6,cfg(execution=ex))
            self.assertEqual(r['trades'][1]['date'],f'2026-01-0{2+delay}')

    def test_queued_buy_cancelled_by_new_risk(self):
        ex=ExecutionConfig(initial_cash=100000,commission_bps=0,slippage_bps=0,delay_sessions=3)
        levels=['REDUCE','HOLD','HOLD','HOLD','REDUCE','REDUCE','REDUCE','REDUCE','REDUCE']
        r=run([100]*len(levels),levels,cfg(execution=ex))
        self.assertTrue(r['cancellations'])
        self.assertFalse(any(t['reason'].startswith('RECOVER') for t in r['trades']))
        self.assertEqual(len({t['order_id'] for t in r['trades']}),len(r['trades']))

    def test_missing_data_does_not_restore_or_rearm(self):
        bars,signals=fixture([100]*8,['REDUCE','HOLD','HOLD','HOLD','REDUCE','REDUCE','HOLD','HOLD'])
        signals[2].update(data_status='STALE',risk_level=None)
        r=simulate(bars,signals,'2026-01-01','2026-12-31',cfg())
        self.assertEqual(len(r['lots']),1)
        self.assertFalse(r['matches'])

    def test_open_cycle_and_last_day_order_not_backfilled(self):
        r=run([100,80],['HOLD','REDUCE'])
        self.assertEqual(len(r['trades']),1)
        self.assertEqual(r['decisions'][-1]['status'],'UNFILLED_AT_CUTOFF')
        open_cycle=run([100,90,80],['REDUCE']*3)
        row=signal_economics(open_cycle)[0]
        self.assertFalse(row['cycle_completed'])
        self.assertIsNone(row['full_lot_recovery_date'])
        self.assertTrue(row['trough_censored'])

    def test_no_lookahead_future_price_and_signal_prefix(self):
        bars,signals=fixture([100,90,80,85,110,120,130],['HOLD','REDUCE','WATCH','HOLD','HOLD','HOLD','HOLD'])
        a=simulate(bars,signals,'2026-01-01','2026-01-05',cfg())
        changed=list(bars);changed[6]=replace(changed[6],open=50,high=60,low=40,close=50)
        signals[6]['risk_level']='CRITICAL'
        b=simulate(changed,signals,'2026-01-01','2026-01-05',cfg())
        self.assertEqual(a['daily'],b['daily']);self.assertEqual(a['trades'],b['trades'])
        extended=simulate(changed,signals,'2026-01-01','2026-01-07',cfg())
        self.assertEqual(a['daily'],extended['daily'][:5])

    def test_no_execution_with_future_or_prepublished_signal(self):
        bars,signals=fixture([100]*5,['REDUCE']*5)
        signals[0]['decision_at']=bars[0].open_at.isoformat()
        with self.assertRaises(ValueError):simulate(bars,signals,'2026-01-01','2026-12-31',cfg())
        signals[0]['decision_at']=bars[2].available_at.isoformat()
        with self.assertRaises(ValueError):simulate(bars,signals,'2026-01-01','2026-12-31',cfg())

    def test_local_trough_only_evaluation_and_requires_confirmation(self):
        bars,_=fixture([100,90,80,85,70,75])
        self.assertEqual(next_trough(bars,1),(2,False,3))
        self.assertEqual(next_trough(bars[:3],1),(2,True,None))
        # Closing trough cannot be chosen based on a still-later lower low.
        self.assertEqual(next_trough(bars,1)[0],2)

    def test_dividend_receivable_not_available_for_buying(self):
        r=run([100,100,150,150,150,150],['REDUCE','HOLD','HOLD','HOLD','HOLD','HOLD'],dividends={'2026-01-03':10})
        self.assertGreater(r['daily'][-1]['dividend_receivable'],0)
        self.assertGreater(r['daily'][-1]['share_deficit'],0)
        self.assertAlmostEqual(r['daily'][-1]['cash'],0)
        base=run([100,100,150,150,150,150],buy_hold=True,dividends={'2026-01-03':10})
        economic_metrics(r,base)  # includes lost dividends in exact reconciliation

    def test_entitlement_precedes_ex_date_open_trade(self):
        r=run([100]*4,['REDUCE']*4,dividends={'2026-01-02':1})
        self.assertAlmostEqual(r['daily'][1]['dividend_receivable'],r['original_shares'])
        self.assertEqual(r['lots'][0]['missed_dividends'],0)

    def test_split_basis_scaling_keeps_nav_and_economics(self):
        prices=[100,95,80,85,110,120,100,90]
        levels=['REDUCE','CRITICAL','WATCH','HOLD','HOLD','HOLD','REDUCE','WATCH']
        a=run(prices,levels);b=run([p/10 for p in prices],levels)
        for x,y in zip(a['daily'],b['daily']):self.assertAlmostEqual(x['equity'],y['equity'])
        self.assertAlmostEqual(b['original_shares'],a['original_shares']*10)

    def test_nav_and_attribution_reconcile_with_multiple_lots(self):
        prices=[100,95,80,85,110,120,100,90,80,100,110]
        levels=['REDUCE','CRITICAL','HOLD','HOLD','HOLD','REDUCE','HOLD','HOLD','HOLD','HOLD','HOLD']
        r=run(prices,levels,cfg(execution=ExecutionConfig(initial_cash=100000)),dividends={'2026-01-04':.1})
        base=run(prices,levels,cfg(execution=ExecutionConfig(initial_cash=100000)),buy_hold=True,dividends={'2026-01-04':.1})
        for d in r['daily']:
            self.assertAlmostEqual(d['equity'],d['cash']+d['dividend_receivable']+d['shares']*d['close'])
        m=economic_metrics(r,base)
        self.assertAlmostEqual(m['equity_difference_vs_buy_hold'],m['attributed_difference'])

    def test_constant_price_roundtrip_loses_exact_trading_costs(self):
        levels=['REDUCE']+['HOLD']*8
        r=run([100]*9,levels,cfg(execution=ExecutionConfig(initial_cash=100000)))
        base=run([100]*9,levels,cfg(execution=ExecutionConfig(initial_cash=100000)),buy_hold=True)
        delta=economic_metrics(r,base)['equity_difference_vs_buy_hold']
        additional=sum(t['commission']+t['slippage'] for t in r['trades'][1:])
        self.assertAlmostEqual(delta,-additional)

    def test_completed_reduce_signal_counts_direct_critical_once(self):
        levels=['CRITICAL']+['HOLD']*10
        r=run([100]*len(levels),levels)
        base=run([100]*len(levels),levels,buy_hold=True)
        m=economic_metrics(r,base)
        self.assertEqual(m['completed_lots'],2)
        self.assertEqual(m['completed_reduce_signals'],1)
        self.assertEqual(m['profitable_completed_reduce_signal_pct'],0)

    def test_pending_sell_escalation_conflict_is_explicit(self):
        levels=['REDUCE','CRITICAL','CRITICAL','CRITICAL','CRITICAL','CRITICAL']
        ex=ExecutionConfig(initial_cash=100000,delay_sessions=3)
        r=run([100]*len(levels),levels,cfg(execution=ex))
        self.assertEqual(len(r['lots']),1)
        self.assertEqual(r['decisions'][1]['status'],'PENDING_ORDER_CONFLICT')
        self.assertEqual(len(r['trades']),2)

    def test_trough_protection_accounts_for_early_repurchases(self):
        prices=[100,100,90,80,70,60,50,55]
        levels=['REDUCE']+['HOLD']*7
        r=run(prices,levels)
        row=signal_economics(r)[0]
        self.assertLess(row['actual_contribution_at_trough_usd'],row['maximum_avoidable_decline_usd'])
        self.assertTrue(row['cycle_completed'])
        self.assertEqual(row['next_local_min_date'],'2026-01-07')

    def test_exported_primary_nav_and_costs(self):
        import csv
        root=Path('reports/risk-v3-economic')
        for row in csv.DictReader((root/'daily-equity.csv').open()):
            self.assertAlmostEqual(float(row['equity']),float(row['total_cash'])+float(row['shares'])*float(row['close']),places=6)
            self.assertGreaterEqual(float(row['cash']),-1e-7)
            self.assertGreaterEqual(float(row['shares_fraction']),.5-1e-8)
            self.assertLessEqual(float(row['shares_fraction']),1+1e-8)
        rows=list(csv.DictReader((root/'summary.csv').open()))
        principal=[r for r in rows if r['account_mode']=='independent' and r['period']=='2023-2026' and r['scenario']!='BUY_HOLD']
        self.assertEqual(len(principal),18)
        for row in principal:
            self.assertAlmostEqual(float(row['equity_difference_vs_buy_hold']),float(row['attributed_difference']),places=6)
        with (root/'trades.csv').open() as stream:
            for row in csv.DictReader(stream):
                if row['reason']!='INITIAL':self.assertGreater(row['executed_at'],row['signal_at'])
                self.assertAlmostEqual(float(row['commission']),float(row['quantity'])*float(row['fill'])*.0005,places=6)

    def test_subperiod_forward_labels_censor_at_account_end(self):
        from aae.research.risk_v3_economic_study import outcome_labels
        bars,signals=fixture(list(range(100,130)),['HOLD']+['REDUCE']*29)
        complete=outcome_labels({'AMD':signals},'2026-01-01','2026-01-30')
        censored=outcome_labels({'AMD':signals},'2026-01-01','2026-01-10')
        self.assertTrue(complete[('AMD','2026-01-02')]['false_reduce_followed_by_growth'])
        self.assertIsNone(censored[('AMD','2026-01-02')]['false_reduce_followed_by_growth'])
        self.assertIsNone(censored[('AMD','2026-01-02')]['forward_20_pct'])

    def test_original_v3_code_and_signals_unchanged(self):
        m=json.loads(Path('reports/risk-signal-v3/run.json').read_text())
        for name,h in m['source_sha256'].items():
            self.assertEqual(hashlib.sha256(Path(name).read_bytes()).hexdigest(),h)
        file=Path('reports/risk-signal-v3/daily-signals.jsonl.gz')
        self.assertEqual(hashlib.sha256(file.read_bytes()).hexdigest(),m['output_sha256'][file.name])


if __name__=='__main__':unittest.main()
