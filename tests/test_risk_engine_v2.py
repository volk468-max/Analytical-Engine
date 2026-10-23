"""Offline, synthetic policy regressions; these are not a performance backtest."""
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone
from aae.engines.tactical_risk_overlay import TacticalRiskConfig, TacticalRiskOverlay, historical_levels
from aae.engines.decision_engine import DecisionEngine
from aae.engines.strategy_engine import StrategyEngine
from aae.engines.technical_analysis import TechnicalAnalysisEngine
from aae.engines.market_regime_engine import MarketRegimeEngine
from aae.engines.data_freshness_engine import DataFreshnessEngine

NOW = datetime(2026, 6, 15, 22, tzinfo=timezone.utc)
DATE = NOW.date().isoformat()


def history(price=105):
    rows = [{"trade_date": (NOW - timedelta(days=i)).date().isoformat(),
             "close": 105, "low": 100, "high": 120} for i in range(260, 0, -1)]
    return rows + [{"trade_date": DATE, "close": price, "low": price - 5, "high": price + 5}]


def snapshot(price=105, vix=16):
    return {"symbol": "TEST", "fundamental": {"fundamental_score": 90},
            "technical": {"current_price": price, "price_as_of": DATE, "technical_score": 65,
                          "ma50": 104, "ma200": 102, "rsi14": 50},
            "risk": {"risk_score": 30}, "revisions": {"revision_score": 75},
            "market": {"vix": vix, "trade_date": DATE},
            "data_freshness": {"overall_status": "FRESH"}}


