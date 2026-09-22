from typing import Any


class DecisionEngine:
    def evaluate(
        self,
        snapshot: dict[str, Any],
        history: list[dict[str, Any]],
        current_weight_pct: float | None = None,
        manual_support: float | None = None,
        manual_resistance: float | None = None,
    ) -> dict[str, Any]:

        symbol = snapshot["symbol"]

        fundamental = snapshot["fundamental"]
        technical = snapshot["technical"]
        risk = snapshot["risk"]
        revisions = snapshot["revisions"]
        market = snapshot["market"]

        price = float(technical["current_price"])

        f_score = float(fundamental["fundamental_score"])
        t_score = float(technical["technical_score"])
        r_score = float(risk["risk_score"])
        rev_score = float(revisions["revision_score"])

        rsi = technical.get("rsi14")
        momentum_1m = technical.get("momentum_1m")
        momentum_3m = technical.get("momentum_3m")

        ma50 = technical.get("ma50")
        ma200 = technical.get("ma200")

        estimate_change_30d = revisions.get(
            "estimate_change_30d"
        )

        up_30d = revisions.get("up_30d") or 0
        down_30d = revisions.get("down_30d") or 0

        market_trend = market.get("market_trend")
        breadth = market.get("breadth_proxy")
        vix = market.get("vix")

        # ------------------------------------------------------
        # 1. Prepare historical range
        # ------------------------------------------------------
        usable = [
            row
            for row in history
            if row.get("trade_date") is not None
            and row.get("close") is not None
        ]

        usable = sorted(
            usable,
            key=lambda x: str(x["trade_date"])
        )

        lookback = usable[-120:]

        if not lookback:
            raise ValueError(
                f"No usable history for {symbol}"
            )

        auto_support = min(
            float(
                row.get("low")
                if row.get("low") is not None
                else row["close"]
            )
            for row in lookback
        )

        auto_resistance = max(
            float(
                row.get("high")
                if row.get("high") is not None
                else row["close"]
            )
            for row in lookback
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

        range_width = resistance - support

        if range_width > 0:
            range_position_pct = (
                (price - support)
                / range_width
                * 100
            )
        else:
            range_position_pct = 50.0

        range_position_pct = max(
            0.0,
            min(100.0, range_position_pct)
        )

        upside_to_resistance_pct = (
            (resistance / price - 1) * 100
        )

        downside_to_support_pct = (
            (support / price - 1) * 100
        )

        if abs(downside_to_support_pct) > 0.01:
            range_reward_risk = (
                upside_to_resistance_pct
                / abs(downside_to_support_pct)
            )
        else:
            range_reward_risk = None

        # ------------------------------------------------------
        # 2. Define conditions
        # ------------------------------------------------------
        above_ma200 = (
            ma200 is not None
            and price > float(ma200)
        )

        below_ma200 = (
            ma200 is not None
            and price < float(ma200)
        )

        above_ma50 = (
            ma50 is not None
            and price > float(ma50)
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
            or down_30d > up_30d * 2
        )

        strong_technical = (
            t_score >= 75
            and above_ma200
        )

        weak_technical = (
            t_score < 50
            and below_ma200
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

        bullish_market = (
            market_trend == "BULLISH"
            and breadth == "BROAD"
        )

        bearish_market = (
            market_trend == "BEARISH"
        )

        high_risk = r_score >= 60

        # ------------------------------------------------------
        # 3. Decision logic
        # ------------------------------------------------------
        action = "HOLD"
        reason = []
        trigger = None

        # SELL:
        # deterioration + broken long-term trend
        if (
            weak_technical
            and deteriorating_revisions
            and rev_score < 55
        ):
            action = "SELL"

            reason.append(
                "Long-term technical structure is broken."
            )
            reason.append(
                "Earnings revisions are deteriorating."
            )
        # CONFIRMED BREAKOUT:
        # old resistance is no longer treated as a ceiling 
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
                    "The long-term trend remains strong, but the stock "
                    "is short-term overextended."
        )

                trigger = (
                    "Retain the core position. Consider adding again "
                    "after consolidation or a successful retest of the "
                    "former resistance zone."
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

        # TRIM:
        # near resistance with poor asymmetry
        elif (
            near_resistance
            and (
                overextended
                or (
                    range_reward_risk is not None
                    and range_reward_risk < 0.60
                )
            )
            and not (
                strong_revisions
                and strong_technical
                and estimate_change_30d is not None
                and estimate_change_30d >= 2
            )
        ):
            action = "TRIM"

            reason.append(
                "Price is close to the upper part of its range."
            )

            reason.append(
                "Upside/downside asymmetry has deteriorated."
            )

        # HOLD near resistance if breakout conditions are strong
        elif (
            near_resistance
            and strong_revisions
            and strong_technical
        ):
            action = "HOLD"

            reason.append(
                "Price is near resistance, but revisions and "
                "technical structure remain strong."
            )

            trigger = (
                "Consider ADD only after a confirmed breakout "
                "above resistance."
            )

        # ADD:
        # good business + strong revisions + lower range
        elif (
            near_support
            and strong_revisions
            and above_ma200
            and bullish_market
            and not high_risk
        ):
            action = "ADD"

            reason.append(
                "Price is near the lower part of its range."
            )

            reason.append(
                "Earnings revisions remain strong."
            )

            reason.append(
                "Long-term technical structure remains intact."
            )

        # TRIM on deterioration before full SELL
        elif (
            deteriorating_revisions
            and t_score < 55
        ):
            action = "TRIM"

            reason.append(
                "Earnings revisions are deteriorating."
            )

            reason.append(
                "Technical structure is weak."
            )

        # HOLD default
        else:
            action = "HOLD"

            reason.append(
                "No sufficiently strong condition for "
                "adding, trimming or exiting."
            )

        # ------------------------------------------------------
        # 4. Market overlay
        # ------------------------------------------------------
        if bearish_market and action == "ADD":
            action = "HOLD"

            reason.append(
                "ADD was suppressed because the broad "
                "market regime is bearish."
            )

        if (
            vix is not None
            and float(vix) >= 30
            and action == "ADD"
        ):
            action = "HOLD"

            reason.append(
                "ADD was suppressed because volatility "
                "is unusually high."
            )

        # ------------------------------------------------------
        # 5. Position sizing v1
        #
        # ADD  = +25% of existing position
        # HOLD = unchanged
        # TRIM = -25% of existing position
        # SELL = zero
        # ------------------------------------------------------
        multiplier_map = {
            "ADD": 1.25,
            "HOLD": 1.00,
            "TRIM": 0.75,
            "SELL": 0.00,
        }

        position_multiplier = multiplier_map[action]

        target_weight_pct = None

        if current_weight_pct is not None:
            target_weight_pct = round(
                float(current_weight_pct)
                * position_multiplier,
                2,
            )

        # ------------------------------------------------------
        # 6. Output
        # ------------------------------------------------------
        return {
            "symbol": symbol,
            "action": action,
            "current_price": round(price, 4),

            "current_weight_pct": current_weight_pct,
            "position_multiplier": position_multiplier,
            "target_weight_pct": target_weight_pct,

            "range": {
                "support": round(support, 4),
                "resistance": round(resistance, 4),
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
                    round(range_reward_risk, 2)
                    if range_reward_risk is not None
                    else None
                ),
                "source": (
                    "MANUAL"
                    if manual_support is not None
                    or manual_resistance is not None
                    else "AUTO_120D"
                ),
            },

            "signals": {
                "fundamental_score": f_score,
                "technical_score": t_score,
                "risk_score": r_score,
                "revision_score": rev_score,

                "rsi14": rsi,
                "momentum_1m_pct": momentum_1m,
                "momentum_3m_pct": momentum_3m,

                "estimate_change_30d_pct":
                    estimate_change_30d,

                "up_revisions_30d": up_30d,
                "down_revisions_30d": down_30d,

                "above_ma50": above_ma50,
                "above_ma200": above_ma200,

                "market_trend": market_trend,
                "market_breadth": breadth,
                "vix": vix,
            },

            "conditions": {
                "near_support": near_support,
                "near_resistance": near_resistance,
                "strong_revisions": strong_revisions,
                "deteriorating_revisions":
                    deteriorating_revisions,
                "strong_technical": strong_technical,
                "weak_technical": weak_technical,
                "overextended": overextended,
                "oversold": oversold,
                "high_risk": high_risk,
                "breakout_candidate": breakout_candidate,
                "confirmed_breakout": confirmed_breakout,
            },

            "reason": reason,
            "trigger": trigger,

            "engine_version": "Decision-Engine-v1",
            "status": "DECISION_READY",
        }
