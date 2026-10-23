import hashlib
import unittest
import csv
import json
import tempfile
from unittest.mock import patch
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from aae.backtest.simulator import (Bar, Observation, ExecutionConfig, OverlayPolicy,
    ArchivedDecisionPolicy, BuyAndHold, TacticalRiskConfig, simulate, visible)

BASE = datetime(2025, 1, 1, tzinfo=timezone.utc)


def bars(count=12):
    return [Bar('TEST', BASE + timedelta(days=i, hours=14), BASE + timedelta(days=i, hours=20),
                BASE + timedelta(days=i, hours=21), 100, 101, 99, 100, 'synthetic test only') for i in range(count)]


class Scripted:
    name = 'synthetic_test_policy'
    def __init__(self, actions):
        self.actions = actions
    def __call__(self, bar, history, at):
        action = self.actions.get((bar.open_at - BASE).days, 'HOLD')
        return dict(action=action, actionable=action != 'REVIEW', reasons=['synthetic fixture'], position_multiplier=.75)


def run(policy=None, data=None, execution=None, end=None, **kwargs):
    return simulate(data or bars(), policy or BuyAndHold(), BASE, end or BASE + timedelta(days=20),
                    execution or ExecutionConfig(commission_bps=0, slippage_bps=0), **kwargs)