class RiskV2Tests(unittest.TestCase):
    def decision(self, price=105, vix=16, **kwargs):
        return DecisionEngine().evaluate(snapshot(price, vix), history(price), now=NOW, **kwargs)

    def test_current_candle_excluded(self):
        decision = self.decision(90)
        self.assertEqual(decision['range']['support'], 100)
        self.assertTrue(decision['conditions']['support_broken'])
        self.assertEqual(decision['tactical_risk']['action'], 'REVIEW')

    def test_current_high_excluded_and_breakout_detected(self):
        decision = self.decision(130)
        self.assertEqual(decision['range']['resistance'], 120)
        self.assertTrue(decision['conditions']['confirmed_breakout'])

    def test_future_rows_do_not_change_levels_or_technical(self):
        rows = history()
        future = {"trade_date": '2026-06-16', "close": 1000, "low": 1, "high": 2000}
        self.assertEqual(historical_levels(rows, DATE), historical_levels(rows + [future], DATE))
        engine = TechnicalAnalysisEngine()
        self.assertEqual(engine.evaluate({'records': rows}, as_of=NOW),
                         engine.evaluate({'records': rows + [future]}, as_of=NOW))

    def test_support_break_and_market_stress_trim_despite_bullish_thesis(self):
        decision = self.decision(90, 26, long_term_thesis={'long_term_view': 'BULLISH'})
        self.assertEqual(decision['action'], 'TRIM')
        self.assertEqual(decision['position_multiplier'], .75)
        self.assertEqual(decision['long_term_thesis']['view'], 'BULLISH')

    def test_severe_market_risk_trims_without_support_break(self):
        self.assertEqual(self.decision(vix=31)['tactical_risk']['action'], 'TRIM')

    def test_normal_market_does_not_reduce(self):
        decision = self.decision()
        self.assertEqual(decision['tactical_risk']['action'], 'HOLD')
        self.assertEqual(decision['action'], 'HOLD')

    def test_stress_alone_requires_review(self):
        self.assertEqual(self.decision(vix=26)['tactical_risk']['action'], 'REVIEW')

    def test_stale_quote_blocks_trade_and_size_change(self):
        data = snapshot(90, 31)
        data['technical']['price_as_of'] = '2026-06-01'
        result = DecisionEngine().evaluate(data, history(90), current_weight_pct=10, now=NOW)
        self.assertEqual(result['action'], 'REVIEW')
        self.assertFalse(result['tactical_risk']['actionable'])
        self.assertEqual(result['target_weight_pct'], 10)

    def test_stale_market_blocks_trim_even_if_recollected_now(self):
        data = snapshot(90, 31)
        data['market'].update(trade_date='2026-06-01', created_at=NOW.isoformat())
        result = DecisionEngine().evaluate(data, history(90), now=NOW)
        self.assertEqual(result['action'], 'REVIEW')
        self.assertFalse(result['tactical_risk']['actionable'])

    def test_collection_time_alone_does_not_verify_market(self):
        data = snapshot(90, 31)
        data['market'] = {'vix': 31, 'created_at': NOW.isoformat()}
        result = DecisionEngine().evaluate(data, history(90), now=NOW)
        self.assertEqual(result['action'], 'REVIEW')
        self.assertFalse(result['tactical_risk']['actionable'])

    def test_buffer_boundary_and_freshness_boundary(self):
        overlay = TacticalRiskOverlay(TacticalRiskConfig(max_quote_age_hours=24))
        args = dict(price=99, support=100, price_as_of=NOW - timedelta(hours=24),
                    market={'vix': 16, 'snapshot_time': NOW.isoformat()}, now=NOW)
        self.assertEqual(overlay.evaluate(**args)['action'], 'HOLD')
        args['price'] = 98.99
        self.assertEqual(overlay.evaluate(**args)['action'], 'REVIEW')
        args['price_as_of'] -= timedelta(seconds=1)
        self.assertFalse(overlay.evaluate(**args)['actionable'])

    def test_missing_future_invalid_quote_dates_block(self):
        for value in (None, 'bad', '2026-06-16'):
            with self.subTest(value=value):
                data = snapshot()
                data['technical']['price_as_of'] = value
                self.assertEqual(DecisionEngine().evaluate(data, history(), now=NOW)['action'], 'REVIEW')

    def test_insufficient_or_duplicate_history_does_not_invent_levels(self):
        for rows in (history()[-10:], history() + [history()[0]]):
            result = DecisionEngine().evaluate(snapshot(), rows, now=NOW)
            self.assertIsNone(result['range']['support'])
            self.assertEqual(result['action'], 'REVIEW')

    def test_config_changes_policy(self):
        engine = DecisionEngine(TacticalRiskConfig(stress_vix=40, severe_vix=50, trim_fraction=.1))
        result = engine.evaluate(snapshot(90, 31), history(90), now=NOW)
        self.assertEqual(result['tactical_risk']['action'], 'REVIEW')
        result = engine.evaluate(snapshot(90, 51), history(90), now=NOW)
        self.assertAlmostEqual(result['position_multiplier'], .9)

    def test_environment_configuration(self):
        with patch.dict('os.environ', {'ALPHA_RISK_TRIM_FRACTION': '0.1'}):
            self.assertEqual(DecisionEngine().risk_config.trim_fraction, .1)

    def test_invalid_price_rejected(self):
        for price in (0, -1, float('nan'), float('inf')):
            with self.subTest(price=price), self.assertRaises(ValueError):
                self.decision(price)

    def test_old_regime_cannot_confirm_break(self):
        result = self.decision(90, market_regime={'regime': 'RISK_OFF', 'data_freshness': {
            'status': 'FRESH', 'evaluated_at': '2026-06-01'}})
        self.assertEqual(result['tactical_risk']['action'], 'REVIEW')

    def test_invalid_config_rejected(self):
        for kwargs in ({'trim_fraction': 1}, {'stress_vix': 40}, {'max_quote_age_hours': float('nan')},
                       {'support_lookback': 0}, {'support_break_buffer_pct': -1}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                TacticalRiskConfig(**kwargs)

    def test_strategy_propagates_tactical_trim_preserves_thesis(self):
        decision = self.decision(90, 31, long_term_thesis={'long_term_view': 'BULLISH'})
        result = StrategyEngine().evaluate(decision, snapshot(90, 31))
        self.assertEqual(result['strategies']['short_term']['action'], 'TRIM')
        self.assertEqual(result['strategies']['medium_term']['action'], 'TRIM_TACTICAL_EXPOSURE')
        self.assertEqual(result['strategies']['long_term']['action'], 'MAINTAIN_CORE_POSITION')

    def test_strategy_blocks_stale_data(self):
        data = snapshot()
        data['market']['trade_date'] = '2026-06-01'
        decision = DecisionEngine().evaluate(data, history(), now=NOW)
        result = StrategyEngine().evaluate(decision, data)
        self.assertEqual(result['strategies']['short_term']['action'], 'REVIEW')
        self.assertEqual(result['strategies']['medium_term']['action'], 'REVIEW')

    def test_freshness_uses_observation_not_collection(self):
        result = DataFreshnessEngine().evaluate({}, [{'trade_date': '2026-06-01', 'created_at': NOW.isoformat()}],
                                                {}, {'trade_date': '2026-06-01', 'created_at': NOW.isoformat()}, now=NOW)
        self.assertEqual(result['history']['status'], 'STALE')
        self.assertEqual(result['market']['status'], 'STALE')

    def test_future_timestamp_not_fresh(self):
        self.assertEqual(DataFreshnessEngine()._status(-1, 36), 'INVALID')

    def test_regime_missing_or_stale_inputs_unavailable(self):
        for rows in ([], history()[:-20]):
            result = MarketRegimeEngine().evaluate(snapshot()['market'], rows, rows, {'TEST': rows}, now=NOW)
            self.assertEqual(result['regime'], 'UNKNOWN')

    def test_fresh_regime_is_usable(self):
        result = MarketRegimeEngine().evaluate(snapshot()['market'], history(110), history(110),
                                              {'TEST': history(110)}, now=NOW)
        self.assertEqual(result['data_freshness']['status'], 'FRESH')

    def test_fresh_defensive_regime_confirms_break(self):
        result = self.decision(90, market_regime={'regime': 'RISK_OFF', 'data_freshness': {'status': 'FRESH', 'evaluated_at': NOW.isoformat()}})
        self.assertEqual(result['tactical_risk']['action'], 'TRIM')
        result = self.decision(90, market_regime={'regime': 'RISK_OFF'})
        self.assertEqual(result['tactical_risk']['action'], 'REVIEW')


if __name__ == '__main__':
    unittest.main()
