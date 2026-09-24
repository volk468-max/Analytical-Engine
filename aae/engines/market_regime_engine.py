from typing import Any


class MarketRegimeEngine:
    VERSION = "Market-Regime-Engine-v1"

    def _records(self, history: Any) -> list:
        if isinstance(history, dict):
            history = history.get("records", [])

        if not isinstance(history, list):
            return []

        return [
            row
            for row in history
            if isinstance(row, dict)
            and row.get("close") is not None
        ]

    def _close(self, row: dict) -> float | None:
        try:
            return float(row.get("close"))
        except (TypeError, ValueError):
            return None

    def _ma(self, records: list, period: int) -> float | None:
        closes = [
            self._close(row)
            for row in records
        ]

        closes = [
            value
            for value in closes
            if value is not None
        ]

        if len(closes) < period:
            return None

        return sum(closes[-period:]) / period

    def _index_state(self, history: Any) -> dict:
        records = self._records(history)

        if not records:
            return {
                "status": "NO_DATA"
            }

        closes = [
            self._close(row)
            for row in records
        ]

        closes = [
            value
            for value in closes
            if value is not None
        ]

        if not closes:
            return {
                "status": "NO_DATA"
            }

        price = closes[-1]

        ma50 = self._ma(records, 50)
        ma200 = self._ma(records, 200)

        day_change_pct = None
        momentum_5d_pct = None
        momentum_20d_pct = None

        if len(closes) >= 2 and closes[-2] != 0:
            day_change_pct = (
                price / closes[-2] - 1
            ) * 100

        if len(closes) >= 6 and closes[-6] != 0:
            momentum_5d_pct = (
                price / closes[-6] - 1
            ) * 100

        if len(closes) >= 21 and closes[-21] != 0:
            momentum_20d_pct = (
                price / closes[-21] - 1
            ) * 100

        return {
            "status": "OK",
            "price": round(price, 2),
            "ma50": (
                round(ma50, 2)
                if ma50 is not None
                else None
            ),
            "ma200": (
                round(ma200, 2)
                if ma200 is not None
                else None
            ),
            "above_ma50": (
                price > ma50
                if ma50 is not None
                else None
            ),
            "above_ma200": (
                price > ma200
                if ma200 is not None
                else None
            ),
            "day_change_pct": (
                round(day_change_pct, 2)
                if day_change_pct is not None
                else None
            ),
            "momentum_5d_pct": (
                round(momentum_5d_pct, 2)
                if momentum_5d_pct is not None
                else None
            ),
            "momentum_20d_pct": (
                round(momentum_20d_pct, 2)
                if momentum_20d_pct is not None
                else None
            ),
        }

    def _portfolio_breadth(
        self,
        portfolio_histories: dict,
    ) -> dict:
        total = 0
        above_ma50 = 0
        above_ma200 = 0
        rising_today = 0
        falling_today = 0
        falling_more_2 = 0

        changes = []

        for symbol, history in portfolio_histories.items():
            state = self._index_state(history)

            if state.get("status") != "OK":
                continue

            total += 1

            if state.get("above_ma50") is True:
                above_ma50 += 1

            if state.get("above_ma200") is True:
                above_ma200 += 1

            day_change = state.get("day_change_pct")

            if day_change is None:
                continue

            changes.append(day_change)

            if day_change > 0:
                rising_today += 1

            elif day_change < 0:
                falling_today += 1

            if day_change <= -2:
                falling_more_2 += 1

        if total == 0:
            return {
                "total": 0,
                "status": "NO_DATA"
            }

        average_day_change = (
            sum(changes) / len(changes)
            if changes
            else None
        )

        return {
            "status": "OK",
            "total": total,
            "above_ma50_pct": round(
                above_ma50 / total * 100,
                1,
            ),
            "above_ma200_pct": round(
                above_ma200 / total * 100,
                1,
            ),
            "rising_today_pct": round(
                rising_today / total * 100,
                1,
            ),
            "falling_today_pct": round(
                falling_today / total * 100,
                1,
            ),
            "falling_more_2_pct": round(
                falling_more_2 / total * 100,
                1,
            ),
            "average_day_change_pct": (
                round(average_day_change, 2)
                if average_day_change is not None
                else None
            ),
        }

    def evaluate(
        self,
        market_summary: dict,
        spy_history: Any,
        qqq_history: Any,
        portfolio_histories: dict,
    ) -> dict:

        spy = self._index_state(spy_history)
        qqq = self._index_state(qqq_history)

        breadth = self._portfolio_breadth(
            portfolio_histories
        )

        try:
            vix = float(
                market_summary.get("vix")
                or market_summary.get("VIX")
                or 0
            )
        except (TypeError, ValueError):
            vix = 0

        existing_trend = market_summary.get(
            "trend",
            "UNKNOWN",
        )

        existing_breadth = market_summary.get(
            "breadth",
            "UNKNOWN",
        )

        spy_above_200 = (
            spy.get("above_ma200") is True
        )

        qqq_above_200 = (
            qqq.get("above_ma200") is True
        )

        spy_above_50 = (
            spy.get("above_ma50") is True
        )

        qqq_above_50 = (
            qqq.get("above_ma50") is True
        )

        breadth_50 = breadth.get(
            "above_ma50_pct",
            0,
        )

        breadth_200 = breadth.get(
            "above_ma200_pct",
            0,
        )

        falling_today = breadth.get(
            "falling_today_pct",
            0,
        )

        falling_more_2 = breadth.get(
            "falling_more_2_pct",
            0,
        )

        reasons = []
        warnings = []

        long_term_intact = (
            spy_above_200
            and qqq_above_200
            and breadth_200 >= 50
        )

        short_term_weakness = (
            not spy_above_50
            or not qqq_above_50
            or breadth_50 < 50
            or falling_today >= 60
        )

        broad_selloff = (
            falling_today >= 70
            and falling_more_2 >= 30
        )

        stress = (
            vix >= 25
        )

        severe_stress = (
            vix >= 30
        )

        if (
            spy_above_50
            and qqq_above_50
            and breadth_50 >= 70
            and vix < 18
        ):
            regime = "STRONG_BULL"
            confidence = 80

            reasons.append(
                "Major indices are above MA50 and MA200."
            )

            reasons.append(
                "Portfolio breadth is broadly positive."
            )

            stance = "STAY_INVESTED"

        elif (
            long_term_intact
            and breadth_50 >= 55
            and vix < 22
        ):
            regime = "BULLISH"
            confidence = 75

            reasons.append(
                "Long-term market trend remains intact."
            )

            reasons.append(
                "Breadth remains constructive."
            )

            stance = "STAY_INVESTED_SELECTIVELY"

        elif (
            long_term_intact
            and short_term_weakness
            and not stress
        ):
            regime = "CORRECTION_WITHIN_BULL_TREND"
            confidence = 72

            reasons.append(
                "Long-term trend remains intact."
            )

            reasons.append(
                "Short-term breadth or index momentum has weakened."
            )

            reasons.append(
                "Volatility does not yet indicate market stress."
            )

            stance = (
                "KEEP_CORE_WATCH_SUPPORTS_SELECTIVE_ADD"
            )

        elif (
            broad_selloff
            or stress
            or (
                breadth_50 < 40
                and short_term_weakness
            )
        ):
            regime = "RISK_OFF"
            confidence = 70

            reasons.append(
                "Market breadth has weakened materially."
            )

            if stress:
                reasons.append(
                    "Volatility has moved into a stress regime."
                )

            stance = "REDUCE_TACTICAL_RISK"

        elif (
            not spy_above_200
            and not qqq_above_200
            and breadth_200 < 40
        ):
            regime = "BEARISH_TREND"
            confidence = 80

            reasons.append(
                "Major indices are below MA200."
            )

            reasons.append(
                "Long-term portfolio breadth is weak."
            )

            stance = "DEFENSIVE"

        else:
            regime = "MIXED"
            confidence = 55

            reasons.append(
                "Signals are mixed and do not confirm a clear regime."
            )

            stance = "HOLD_AND_MONITOR"

        if severe_stress:
            warnings.append(
                "VIX is above 30."
            )

        if breadth_50 < 40:
            warnings.append(
                "Less than 40% of portfolio stocks are above MA50."
            )

        if breadth_200 < 50:
            warnings.append(
                "Long-term portfolio breadth has weakened."
            )

        if broad_selloff:
            warnings.append(
                "A broad daily selloff is affecting the portfolio."
            )

        return {
            "regime": regime,
            "confidence_pct": confidence,
            "portfolio_stance": stance,

            "market_summary": {
                "existing_trend": existing_trend,
                "existing_breadth": existing_breadth,
                "vix": round(vix, 2),
            },

            "indices": {
                "SPY": spy,
                "QQQ": qqq,
            },

            "portfolio_breadth": breadth,

            "conditions": {
                "long_term_trend_intact": long_term_intact,
                "short_term_weakness": short_term_weakness,
                "broad_selloff": broad_selloff,
                "market_stress": stress,
                "severe_market_stress": severe_stress,
            },

            "reasons": reasons,
            "warnings": warnings,

            "engine_version": self.VERSION,
            "status": "REGIME_READY",
        }

