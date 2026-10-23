"""Synthetic numerical/causality tests; report integration tests use downloaded data."""
import csv
import hashlib
import json
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from aae.backtest.simulator import Bar, Observation
from aae.backtest.diagnostics import (features, drawdown_events, indicator_evaluation,
    fifo_recovery_costs, recovery_analysis)

BASE=datetime(2025,1,1,tzinfo=timezone.utc)


def candles(prices, symbol='TEST'):
    return [Bar(symbol,BASE+timedelta(days=i,hours=14),BASE+timedelta(days=i,hours=20),
                BASE+timedelta(days=i,hours=21),p,p+1,p-1,p,'synthetic test only') for i,p in enumerate(prices)]


def markets(data, value=16):
    return [Observation(b.close_at,b.available_at,{'vix':value},'synthetic market') for b in data]


class DiagnosticsTests(unittest.TestCase):
    def test_prior_peak_excludes_current_candle(self):
        data=candles([100]*200+[200])
        row=features(data,markets(data))[-1]
        self.assertEqual(row['prior_peak_20'],100)
        self.assertEqual(row['drawdown_20_pct'],0)
        self.assertAlmostEqual(row['ma20'],105)

    def test_support_excludes_current_low(self):
        data=candles([100]*200+[70])
        data[-1]=replace(data[-1],low=1)
        row=features(data,markets(data))[-1]
        self.assertEqual(row['support'],99)
        self.assertTrue(row['support_broken'])
        self.assertEqual(row['action'],'REVIEW')
        self.assertFalse(row['market_stress'])
        self.assertFalse(row['trim_formula'])

    def test_future_prices_cannot_change_daily_prefix(self):
        data=candles([100]*201+[80])
        changed=data[:-1]+[replace(data[-1],open=30,high=31,low=29,close=30)]
        self.assertEqual(features(data,markets(data))[:-1],features(changed,markets(changed))[:-1])

    def test_future_vix_publication_not_visible(self):
        data=candles([100]*201)
        old=markets(data)
        future=Observation(data[-1].close_at,data[-1].available_at+timedelta(days=1),{'vix':99},'test')
        self.assertEqual(features(data,old)[-1],features(data,old+[future])[-1])

    def test_ma_rsi_and_return_use_past_closes(self):
        data=candles(list(range(100,305)))
        row=features(data,markets(data))[-1]
        self.assertAlmostEqual(row['ma20'],294.5)
        self.assertEqual(row['rsi14'],100)
        self.assertAlmostEqual(row['day_change_pct'],(304/303-1)*100)

    def test_relative_strength_uses_matched_sessions(self):
        data=candles([100]*200+[90])
        qqq=candles([100]*201,'QQQ')
        row=features(data,markets(data),qqq)[-1]
        self.assertAlmostEqual(row['relative_return_20_pp'],-10)
        qqq[-1]=replace(qqq[-1],available_at=qqq[-1].available_at+timedelta(days=1))
        row=features(data,markets(data),qqq)[-1]
        self.assertIsNone(row['relative_return_20_pp'])
        self.assertIsNone(row['qqq_close'])

    def test_market_regime_and_breadth_not_invented(self):
        data=candles([100]*201)
        row=features(data,markets(data))[-1]
        self.assertEqual(row['market_regime'],'UNAVAILABLE')
        self.assertEqual(row['market_breadth'],'UNAVAILABLE')
        self.assertFalse(row['defensive_regime'])

    def test_severe_vix_branch_explained(self):
        data=candles([100]*201)
        row=features(data,markets(data,31))[-1]
        self.assertEqual(row['action'],'TRIM')
        self.assertTrue(row['severe_market_stress'])
        self.assertFalse(row['support_broken'])
        self.assertEqual(row['trim_blockers'],'')

    def test_support_plus_stress_branch_explained(self):
        data=candles([100]*200+[70])
        row=features(data,markets(data,26))[-1]
        self.assertTrue(row['support_and_stress'])
        self.assertFalse(row['severe_market_stress'])
        self.assertEqual(row['action'],'TRIM')

    def test_stale_data_short_circuits_risk_conditions(self):
        data=candles([100]*201)
        row=features(data,[markets(data,31)[0]])[-1]
        self.assertFalse(row['market_fresh'])
        self.assertFalse(row['risk_conditions_evaluated'])
        self.assertEqual(row['action'],'REVIEW')

    def test_episode_counts_threshold_once_not_each_day(self):
        data=candles([100]*200+[95,89,84,79,85,78])
        rows=features(data,markets(data))
        events=drawdown_events(rows,rows[200]['date'],rows[-1]['date'])
        self.assertEqual(sorted(e['threshold_pct'] for e in events),[10,15,20])
        self.assertAlmostEqual(events[0]['max_drawdown_pct'],-22)
        self.assertFalse(events[0]['recovered_to_peak'])

    def test_recovered_peak_allows_new_episode(self):
        data=candles([100]*200+[80,100,80])
        rows=features(data,markets(data))
        events=drawdown_events(rows,rows[200]['date'],rows[-1]['date'])
        self.assertEqual(len(events),6)
        self.assertEqual(len(set(e['episode_id'] for e in events)),2)

    def test_event_outcomes_cut_off_at_study_end(self):
        data=candles([100]*200+[90,80,50])
        rows=features(data,markets(data))
        events=drawdown_events(rows,rows[200]['date'],rows[201]['date'])
        self.assertTrue(all(e['trough_date']!=rows[-1]['date'] for e in events))
        self.assertTrue(all(e['max_drawdown_pct']>=-20.000001 for e in events))

    def test_missing_indicator_not_counted_as_inactive(self):
        data=candles([100]*230)
        rows=features(data,markets(data))
        evaluation=indicator_evaluation(rows)
        relative=[r for r in evaluation if r['indicator']=='relative_weak_qqq20' and r['period']=='pre_window']
        self.assertTrue(all(r['observations']==0 for r in relative))
        self.assertTrue(all(r['missing_observations']==230 for r in relative))

    def test_forward_labels_are_separate_and_censored(self):
        data=candles([100]*230)
        rows=features(data,markets(data))
        self.assertTrue(all('forward' not in key for row in rows for key in row))
        evaluated=indicator_evaluation(rows)
        group=next(r for r in evaluated if r['period']=='pre_window' and r['indicator']=='below_ma20' and not r['active'])
        self.assertEqual(group['censored'],20)
        self.assertEqual(group['forward_20_loss_10_count'],0)

    def test_fifo_restored_weight_can_leave_share_deficit(self):
        trades=[{'side':'BUY','units':100,'mid_price':100},
                {'side':'SELL','units':25,'mid_price':100},
                {'side':'BUY','units':20,'mid_price':125}]
        cost=fifo_recovery_costs(trades,200)[1]
        self.assertEqual(cost['terminal_unreacquired_units'],5)
        self.assertEqual(cost['matched_repurchase_cost_dollars'],500)
        self.assertEqual(cost['terminal_mark_cost_dollars'],500)
        self.assertEqual(cost['missed_recovery_fifo_dollars'],1000)

    def test_actual_daily_actions_match_parent_replay(self):
        rows=list(csv.DictReader(open('reports/risk-diagnostics/daily-signals.csv')))
        previous={(r['symbol'],r['observed_at'][:10]):r for r in csv.DictReader(open('reports/risk-backtest-v1/signals.csv'))
                  if r['window']=='requested' and r['strategy']=='risk_overlay_only'}
        self.assertEqual(len(rows),111)
        for r in rows:
            self.assertEqual(r['action'],previous[(r['symbol'],r['date'])]['action'])
            self.assertEqual(r['actionable'],previous[(r['symbol'],r['date'])]['actionable'])

    def test_actual_fifo_costs_reconcile_parent_metrics(self):
        rows=list(csv.DictReader(open('reports/risk-diagnostics/recovery-analysis.csv')))
        parent={r['symbol']:r for r in csv.DictReader(open('reports/risk-backtest-v1/summary.csv'))
                if r['window']=='extended_2024_2026' and r['strategy']=='risk_overlay_only'}
        self.assertEqual(len(rows),9)
        for symbol in ('AMD','NVDA','MU'):
            self.assertAlmostEqual(sum(float(r['missed_recovery_fifo_dollars']) for r in rows if r['symbol']==symbol),
                                   float(parent[symbol]['missed_recovery_dollars']),places=6)

    def test_actual_restoration_follows_three_actionable_holds(self):
        diagnostics=list(csv.DictReader(open('reports/risk-diagnostics/recovery-analysis.csv')))
        signals=list(csv.DictReader(open('reports/risk-backtest-v1/signals.csv')))
        for trade in diagnostics:
            dates=trade['restoration_hold_dates'].split('; ')
            self.assertEqual(len(dates),3)
            relevant=[r for r in signals if r['symbol']==trade['symbol'] and r['window']=='extended_2024_2026'
                      and r['strategy']=='risk_overlay_only' and r['observed_at'][:10] in dates]
            self.assertEqual(len(relevant),3)
            self.assertTrue(all(r['action']=='HOLD' and r['actionable']=='True' for r in relevant))

    def test_local_mu_october_excursion_is_retained(self):
        events=list(csv.DictReader(open('reports/risk-diagnostics/drawdown-events.csv')))
        october=[r for r in events if r['symbol']=='MU' and r['peak_date']=='2026-10-01']
        self.assertEqual({int(r['threshold_pct']) for r in october},{10,15,20})
        self.assertTrue(all(r['reference_windows'] for r in october))

    def test_engine_and_execution_unchanged_from_recorded_sources(self):
        recorded=json.loads(Path('reports/risk-backtest-v1/run.json').read_text())['source_sha256']
        for path in ('aae/engines/tactical_risk_overlay.py','aae/backtest/simulator.py'):
            digest=next(h for p,h in recorded.items() if p.endswith(path))
            self.assertEqual(hashlib.sha256(Path(path).read_bytes()).hexdigest(),digest)


if __name__=='__main__':
    unittest.main()
