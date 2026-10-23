
from typing import Any
from datetime import datetime, timezone
from .tactical_risk_overlay import (TacticalRiskConfig, TacticalRiskOverlay, historical_levels, timestamp, number)


class DecisionEngine:
    VERSION = "Decision-Engine-v2"

    def __init__(self, risk_config: TacticalRiskConfig | None = None):
        self.risk_config = risk_config or TacticalRiskConfig.from_env()

    def evaluate(
        self,
        snapshot: dict[str, Any],
        history: list[dict[str, Any]],
        current_weight_pct: float | None = None,
        manual_support: float | None = None,
        manual_resistance: float | None = None,
        market_regime: dict[str, Any] | None = None,
        long_term_thesis: dict[str, Any] | None = None,
        now: datetime | None = None,
    ) -> dict[str, Any]:

        now = timestamp(now or datetime.now(timezone.utc))
        if now is None:
            raise ValueError("Invalid evaluation time")
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

        if number(price) is None or price <= 0:
            raise ValueError("Current price must be finite and positive")

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

        price_as_of = technical.get("price_as_of")
        # Unstamped technical snapshots cannot safely be matched to another history fetch.
        auto_support, auto_resistance = historical_levels(
            history, price_as_of, self.risk_config.support_lookback
        )

        support = (
            number(manual_support)
            if manual_support is not None
            else auto_support
        )

        resistance = (
            number(manual_resistance)
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

        levels_valid = (support is not None and resistance is not None
                        and 0 < support < resistance)
        range_width = resistance - support if levels_valid else 0

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
            ((resistance / price - 1) if levels_valid else 0)
            * 100
        )

        downside_to_support_pct = (
            ((support / price - 1) if levels_valid else 0)
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
            levels_valid and (range_position_pct >= 85
            or upside_to_resistance_pct <= 4)
        )

        near_support = (
            levels_valid and (range_position_pct <= 25
            or downside_to_support_pct >= -6)
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

        strong_fundamental = (
            f_score >= 70
        )

        # Support is considered crossed as soon as price
        # falls below the selected level.
        support_broken = (
            levels_valid and price < support
        )

        support_holding = (
            levels_valid and price >= support
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

        # REVIEW:
        # support broken, fundamentals strong,
        # technical structure weak.
        if (
            strong_fundamental
            and support_broken
            and weak_technical
        ):
            action = "REVIEW"

            reason.append(
                "Price has fallen below the selected support level."
            )

            reason.append(
                "The fundamental score remains strong, but "
                "the technical structure is weak."
            )

            if deteriorating_revisions:
                reason.append(
                    "Earnings revisions are deteriorating."
                )

            if long_term_view is None:
                reason.append(
                    "No verified long-term thesis is available."
                )

            trigger = (
                "Review the investment thesis, earnings revisions, "
                "and support-break confirmation before changing "
                "the position. REVIEW is not an automatic exit."
            )

        # SELL / TRIM / HOLD:
        # consider fundamentals, oversold status and support.
        elif (
            weak_technical
            and deteriorating_revisions
            and rev_score < 55
        ):

            if (
                strong_fundamental
                and oversold
                and support_holding
            ):
                action = "HOLD"

                reason.append(
                    "Fundamentals remain strong despite "
                    "weak technical conditions."
                )

                reason.append(
                    "The stock is oversold and has not "
                    "confirmed a support breakdown."
                )

                trigger = (
                    "Reassess if support breaks or "
                    "fundamentals deteriorate."
                )

            elif (
                strong_fundamental
                and support_holding
            ):
                action = "TRIM"

                reason.append(
                    "Earnings revisions and technical "
                    "structure are deteriorating."
                )

                reason.append(
                    "Strong fundamentals do not yet "
                    "justify a full exit."
                )

            else:
                action = "SELL"

                reason.append(
                    "Weak technical structure and "
                    "deteriorating earnings revisions "
                    "justify an exit."
                )

                if support_broken:
                    reason.append(
                        "Price has broken below support."
                    )

                if not strong_fundamental:
                    reason.append(
                        "Fundamental strength is insufficient "
                        "to offset the negative signals."
                    )

        # CONFIRMED BREAKOUT:
        # former resistance is no longer treated as ceiling.
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

        # Near resistance with poor asymmetry.
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

        # Near resistance but strong structure.
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

        # ADD near support.
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

        # TRIM if revisions deteriorate.
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

        thesis_review_required = action == "REVIEW"
        tactical = TacticalRiskOverlay(self.risk_config).evaluate(
            price=price, support=support if levels_valid else None,
            price_as_of=price_as_of, market=market,
            market_regime=market_regime, now=now,
        )
        if not tactical["actionable"] or not levels_valid:
            action = "REVIEW"
            reason = list(tactical["reasons"])
            trigger = "Refresh and verify market data and historical levels before trading."
            decision_reliability = "LIMITED"
        elif tactical["action"] == "TRIM" and action != "SELL":
            action = "TRIM"
            reason.extend(tactical["reasons"])
            trigger = "Consider reducing tactical exposure; retain a separately assessed core position."
        elif tactical["action"] == "REVIEW" and action in {"ADD", "HOLD"}:
            action = "REVIEW"
            reason.extend(tactical["reasons"])
            trigger = "Review tactical risk before changing exposure."

        # ---------------------------------------------------------
        # 9. Position sizing
        # ---------------------------------------------------------

        position_multiplier = {
            "ADD": 1.25,
            "HOLD": 1.0,
            "REVIEW": 1.0,
            "TRIM": 1 - self.risk_config.trim_fraction,
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
            "tactical_risk": tactical,
            "price_as_of": price_as_of,
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
                "support": round(support, 4) if support is not None else None,
                "resistance": round(resistance, 4) if resistance is not None else None,
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
                "valid": levels_valid,
                "lookback": self.risk_config.support_lookback,
                "historical_before": price_as_of,
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
                    2
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
                "strong_fundamental": strong_fundamental,
                "support_broken": support_broken,
                "review_required": action == "REVIEW",
                "thesis_review_required": thesis_review_required,
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
            "status": "DECISION_READY" if tactical["actionable"] else "DATA_REVIEW_REQUIRED",
        }
