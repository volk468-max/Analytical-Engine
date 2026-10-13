
from datetime import datetime, timezone


class StrategyEngine:
    VERSION = "Strategy-Engine-v1.1"

    @staticmethod
    def _number(value, default=None):
        try:
            if value is None:
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _get(data, *keys, default=None):
        current = data
        for key in keys:
            if not isinstance(current, dict):
                return default
            current = current.get(key)
        return default if current is None else current

    def evaluate(
        self,
        decision: dict,
        snapshot: dict,
        market_regime: dict = None,
        long_term_thesis: dict = None,
    ) -> dict:

        decision = decision or {}
        snapshot = snapshot or {}
        market_regime = market_regime or {}
        long_term_thesis = long_term_thesis or {}

        technical = snapshot.get("technical") or {}
        fundamental = snapshot.get("fundamental") or {}
        risk = snapshot.get("risk") or {}
        revisions = snapshot.get("revisions") or {}

        symbol = (
            decision.get("symbol")
            or snapshot.get("symbol")
        )

        price = self._number(
            decision.get("current_price")
        )

        rsi = self._number(
            technical.get("rsi14")
        )
        ma50 = self._number(
            technical.get("ma50")
        )
        ma200 = self._number(
            technical.get("ma200")
        )

        fundamental_score = self._number(
            fundamental.get("fundamental_score"), 0
        )
        technical_score = self._number(
            technical.get("technical_score"), 0
        )
        risk_score = self._number(
            risk.get("risk_score"), 50
        )
        revision_score = self._number(
            revisions.get("revision_score"), 50
        )

        range_data = decision.get("range") or {}
        support = self._number(
            range_data.get("support")
        )
        resistance = self._number(
            range_data.get("resistance")
        )

        # ----------------------------------
        # MARKET REGIME
        # ----------------------------------

        decision_market = (
            decision.get("market_regime") or {}
        )

        if not isinstance(decision_market, dict):
            decision_market = {}

        if not isinstance(market_regime, dict):
            market_regime = {}

        regime = (
            decision_market.get("regime")
            or market_regime.get("regime")
            or "UNKNOWN"
        )

        # ----------------------------------
        # LONG-TERM THESIS
        # ----------------------------------

        decision_thesis = (
            decision.get("long_term_thesis") or {}
        )

        if not isinstance(decision_thesis, dict):
            decision_thesis = {}

        if not isinstance(long_term_thesis, dict):
            long_term_thesis = {}

        thesis_view = (
            decision_thesis.get("view")
            or long_term_thesis.get("view")
        )

        thesis_confidence = self._number(
            decision_thesis.get("confidence_pct")
        )

        if thesis_confidence is None:
            thesis_confidence = self._number(
                long_term_thesis.get("confidence_pct")
            )

        strategic_weight = self._number(
            decision_thesis.get(
                "strategic_target_weight_pct"
            )
        )

        if strategic_weight is None:
            strategic_weight = self._number(
                long_term_thesis.get(
                    "strategic_target_weight_pct"
                )
            )

        current_weight = self._number(
            decision.get("current_weight_pct")
        )

        # ----------------------------------
        # DATA QUALITY
        # ----------------------------------

        freshness = (
            decision.get("data_freshness") or {}
        )

        if not isinstance(freshness, dict):
            freshness = {}

        freshness_status = freshness.get(
            "overall_status", "UNKNOWN"
        )

        reliability = decision.get(
            "decision_reliability", "UNKNOWN"
        )

        decision_action = decision.get(
            "action", "UNKNOWN"
        )

        data_warnings = freshness.get(
            "warnings") or []

        if not isinstance(data_warnings, list):
            data_warnings = [str(data_warnings)]

        warnings = list(data_warnings)

        data_limited = (
            freshness_status != "FRESH"
            or reliability != "HIGH"
        )

        if data_limited:
            warnings.append(
                "Investment strategy is based on "
                "incomplete, stale or unverified data."
            )

        review_required = (
            decision_action == "REVIEW"
            or bool(
                self._get(
                    decision,
                    "conditions",
                    "review_required",
                    default=False,
                )
            )
        )

        if review_required:
            warnings.append(
                "Decision Engine requires an investment review."
            )

        # ----------------------------------
        # MARKET SUMMARY
        # ----------------------------------

        if regime == "CORRECTION_WITHIN_BULL_TREND":
            market_summary = (
                "The market is correcting within a broader "
                "bull trend. Maintain core positions and "
                "add selectively when conditions permit."
            )

        elif regime in ("BEAR_MARKET", "RISK_OFF"):
            market_summary = (
                "Market conditions are defensive. "
                "Prioritize capital preservation."
            )

        elif regime in ("BULL_MARKET", "STRONG_BULL"):
            market_summary = (
                "Market conditions favor growth exposure, "
                "subject to valuation and risk."
            )

        else:
            market_summary = (
                "Market conditions are mixed or uncertain. "
                "Avoid aggressive position changes."
            )

        # ----------------------------------
        # SHORT TERM: 1-4 WEEKS
        # ----------------------------------

        short_action = "WAIT"
        short_reasons = []

        if review_required:
            short_action = "REVIEW"
            short_reasons.append(
                "The investment thesis requires review "
                "before changing exposure."
            )

        elif data_limited:
            short_action = "WAIT_FOR_FRESH_DATA"
            short_reasons.append(
                "Fresh and reliable market data are required "
                "before making a new entry decision."
            )

        elif (
            technical_score >= 70
            and revision_score >= 70
            and rsi is not None
            and 40 <= rsi <= 65
            and regime not in (
                "BEAR_MARKET",
                "RISK_OFF",
            )
        ):
            short_action = "HOLD_OR_SELECTIVE_ADD"
            short_reasons.append(
                "Technical conditions and analyst "
                "revisions are supportive."
            )

        elif (
            rsi is not None
            and rsi < 35
            and fundamental_score >= 70
        ):
            short_action = "WAIT_FOR_CONFIRMATION"
            short_reasons.append(
                "The stock is oversold, but a reversal "
                "requires confirmation."
            )

        elif technical_score < 45:
            short_action = "DEFENSIVE"
            short_reasons.append(
                "Technical conditions are weak."
            )

        else:
            short_reasons.append(
                "There is no sufficiently strong "
                "short-term entry signal."
            )

        # ----------------------------------
        # MEDIUM TERM: 1-6 MONTHS
        # ----------------------------------

        medium_action = "HOLD"
        medium_reasons = []

        if review_required:
            medium_action = "REVIEW"
            medium_reasons.append(
                "Review the investment thesis and risk "
                "before increasing exposure."
            )

        elif data_limited:
            medium_action = "HOLD_PENDING_DATA"
            medium_reasons.append(
                "Do not increase exposure until data "
                "reliability is restored."
            )

        elif (
            fundamental_score >= 70
            and revision_score >= 70
            and technical_score >= 60
        ):
            medium_action = "ACCUMULATE_ON_PULLBACKS"
            medium_reasons.append(
                "Fundamentals, earnings revisions and "
                "trend support a constructive outlook."
            )

        elif (
            fundamental_score < 50
            and revision_score < 50
        ):
            medium_action = "REDUCE_EXPOSURE"
            medium_reasons.append(
                "Fundamental quality and earnings "
                "revisions are both weak."
            )

        else:
            medium_reasons.append(
                "Maintain exposure while monitoring "
                "fundamentals and earnings revisions."
            )

        if risk_score >= 65:
            medium_reasons.append(
                "Elevated risk score requires cautious sizing."
            )

        # ----------------------------------
        # LONG TERM: 1-5 YEARS
        # ----------------------------------

        long_action = "HOLD_AND_MONITOR"
        long_reasons = []

        if review_required:
            long_action = "REASSESS_LONG_TERM_EXPOSURE"
            long_reasons.append(
                "The investment thesis requires review."
            )

        elif thesis_view == "BEARISH":
            long_action = "REASSESS_LONG_TERM_EXPOSURE"
            long_reasons.append(
                "The long-term thesis is bearish."
            )

        elif thesis_view is None:
            long_action = "THESIS_REQUIRED"
            long_reasons.append(
                "A verified long-term thesis is unavailable."
            )

        elif (
            thesis_view == "BULLISH"
            and fundamental_score >= 70
        ):
            long_action = "MAINTAIN_CORE_POSITION"
            long_reasons.append(
                "The long-term thesis is bullish and "
                "fundamental strength is supportive."
            )

        else:
            long_reasons.append(
                "Monitor the long-term thesis "
                "and business performance."
            )

        if data_limited:
            long_reasons.append(
                "Refresh market data before implementing "
                "any increase in portfolio exposure."
            )

        # ----------------------------------
        # REFERENCE LEVELS AND WARNINGS
        # ----------------------------------

        if price is None:
            warnings.append(
                "Current price is missing."
            )

        if support is None or resistance is None:
            warnings.append(
                "Support or resistance is unavailable."
            )

        if (
            support is not None
            and resistance is not None
            and support >= resistance
        ):
            warnings.append(
                "Support and resistance are inconsistent."
            )

        if (
            price is not None
            and ma50 is not None
            and price < ma50
        ):
            warnings.append(
                "Price is below MA50."
            )

        if (
            price is not None
            and ma200 is not None
            and price < ma200
        ):
            warnings.append(
                "Price is below MA200."
            )

        # ----------------------------------
        # FINAL REPORT
        # ----------------------------------

        return {
            "symbol": symbol,
            "engine_version": self.VERSION,
            "created_at_utc": datetime.now(
                timezone.utc
            ).isoformat(),

            "data_quality": {
                "freshness_status": freshness_status,
                "decision_reliability": reliability,
                "limited": data_limited,
                "review_required": review_required,
            },

            "market_summary": {
                "regime": regime,
                "summary": market_summary,
            },

            "long_term_thesis": {
                "view": thesis_view,
                "confidence_pct": thesis_confidence,
            },

            "strategies": {
                "short_term": {
                    "horizon": "1-4 weeks",
                    "action": short_action,
                    "reasons": short_reasons,
                },

                "medium_term": {
                    "horizon": "1-6 months",
                    "action": medium_action,
                    "reasons": medium_reasons,
                },

                "long_term": {
                    "horizon": "1-5 years",
                    "action": long_action,
                    "reasons": long_reasons,
                    "strategic_target_weight_pct": strategic_weight,
                    "current_weight_pct": current_weight,
                },
            },

            "reference_levels": {
                "current_price": price,
                "support": support,
                "resistance": resistance,
                "ma50": ma50,
                "ma200": ma200,
                "rsi14": rsi,
            },

            "warnings": warnings,
            "status": "STRATEGY_READY",
        }
