import csv
import hashlib
import json
import unittest
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from pathlib import Path
from aae.backtest.simulator import Bar
from aae.backtest.ladder import LadderConfig,LadderState,Split,simulate_ladder,metrics,recovery_costs
from aae.backtest.ladder_research import select_episodes

BASE=datetime(2021,1,1,tzinfo=timezone.utc)
CFG=LadderConfig(capital=10000,commission_bps=0,slippage_bps=0)


def bars(prices,opens=None):
    opens=opens or prices
    return [Bar('AMD',BASE+timedelta(days=i,hours=14),BASE+timedelta(days=i,hours=20),
                BASE+timedelta(days=i,hours=21),o,max(o,p)+1,min(o,p)-1,p,'synthetic test')
            for i,(o,p) in enumerate(zip(opens,prices))]


def run(prices,opens=None,**kwargs):
    return simulate_ladder(bars(prices,opens),kwargs.pop('config',CFG),**kwargs)


class LadderTests(unittest.TestCase):
    def test_sequential_decline_stops_at_core(self):
        result=run([100*.97**i for i in range(60)])
        self.assertEqual(sum(t['side']=='SELL' for t in result['trades']),10)
        self.assertAlmostEqual(result['state'].shares,50)
        self.assertTrue(all(r['share_fraction']>=.5-1e-10 for r in result['daily']))

    def test_growth_after_reduction_queues_buy(self):
        result=run([100,97,95,100],[100,97,90,100])
        self.assertTrue(any(t['side']=='BUY' and t['reason']=='ladder' for t in result['trades']))

    def test_return_to_full_shares_and_upper_limit(self):
        result=run([97,95,80,200],[100,90,80,200])
        self.assertAlmostEqual(result['state'].shares,100)
        self.assertEqual(len(result['trades']),3)
        self.assertEqual(result['events'][-1]['event'],'UPPER_BOUND_ANCHOR_FROZEN')

    def test_decline_bounce_decline_alternates(self):
        result=run([97,95,78,77,80],[100,90,80,77,70])
        self.assertEqual([t['side'] for t in result['trades'][:4]],['BUY','SELL','BUY','SELL'])

    def test_small_oscillations_do_not_trade(self):
        result=run([100,101,99,101,99,100])
        self.assertEqual(len(result['trades']),1)
        self.assertEqual(result['state'].anchor,100)

    def test_lower_bound_reference_does_not_follow_trough(self):
        result=run([100*.97**i for i in range(60)])
        anchor=result['state'].anchor
        self.assertGreater(anchor,result['daily'][-1]['close']*2)
        self.assertEqual(result['events'][-1]['event'],'LOWER_BOUND_ANCHOR_FROZEN')

    def test_fully_invested_reference_does_not_follow_high(self):
        result=run([100,150,140,110])
        self.assertEqual(result['state'].anchor,100)
        self.assertEqual(len(result['trades']),1)

    def test_gap_crossing_many_levels_fills_only_one_step(self):
        result=run([90,50],[100,50])
        self.assertEqual(len(result['trades']),2)
        self.assertEqual(result['trades'][-1]['units'],5)
        self.assertEqual(result['trades'][-1]['fill_price'],50)
        self.assertEqual(result['state'].shares,95)

    def test_no_cash_blocks_buy_and_freezes_reference(self):
        state=LadderState(0,90,100,50,last_close_at=BASE-timedelta(days=1))
        result=run([100],state=state)
        self.assertEqual(len(result['trades']),0)
        self.assertEqual(result['events'][-1]['event'],'BUY_BLOCKED_NO_CASH_ANCHOR_FROZEN')
        self.assertEqual(result['state'].anchor,50)

    def test_cash_cap_partial_fill_never_borrows(self):
        state=LadderState(10,90,100,50,last_close_at=BASE-timedelta(days=1))
        result=run([100,100],state=state)
        self.assertAlmostEqual(result['trades'][0]['units'],.1)
        self.assertEqual(result['state'].cash,0)
        self.assertEqual(result['trades'][0]['fill_status'],'PARTIAL_REMAINDER_CANCELLED')

    def test_unaffordable_whole_order_can_be_rejected(self):
        state=LadderState(10,90,100,50,last_close_at=BASE-timedelta(days=1))
        result=run([100,100],state=state,config=replace(CFG,partial_cash=False))
        self.assertFalse(result['trades'])
        self.assertEqual(result['state'].anchor,50)

    def test_future_open_cannot_set_signal_reference(self):
        a=run([90,50],[100,50]); b=run([90,30],[100,30])
        self.assertEqual(a['daily'][0],b['daily'][0])
        self.assertEqual(a['daily'][0]['anchor'],100)
        self.assertEqual(a['daily'][1]['anchor'],50)

    def test_future_closes_do_not_change_prefix(self):
        a=run([100,97,95,80]); b=run([100,97,95,150])
        self.assertEqual(a['daily'][:3],b['daily'][:3])

    def test_signal_not_executed_before_publication(self):
        data=bars([90,90,90],[100,90,90])
        data[0]=replace(data[0],available_at=BASE+timedelta(days=1,hours=15))
        # The daily adapter refuses this unsupported timing rather than valuing a
        # prior close with holdings changed at an intervening open.
        with self.assertRaises(ValueError):
            simulate_ladder(data,CFG)

    def test_two_session_latency_and_single_pending_order(self):
        result=run([90,80,70,60,50],[100,80,70,60,50],config=replace(CFG,delay_sessions=2))
        self.assertEqual(result['trades'][1]['executed_at'],bars([90,80,70,60,50])[2].open_at.isoformat())
        self.assertTrue(any(e['event']=='PENDING_NO_NEW_ORDER' for e in result['events']))

    def test_fees_slippage_and_cash_conservation(self):
        cfg=replace(CFG,commission_bps=5,slippage_bps=5)
        result=run([90,90],opens=[100,90],config=cfg)
        first=result['trades'][0]
        self.assertAlmostEqual(first['fill_price'],100.05)
        self.assertAlmostEqual(first['units'],10000/(100.05*1.0005))
        sale=result['trades'][1]
        self.assertAlmostEqual(sale['fill_price'],89.955)
        self.assertAlmostEqual(sale['commission'],sale['units']*sale['fill_price']*.0005)
        self.assertAlmostEqual(result['state'].cash,sale['notional']-sale['commission'])

    def test_state_survives_episode_boundary(self):
        data=bars([100,97,94,91,95,100,105])
        full=simulate_ladder(data,CFG)
        first=simulate_ladder(data[:2],CFG)
        second=simulate_ladder(data[2:],CFG,state=first['state'])
        self.assertEqual(full['daily'],first['daily']+second['daily'])
        self.assertEqual(full['trades'],first['trades']+second['trades'])
        self.assertEqual(full['state'],second['state'])

    def test_no_duplicate_execution_of_signal(self):
        result=run([100*.97**i for i in range(40)])
        ids=[t['order_id'] for t in result['trades']]
        self.assertEqual(len(ids),len(set(ids)))
        self.assertEqual(len({t['executed_at'] for t in result['trades']}),len(ids))

    def test_known_split_adjusts_units_reference_and_nav(self):
        data=bars([100,50,50])
        action=Split(data[1].open_at,data[1].open_at,2)
        result=simulate_ladder(data,CFG,splits=[action])
        self.assertEqual(result['state'].shares,200)
        self.assertEqual(result['state'].base_shares,200)
        self.assertEqual(result['state'].anchor,50)
        self.assertTrue(all(r['equity']==10000 for r in result['daily']))
        self.assertEqual(len(result['trades']),1)

    def test_split_adjusts_pending_order(self):
        data=bars([90,45],[100,45])
        action=Split(data[1].open_at,data[1].open_at,2)
        result=simulate_ladder(data,CFG,splits=[action])
        self.assertEqual(result['trades'][1]['units'],10)
        self.assertAlmostEqual(result['state'].shares,190)

    def test_split_cannot_be_known_after_its_effective_open(self):
        with self.assertRaises(ValueError):
            Split(BASE,BASE+timedelta(days=1),2)

    def test_nav_is_cash_plus_market_value(self):
        result=run([100,97,94,105,95,80,120])
        for row in result['daily']:
            self.assertAlmostEqual(row['equity'],row['cash']+row['shares']*row['close'])

    def test_partial_fill_cancels_remainder_and_updates_anchor(self):
        result=run([90,90],[100,90],config=replace(CFG,fill_fraction=.5))
        self.assertEqual(result['trades'][1]['units'],2.5)
        self.assertEqual(result['state'].anchor,90)
        self.assertIsNone(result['state'].pending)

    def test_whole_lot_rounding_does_not_break_floor(self):
        result=run([100*.97**i for i in range(60)],config=replace(CFG,lot_size=1,capital=10050))
        self.assertTrue(all(abs(t['units']-round(t['units']))<1e-9 for t in result['trades']))
        self.assertGreaterEqual(result['state'].shares,result['state'].base_shares*.5-1e-10)

    def test_short_period_cagr_and_flat_sharpe_are_blank(self):
        result=run([100]*10,ladder=False)
        m=metrics(result['daily'],result['trades'],10000,bars([100]*10)[0].open_at)
        self.assertIsNone(m['cagr_pct']); self.assertIsNone(m['sharpe_rf_zero']); self.assertIsNone(m['sortino_rf_zero'])

    def test_drawdown_duration(self):
        result=run([100,90,80,100],ladder=False)
        m=metrics(result['daily'],result['trades'],10000,bars([100]*4)[0].open_at)
        self.assertEqual(m['max_drawdown_duration_sessions'],2)
        self.assertAlmostEqual(m['max_drawdown_pct'],-20)

    def test_terminal_order_is_pending_not_backfilled(self):
        result=run([100,90])
        self.assertEqual(len(result['trades']),1)
        self.assertIsNotNone(result['state'].pending)

    def test_invalid_parameters_fail_closed(self):
        for kwargs in ({'sell_step':0},{'capital':-1},{'min_fraction':1},{'lot_size':0},{'delay_sessions':0}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):
                LadderConfig(**kwargs)

    def test_split_normalized_fifo_cost_is_consistent(self):
        trades=[dict(side='SELL',units=10,fill_price=100,commission=0,base_shares=100,order_id=1,reason='ladder'),
                dict(side='BUY',units=20,fill_price=60,commission=0,base_shares=200,order_id=2,reason='ladder')]
        cost=recovery_costs(trades,70,terminal_base=200)
        self.assertAlmostEqual(cost['missed_recovery_dollars'],200)
        self.assertEqual(cost['unreacquired_units'],0)

    def test_duplicate_split_event_rejected(self):
        data=bars([100,50]); split=Split(data[1].open_at,data[1].open_at,2)
        with self.assertRaises(ValueError):
            simulate_ladder(data,CFG,splits=[split,split])

    def test_recovery_after_real_loss_not_first_profitable_mark(self):
        result=run([105,90,80,100,110],[100,90,80,100,110],ladder=False)
        m=metrics(result['daily'],result['trades'],10000,bars([100]*5)[0].open_at)
        self.assertEqual(m['initial_capital_recovery_date'],'2021-01-01')
        self.assertEqual(m['initial_capital_recovery_after_loss_date'],'2021-01-04')
        self.assertEqual(m['initial_capital_recovery_after_loss_sessions'],2)

    def test_cash_and_position_journal_conserves_capital(self):
        rows=list(csv.DictReader(open('reports/core-tactical-ladder/position-history.csv')))
        self.assertTrue(rows)
        for r in rows:
            self.assertAlmostEqual(float(r['equity']),float(r['cash'])+float(r['shares'])*float(r['close']),places=6)
            self.assertGreaterEqual(float(r['shares'])+1e-7,float(r['core_shares']))
            self.assertLessEqual(float(r['shares']),float(r['base_shares'])+1e-7)
            self.assertGreaterEqual(float(r['cash']),0)

    def test_complete_grid_and_baseline_are_preserved(self):
        rows=list(csv.DictReader(open('reports/core-tactical-ladder/sensitivity.csv')))
        for window in ('full','development','validation_carry','validation_independent'):
            selected=[r for r in rows if r['family']=='parameters' and r['window']==window]
            self.assertEqual(len(selected),144)
        self.assertEqual(sum(r['family']=='execution' for r in rows),48)
        self.assertEqual(sum(r['family']=='rounding_partial' for r in rows),5)
        control=next(r for r in csv.DictReader(open('reports/core-tactical-ladder/summary.csv')) if r['scenario']=='ladder_base_continuous')
        selected=next(r for r in rows if r['family']=='parameters' and r['window']=='full'
            and float(r['sell_step'])==.02 and float(r['buy_step'])==.02
            and float(r['trade_fraction'])==.05 and float(r['min_fraction'])==.5)
        self.assertAlmostEqual(float(control['final_equity']),float(selected['final_equity']))

    def test_all_journal_orders_execute_once_and_after_signal(self):
        seen=set(); sessions=set()
        for trade in csv.DictReader(open('reports/core-tactical-ladder/trades.csv')):
            key=(trade['scenario'],trade['order_id'])
            session=(trade['scenario'],trade['executed_at'])
            self.assertNotIn(key,seen); seen.add(key)
            self.assertNotIn(session,sessions); sessions.add(session)
            if trade['signal_at']:
                self.assertGreater(trade['executed_at'],trade['signal_at'])

    def test_actual_cycles_and_regimes_meet_prespecified_coverage(self):
        from aae.backtest.ladder_research import load_data
        data,manifest=load_data()
        self.assertEqual(manifest['rows'],1458)
        self.assertEqual(data[-1].close_at.date().isoformat(),'2026-10-22')
        episodes=select_episodes(data)
        self.assertGreaterEqual(sum(e['selection']=='all_peak_to_recovery_10pct' for e in episodes),4)
        regimes={e['regime'] for e in episodes}
        self.assertTrue({'strong_growth','deep_decline_recovery','prolonged_correction','sideways_oscillation'}<=regimes)

    def test_actual_continuous_episodes_inherit_account_state(self):
        positions=list(csv.DictReader(open('reports/core-tactical-ladder/position-history.csv')))
        histories={strategy:[r for r in positions if r['scenario']==strategy+'_continuous'] for strategy in ('buy_hold','ladder_base')}
        for row in csv.DictReader(open('reports/core-tactical-ladder/episodes.csv')):
            if row['method']!='continuous':
                continue
            source=histories['buy_hold' if row['strategy']=='buy_hold' else 'ladder_base']
            index=next(i for i,r in enumerate(source) if r['date']==row['start'])
            if index:
                previous=source[index-1]
                self.assertAlmostEqual(float(row['inherited_cash']),float(previous['cash']))
                self.assertAlmostEqual(float(row['inherited_shares']),float(previous['shares']))
                self.assertAlmostEqual(float(row['inherited_anchor']),float(previous['anchor']))
                self.assertAlmostEqual(float(row['initial_equity']),float(previous['equity']))

    def test_original_engines_and_executor_unchanged(self):
        sources=json.loads(Path('reports/risk-backtest-v1/run.json').read_text())['source_sha256']
        for suffix in ('aae/engines/decision_engine.py','aae/engines/tactical_risk_overlay.py','aae/backtest/simulator.py'):
            digest=next(h for name,h in sources.items() if name.endswith(suffix))
            self.assertEqual(hashlib.sha256(Path(suffix).read_bytes()).hexdigest(),digest)

    def test_chunk_boundary_cannot_bypass_publication_guard(self):
        data=bars([90,90,90],[100,90,90])
        data[0]=replace(data[0],available_at=BASE+timedelta(days=1,hours=15))
        first=simulate_ladder(data[:1],CFG)
        with self.assertRaises(ValueError):
            simulate_ladder(data[1:],CFG,state=first['state'])

    def test_cash_impact_exactly_decomposes_relative_nav(self):
        for row in csv.DictReader(open('reports/core-tactical-ladder/cash-impact.csv')):
            self.assertAlmostEqual(float(row['equity_delta_dollars']),
                float(row['cash_delta_dollars'])+float(row['share_market_value_delta_dollars']),places=6)

    def test_continuous_window_retains_prior_fifo_costs(self):
        row=next(r for r in csv.DictReader(open('reports/core-tactical-ladder/episodes.csv'))
                 if r['episode']=='Sep_Oct_2026_diagnostic' and r['method']=='continuous' and r['strategy']=='ladder')
        self.assertGreater(float(row['inherited_missed_recovery_at_start']),0)
        self.assertAlmostEqual(float(row['inherited_missed_recovery_change']),
            float(row['inherited_missed_recovery_at_end'])-float(row['inherited_missed_recovery_at_start']))

    def test_cycle_selection_uses_all_completed_cycles(self):
        data=bars([100,80,100,110,90,110,100])
        cycles=[r for r in select_episodes(data) if r['selection']=='all_peak_to_recovery_10pct']
        self.assertEqual(len(cycles),2)


if __name__=='__main__':
    unittest.main()