class BacktestTests(unittest.TestCase):
    def test_future_observation_is_not_visible(self):
        old = Observation(BASE, BASE, {'vix': 10}, 'test')
        future = Observation(BASE, BASE + timedelta(days=1), {'vix': 99}, 'test')
        self.assertIs(visible([old, future], BASE), old)
        self.assertIsNone(visible([future], BASE))

    def test_no_future_bars_in_callback(self):
        class Spy(BuyAndHold):
            def __call__(self, bar, history, at):
                assert all(b.close_at <= at and b.available_at <= at for b in history)
                assert history[-1] == bar
                return super().__call__(bar, history, at)
        run(Spy())

    def test_future_mutation_does_not_change_prefix(self):
        data = bars()
        later = [replace(b, open=1000, close=1000, high=1001, low=999) if i > 5 else b for i,b in enumerate(data)]
        a = run(Scripted({2:'TRIM'}), data)
        b = run(Scripted({2:'TRIM'}), later)
        self.assertEqual(a['signals'][:6], b['signals'][:6])
        self.assertEqual(a['equity'][:6], b['equity'][:6])

    def test_trade_executes_at_next_open_not_signal_close(self):
        data = bars()
        data[3] = replace(data[3], open=80, low=79, high=101)
        result = run(Scripted({2:'TRIM'}), data)
        sell = next(t for t in result['trades'] if t['side'] == 'SELL')
        self.assertEqual(sell['executed_at'], data[3].open_at.isoformat())
        self.assertEqual(sell['mid_price'], 80)
        self.assertLess(sell['signal_at'], sell['executed_at'])

    def test_multisession_delay(self):
        result = run(Scripted({1:'TRIM'}), execution=ExecutionConfig(delay_sessions=2))
        self.assertEqual(result['trades'][1]['executed_at'], bars()[3].open_at.isoformat())

    def test_publication_after_next_open_delays_execution(self):
        data = bars()
        # Publication after the following open but before its close.
        data[1] = replace(data[1], available_at=BASE + timedelta(days=2, hours=15))
        result = run(Scripted({1:'TRIM'}), data)
        self.assertEqual(result['trades'][1]['executed_at'], data[3].open_at.isoformat())

    def test_costs_and_slippage_deducted(self):
        result = run(execution=ExecutionConfig(commission_bps=10, slippage_bps=20))
        initial = result['trades'][0]
        self.assertAlmostEqual(initial['fill_price'], 100.2)
        self.assertAlmostEqual(result['equity'][-1]['equity'], 10000 / 1.002 / 1.001)
        self.assertLess(result['metrics']['return_pct'], 0)

    def test_flat_buy_hold_zero_without_costs(self):
        self.assertEqual(run()['metrics']['return_pct'], 0)
        self.assertEqual(len(run()['trades']), 1)

    def test_repeat_trim_suppressed_per_episode(self):
        result = run(Scripted({i:'TRIM' for i in range(10)}))
        self.assertEqual(sum(t['side']=='SELL' for t in result['trades']), 1)
        self.assertEqual(sum(s['action']=='TRIM' for s in result['signals']), 10)

    def test_compounding_has_floor(self):
        result = run(Scripted({i:'TRIM' for i in range(12)}),
                     execution=ExecutionConfig(repeat_trim='compound', min_weight=.4, commission_bps=0, slippage_bps=0))
        self.assertGreaterEqual(result['equity'][-1]['weight'], .4 - 1e-10)

    def test_three_holds_restore_at_later_open(self):
        result = run(Scripted({0:'TRIM'}))
        restore = next(t for t in result['trades'] if t['reason']=='restore')
        self.assertEqual(restore['executed_at'], bars()[4].open_at.isoformat())
        self.assertAlmostEqual(restore['weight_after'], 1)

    def test_review_interrupts_restoration(self):
        result = run(Scripted({0:'TRIM', 2:'REVIEW'}))
        restore = next(t for t in result['trades'] if t['reason']=='restore')
        self.assertEqual(restore['executed_at'], bars()[6].open_at.isoformat())

    def test_terminal_order_unfilled(self):
        result = run(Scripted({11:'TRIM'}))
        self.assertEqual(len(result['trades']), 1)
        self.assertTrue(result['metrics']['pending_at_end'])

    def test_strict_rejects_assumed_prices(self):
        data = [replace(b, verified=False) for b in bars()]
        with self.assertRaises(ValueError):
            run(data=data)
        self.assertEqual(run(data=data, allow_assumed=True)['metrics']['validation'], 'assumed_availability_price_replay')

    def test_strict_rejects_assumed_market(self):
        observation = Observation(BASE, BASE, {'vix': 30}, 'test', verified=False)
        with self.assertRaises(ValueError):
            run(OverlayPolicy(markets=[observation]))

    def test_no_archives_no_full_comparison(self):
        for version in ('alpha_v1', 'risk_v2'):
            with self.assertRaises(ValueError):
                run(ArchivedDecisionPolicy(version, []))

    def test_unavailable_vix_requires_review_not_fabrication(self):
        result = run(OverlayPolicy(TacticalRiskConfig(support_lookback=2)))
        self.assertTrue(all(s['action']=='REVIEW' for s in result['signals']))
        self.assertEqual(len(result['trades']), 1)

    def test_false_signal_horizon_is_censored(self):
        result = run(Scripted({10:'TRIM'}))
        self.assertEqual(result['metrics']['censored_false_signals'], 1)
        self.assertEqual(result['metrics']['false_signals'], 0)

    def test_drawdown_includes_initial_cost(self):
        result = run(execution=ExecutionConfig(commission_bps=10, slippage_bps=0))
        self.assertLess(result['metrics']['max_drawdown_pct'], 0)

    def test_invalid_ohlc_or_timestamps_rejected(self):
        for kwargs in ({'open':float('nan')}, {'low':102}, {'available_at':BASE}, {'open_at':'2025-01-01'}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                replace(bars()[0], **kwargs)

    def test_invalid_execution_config(self):
        for kwargs in ({'delay_sessions':0}, {'commission_bps':-1}, {'slippage_bps':10000}, {'repeat_trim':'unknown'}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                ExecutionConfig(**kwargs)

    def test_future_bars_not_marked_as_completed(self):
        result = run(end=BASE + timedelta(days=3))
        self.assertEqual(len(result['signals']), 3)

    def test_missed_recovery_uses_sold_units(self):
        data = bars()
        data = [replace(b, open=110, close=110, low=109, high=111) if i >= 3 else b for i,b in enumerate(data)]
        result = run(Scripted({0:'TRIM'}), data)
        self.assertAlmostEqual(result['metrics']['missed_recovery_dollars'], 250)

    def test_verified_archive_replays_both_engines(self):
        data = bars(4)
        archives = []
        for bar in data:
            snapshot = dict(symbol='TEST', fundamental={'fundamental_score': 80},
                technical={'current_price': bar.close, 'price_as_of': bar.close_at.isoformat(),
                           'technical_score': 65, 'rsi14': 50, 'ma50': 100, 'ma200': 100},
                risk={'risk_score': 30}, revisions={'revision_score': 75},
                market={'vix': 16, 'snapshot_time': bar.close_at.isoformat()},
                data_freshness={'overall_status': 'FRESH'})
            archives.append(Observation(bar.close_at, bar.available_at,
                {'snapshot': snapshot, 'point_in_time_attested': True}, 'synthetic archive'))
        for version in ('alpha_v1', 'risk_v2'):
            result = run(ArchivedDecisionPolicy(version, archives, TacticalRiskConfig(support_lookback=2)), data)
            self.assertEqual(len(result['signals']), 4)

    def test_archive_attestation_and_publication_enforced(self):
        bar = bars()[0]
        for archive in (
            Observation(bar.close_at, bar.available_at + timedelta(days=1), {}, 'test'),
            Observation(bar.close_at, bar.available_at, {'snapshot': {'technical': {
                'current_price': 100, 'price_as_of': bar.close_at.isoformat()}, 'symbol':'TEST'}}, 'test'),
        ):
            with self.assertRaises(ValueError):
                run(ArchivedDecisionPolicy('risk_v2', [archive]))

    def test_missing_data_cli_exports_unavailable_not_zero(self):
        from aae.backtest.cli import main
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch('aae.backtest.cli.SYMBOLS', ['TEST']), patch('sys.argv',
                ['backtest', '--data', str(root/'missing'), '--output', str(root/'output')]):
                main()
            rows = list(csv.DictReader((root/'output'/'summary.csv').open()))
            self.assertEqual(len(rows), 4)
            self.assertTrue(all(row['status'] == 'UNAVAILABLE' for row in rows))
            self.assertTrue(all(not row.get('return_pct') for row in rows))

    def test_cli_rejects_changed_input_checksum(self):
        from aae.backtest.cli import main
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'bars.csv').write_text('changed')
            (root/'manifest.json').write_text(json.dumps({'artifact_sha256': {'bars.csv':'wrong'}}))
            with patch('sys.argv', ['backtest', '--data', str(root), '--output', str(root/'output')]), self.assertRaises(ValueError):
                main()

    def test_nested_future_timestamp_rejected_despite_attestation(self):
        bar = bars()[0]
        payload = {'point_in_time_attested': True, 'snapshot': {'symbol':'TEST',
            'technical': {'current_price':100, 'price_as_of':bar.close_at.isoformat()},
            'fundamental': {'snapshot_time':(bar.available_at + timedelta(days=1)).isoformat()}}}
        archive = Observation(bar.close_at, bar.available_at, payload, 'test')
        with self.assertRaises(ValueError):
            run(ArchivedDecisionPolicy('risk_v2', [archive]))

    def test_legacy_source_is_exact(self):
        # Original main a14ebf9, SHA-1 of its unmodified Git blob.
        content = Path('aae/backtest/legacy_decision_engine.py').read_bytes()
        digest = hashlib.sha1(b'blob '+str(len(content)).encode()+b'\0'+content).hexdigest()
        self.assertEqual(digest, '26721ae07a6ae2d60d1c771754981e714b479624')


if __name__ == '__main__':
    unittest.main()
