from typing import Any


class DecisionEngine:
    VERSION = "Decision-Engine-v1"

    def evaluate(
        self,
        snapshot: dict[str, Any],
        history: list[dict[str, Any]],
        current_weight_pct: float | None = None,
        manual_support: float | None = None,
        manual_resistance: float | None = None,
        market_regime: dict[str, Any] | None = None,
        long_term_thesis: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        symbol = snapshot["symbol"]

        fundamental = snapshot["fundamental"]
        technical = snapshot["technical"]
        risk = snapshot["risk"]
        revisions = snapshot["revisions"]
        market = snapshot["market"]

        # ---------------------------------------------------------
        # 1. Market regime
        # ---------------------------------------------------------

        regime_name = None
        regime_confidence = None
        regime_stance = None

        if isinstance(market_regime, dict):
            regime_name = market_regime.get("regime")
            regime_confidence = market_regime.get(
                "confidence_pct"
            )
            regime_stance = market_regime.get(
                "portfolio_stance"
            )

        # ---------------------------------------------------------
        # 2. Long-term thesis
        # ---------------------------------------------------------

        long_term_view = None
        long_term_confidence = None
        strategic_target_weight_pct = None
        strategic_weight_status = None
        strategic_role = None

        if isinstance(long_term_thesis, dict):
            long_term_view = long_term_thesis.get(
                "long_term_view"
            )

            long_term_confidence = long_term_thesis.get(
                "confidence_pct"
            )

            strategic_target_weight_pct = (
                long_term_thesis.get(
                    "strategic_target_weight_pct"
                )
            )

            strategic_weight_status = (
                long_term_thesis.get(
                    "weight_status"
                )
            )

            strategic_role = long_term_thesis.get(
                "role"
            )

        # ---------------------------------------------------------
        # 3. Data freshness
        # ---------------------------------------------------------

        data_freshness = snapshot.get(
            "data_freshness",
            {},
        )

        freshness_status = data_freshness.get(
            "overall_status",
            "UNKNOWN",
        )

        freshness_warnings = data_freshness.get(
            "warnings",
            [],
        )

        if freshness_status == "FRESH":
            decision_reliability = "HIGH"

        elif freshness_status == "PARTIALLY_STALE":
            decision_reliability = "LIMITED"

        else:
            decision_reliability = "UNKNOWN"

        # ---------------------------------------------------------
        # 4. Core scores
        # ---------------------------------------------------------

        price = float(
            technical["current_price"]
        )

        f_score = float(
            fundamental["fundamental_score"]
        )

        t_score = float(
            technical["technical_score"]
        )

        r_score = float(
            risk["risk_score"]
        )

        rev_score = float(
            revisions["revision_score"]
        )

        rsi = technical.get("rsi14")
        momentum_1m = technical.get(
            "momentum_1m"
        )
        momentum_3m = technical.get(
            "momentum_3m"
        )

        ma50 = technical.get("ma50")
        ma200 = technical.get("ma200")

        estimate_change_30d = revisions.get(
            "estimate_change_30d"
        )

        up_revisions_30d = revisions.get(
            "up_30d",
            0,
        )

        down_revisions_30d = revisions.get(
            "down_30d",
            0,
        )

        market_trend = (
            market.get("market_trend")
            or market.get("trend")
            or "UNKNOWN"
        )

        market_breadth = (
            market.get("breadth_proxy")
            or market.get("breadth")
            or "UNKNOWN"
        )

        try:
            vix = float(
                market.get("vix")
                or 0
            )
        except (TypeError, ValueError):
            vix = 0

        # ---------------------------------------------------------
        # 5. Price history / support / resistance
        # ---------------------------------------------------------

        if isinstance(history, dict):
            history = history.get(
                "records",
                [],
            )

        if not isinstance(history, list):
            history = []

        usable_history = [
            row
            for row in history
            if isinstance(row, dict)
            and row.get("close") is not None
        ]

        def history_date(row: dict):
            return (
                row.get("trade_date")
                or row.get("date")
                or row.get("timestamp")
                or ""
            )

        usable_history.sort(
            key=history_date
        )

        recent_history = usable_history[-120:]

        lows = []
        highs = []

        for row in recent_history:
            try:
                low = row.get("low")

                if low is not None:
                    lows.append(float(low))

                high = row.get("high")

                if high is not None:
                    highs.append(float(high))

            except (TypeError, ValueError):
                continue

        auto_support = (
            min(lows)
            if lows
            else price
        )

        auto_resistance = (
            max(highs)
            if highs
            else price
        )

        support = (
            float(manual_support)
            if manual_support is not None
            else auto_support
        )

        resistance = (
            float(manual_resistance)
            if manual_resistance is not None
            else auto_resistance
        )

        range_source = (
            "MANUAL"
            if (
                manual_support is not None
                or manual_resistance is not None
            )
            else "AUTO"
        )

        range_width = resistance - support

        if range_width > 0:
            range_position_pct = (
                (price - support)
                / range_width
                * 100
            )
        else:
            range_position_pct = 50

        range_position_pct = max(
            0,
            min(
                100,
                range_position_pct,
            ),
        )

        upside_to_resistance_pct = (
            (resistance / price - 1)
            * 100
        )

        downside_to_support_pct = (
            (support / price - 1)
            * 100
        )

        downside_abs = abs(
            downside_to_support_pct
        )

        if downside_abs > 0:
            range_reward_risk = (
                upside_to_resistance_pct
                / downside_abs
            )
        else:
            range_reward_risk = None

        # ---------------------------------------------------------
        # 6. Conditions
        # ---------------------------------------------------------

        above_ma50 = (
            price > float(ma50)
            if ma50 is not None
            else False
        )

        above_ma200 = (
            price > float(ma200)
            if ma200 is not None
            else False
        )

        near_resistance = (
            range_position_pct >= 85
            or upside_to_resistance_pct <= 4
        )

        near_support = (
            range_position_pct <= 25
            or downside_to_support_pct >= -6
        )

        confirmed_breakout = (
            resistance is not None
            and price > resistance * 1.05
        )

        breakout_candidate = (
            resistance is not None
            and price > resistance * 1.03
        )

        strong_revisions = (
            rev_score >= 85
            and (
                estimate_change_30d is None
                or estimate_change_30d >= 0
            )
        )

        deteriorating_revisions = (
            rev_score < 55
            or (
                estimate_change_30d is not None
                and estimate_change_30d < -2
            )
            or (
                down_revisions_30d
                > up_revisions_30d * 2
                and down_revisions_30d >= 4
            )
        )

        strong_technical = (
            t_score >= 75
            and above_ma200
        )

        weak_technical = (
            t_score < 50
            and not above_ma200
        )

        overextended = (
            (
                rsi is not None
                and rsi >= 68
            )
            or (
                momentum_1m is not None
                and momentum_1m >= 15
            )
        )

        oversold = (
            rsi is not None
            and rsi <= 35
        )

        high_risk = (
            r_score >= 60
        )

        bullish_market = (
            market_trend == "BULLISH"
            and market_breadth == "BROAD"
        )

        bearish_market = (
            market_trend == "BEARISH"
        )

        # ---------------------------------------------------------
        # 7. Decision logic
        # ---------------------------------------------------------

        action = "HOLD"
        reason = []
        trigger = None

        # SELL:
        # weak technical structure +
        # deteriorating earnings expectations
        if (
            weak_technical
            and deteriorating_revisions
            and rev_score < 55
        ):
            action = "SELL"

            reason.append(
                "Technical structure is weak."
            )

            reason.append(
                "Earnings revisions are deteriorating."
            )

        # CONFIRMED BREAKOUT:
        # former resistance is no longer treated as ceiling
        elif (
            confirmed_breakout
            and strong_revisions
            and strong_technical
        ):
            if overextended:
                action = "TRIM"

                reason.append(
                    "Former resistance has been decisively broken."
                )

                reason.append(
                    "The long-term trend remains strong, "
                    "but the stock is short-term overextended."
                )

                trigger = (
                    "Retain the core position. "
                    "Consider adding again after consolidation "
                    "or a successful retest of the former "
                    "resistance zone."
                )

            else:
                action = "HOLD"

                reason.append(
                    "Former resistance has been decisively broken."
                )

                reason.append(
                    "Technical structure and earnings revisions "
                    "support the breakout."
                )

                trigger = (
                    "Consider ADD after the breakout is confirmed "
                    "by consolidation above the former resistance."
                )

        # Near resistance with poor asymmetry
        elif (
            near_resistance
            and (
                overextended
                or (
                    range_reward_risk is not None
                    and range_reward_risk < 0.6
                )
            )
        ):
            action = "TRIM"

            reason.append(
                "Price is close to the upper part of its range."
            )

            reason.append(
                "Upside/downside asymmetry has deteriorated."
            )

        # Near resistance but strong structure
        elif (
            near_resistance
            and strong_revisions
            and strong_technical
        ):
            action = "HOLD"

            reason.append(
                "Price is near resistance, but revisions "
                "and technical structure remain strong."
            )

            trigger = (
                "Consider ADD only after a confirmed breakout "
                "above resistance."
            )

        # ADD near support
        elif (
            near_support
            and strong_revisions
            and above_ma200
            and bullish_market
            and not high_risk
        ):
            action = "ADD"

            reason.append(
                "Price is near support."
            )

            reason.append(
                "Earnings revisions and long-term trend "
                "remain constructive."
            )

        # TRIM if revisions deteriorate
        elif (
            deteriorating_revisions
            and t_score < 55
        ):
            action = "TRIM"

            reason.append(
                "Earnings revisions are deteriorating."
            )

            reason.append(
                "Technical confirmation is weak."
            )

        else:
            action = "HOLD"

            reason.append(
                "No sufficiently strong condition for "
                "adding, trimming or exiting."
            )

        # ---------------------------------------------------------
        # 8. Market overlay
        # ---------------------------------------------------------

        if (
            action == "ADD"
            and (
                bearish_market
                or vix >= 30
            )
        ):
            action = "HOLD"

            reason.append(
                "ADD was suppressed because market risk "
                "conditions are unfavorable."
            )

        # ---------------------------------------------------------
        # 9. Position sizing
        # ---------------------------------------------------------

        position_multiplier = {
            "ADD": 1.25,
            "HOLD": 1.0,
            "TRIM": 0.75,
            "SELL": 0.0,
        }.get(
            action,
            1.0,
        )

        target_weight_pct = None

        if current_weight_pct is not None:
            target_weight_pct = round(
                current_weight_pct
                * position_multiplier,
                2,
            )

        # ---------------------------------------------------------
        # 10. Output
        # ---------------------------------------------------------

        return {
            "symbol": symbol,
            "action": action,
            "current_price": round(
                price,
                4,
            ),

            "market_regime": {
                "regime": regime_name,
                "confidence_pct": regime_confidence,
                "portfolio_stance": regime_stance,
            },

            "long_term_thesis": {
                "view": long_term_view,
                "confidence_pct": long_term_confidence,
                "role": strategic_role,
                "strategic_target_weight_pct": (
                    strategic_target_weight_pct
                ),
                "weight_status": strategic_weight_status,
            },

            "data_freshness": {
                "overall_status": freshness_status,
                "warnings": freshness_warnings,
            },

            "decision_reliability": (
                decision_reliability
            ),

            "current_weight_pct": (
                current_weight_pct
            ),

            "position_multiplier": (
                position_multiplier
            ),

            "target_weight_pct": (
                target_weight_pct
            ),

            "range": {
                "support": round(
                    support,
                    4,
                ),
                "resistance": round(
                    resistance,
                    4,
                ),
                "position_in_range_pct": round(
                    range_position_pct,
                    1,
                ),
                "upside_to_resistance_pct": round(
                    upside_to_resistance_pct,
                    2,
                ),
                "downside_to_support_pct": round(
                    downside_to_support_pct,
                    2,
                ),
                "reward_risk_to_range": (
                    round(
                        range_reward_risk,
                        2,
                    )
                    if range_reward_risk is not None
                    else None
                ),
                "source": range_source,
            },

            "signals": {
                "fundamental_score": round(
                    f_score,
                    1,
                ),
                "technical_score": round(
                    t_score,
                    1,
                ),
                "risk_score": round(
                    r_score,
                    1,
                ),
                "revision_score": round(
                    rev_score,
                    1,
                ),
                "rsi14": rsi,
                "momentum_1m_pct": momentum_1m,
                "momentum_3m_pct": momentum_3m,
                "estimate_change_30d_pct": (
                    estimate_change_30d
                ),
                "up_revisions_30d": (
                    up_revisions_30d
                ),
                "down_revisions_30d": (
                    down_revisions_30d
                ),
                "above_ma50": above_ma50,
                "above_ma200": above_ma200,
                "market_trend": market_trend,
                "market_breadth": market_breadth,
                "vix": round(
                    vix,
                    2,
                ),
            },

            "conditions": {
                "near_support": near_support,
                "near_resistance": near_resistance,
                "strong_revisions": strong_revisions,
                "deteriorating_revisions": (
                    deteriorating_revisions
                ),
                "strong_technical": strong_technical,
                "weak_technical": weak_technical,
                "overextended": overextended,
                "oversold": oversold,
                "high_risk": high_risk,
                "breakout_candidate": (
                    breakout_candidate
                ),
                "confirmed_breakout": (
                    confirmed_breakout
                ),
            },

            "reason": reason,
            "trigger": trigger,
            "engine_version": self.VERSION,
            "status": "DECISION_READY",
        }
