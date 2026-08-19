class RevisionAnalysisEngine:
    def evaluate(
        self,
        revisions: dict,
    ) -> dict:
        symbol = str(
            revisions.get("symbol", "")
        ).upper()

        eps_current_y = self._num(
            revisions.get("eps_current_y")
        )

        eps_next_y = self._num(
            revisions.get("eps_next_y")
        )

        up_7d = self._int_or_zero(
            revisions.get("up_7d")
        )

        down_7d = self._int_or_zero(
            revisions.get("down_7d")
        )

        up_30d = self._int_or_zero(
            revisions.get("up_30d")
        )

        down_30d = self._int_or_zero(
            revisions.get("down_30d")
        )

        eps_trend_current = self._num(
            revisions.get(
                "eps_trend_current"
            )
        )

        eps_trend_30d_ago = self._num(
            revisions.get(
                "eps_trend_30d_ago"
            )
        )

        number_of_analysts = (
            self._int_or_none(
                revisions.get(
                    "number_of_analysts"
                )
            )
        )

        forward_eps_growth = (
            self._forward_eps_growth(
                eps_current_y,
                eps_next_y,
            )
        )

        estimate_change_30d = (
            self._estimate_change(
                eps_trend_30d_ago,
                eps_trend_current,
            )
        )

        forward_growth_score = (
            self._forward_growth_score(
                forward_eps_growth
            )
        )

        revision_breadth_score = (
            self._revision_breadth_score(
                up_7d=up_7d,
                down_7d=down_7d,
                up_30d=up_30d,
                down_30d=down_30d,
            )
        )

        estimate_trend_score = (
            self._estimate_trend_score(
                estimate_change_30d
            )
        )

        analyst_coverage_score = (
            self._analyst_coverage_score(
                number_of_analysts
            )
        )

        revision_score = round(
            forward_growth_score * 0.35
            + revision_breadth_score * 0.35
            + estimate_trend_score * 0.20
            + analyst_coverage_score * 0.10,
            1,
        )

        supporting_factors = []
        opposing_factors = []

        if forward_eps_growth is not None:
            if forward_eps_growth >= 20:
                supporting_factors.append(
                    (
                        "Strong expected EPS growth: "
                        f"{forward_eps_growth:.1f}%."
                    )
                )

            elif forward_eps_growth >= 5:
                supporting_factors.append(
                    (
                        "Positive expected EPS growth: "
                        f"{forward_eps_growth:.1f}%."
                    )
                )

            elif forward_eps_growth < 0:
                opposing_factors.append(
                    (
                        "Expected EPS contraction: "
                        f"{forward_eps_growth:.1f}%."
                    )
                )

        net_30d = (
            up_30d - down_30d
        )

        if net_30d >= 3:
            supporting_factors.append(
                (
                    "Strong positive analyst revision "
                    f"breadth over 30 days: "
                    f"{up_30d} up vs "
                    f"{down_30d} down."
                )
            )

        elif net_30d > 0:
            supporting_factors.append(
                (
                    "Positive analyst revision "
                    f"breadth over 30 days: "
                    f"{up_30d} up vs "
                    f"{down_30d} down."
                )
            )

        elif net_30d < 0:
            opposing_factors.append(
                (
                    "Negative analyst revision "
                    f"breadth over 30 days: "
                    f"{up_30d} up vs "
                    f"{down_30d} down."
                )
            )

        if estimate_change_30d is not None:
            if estimate_change_30d >= 2:
                supporting_factors.append(
                    (
                        "Consensus EPS estimate "
                        f"increased by "
                        f"{estimate_change_30d:.2f}% "
                        "over 30 days."
                    )
                )

            elif estimate_change_30d > 0:
                supporting_factors.append(
                    (
                        "Consensus EPS estimate "
                        "improved slightly over "
                        "30 days."
                    )
                )

            elif estimate_change_30d <= -2:
                opposing_factors.append(
                    (
                        "Consensus EPS estimate "
                        f"fell by "
                        f"{abs(estimate_change_30d):.2f}% "
                        "over 30 days."
                    )
                )

            elif estimate_change_30d < 0:
                opposing_factors.append(
                    (
                        "Consensus EPS estimate "
                        "weakened slightly over "
                        "30 days."
                    )
                )

        if (
            number_of_analysts is not None
            and number_of_analysts >= 20
        ):
            supporting_factors.append(
                (
                    "Broad analyst coverage: "
                    f"{number_of_analysts} analysts."
                )
            )

        return {
            "symbol": symbol,
            "revision_score": (
                revision_score
            ),
            "forward_growth_score": (
                forward_growth_score
            ),
            "revision_breadth_score": (
                revision_breadth_score
            ),
            "estimate_trend_score": (
                estimate_trend_score
            ),
            "analyst_coverage_score": (
                analyst_coverage_score
            ),
            "forward_eps_growth": (
                self._round_or_none(
                    forward_eps_growth
                )
            ),
            "estimate_change_30d": (
                self._round_or_none(
                    estimate_change_30d
                )
            ),
            "up_7d": up_7d,
            "down_7d": down_7d,
            "up_30d": up_30d,
            "down_30d": down_30d,
            "number_of_analysts": (
                number_of_analysts
            ),
            "supporting_factors": (
                supporting_factors
            ),
            "opposing_factors": (
                opposing_factors
            ),
            "conclusion": self._conclusion(
                revision_score
            ),
        }

    @staticmethod
    def _forward_eps_growth(
        current_eps,
        next_eps,
    ):
        if (
            current_eps is None
            or next_eps is None
            or current_eps == 0
        ):
            return None

        return (
            (
                next_eps
                / abs(current_eps)
            )
            - 1
        ) * 100

    @staticmethod
    def _estimate_change(
        old_value,
        current_value,
    ):
        if (
            old_value is None
            or current_value is None
            or old_value == 0
        ):
            return None

        return (
            (
                current_value
                / abs(old_value)
            )
            - 1
        ) * 100

    @staticmethod
    def _forward_growth_score(
        growth,
    ) -> float:
        if growth is None:
            return 50.0

        if growth >= 40:
            return 100.0

        if growth >= 25:
            return 90.0

        if growth >= 15:
            return 80.0

        if growth >= 8:
            return 70.0

        if growth >= 3:
            return 60.0

        if growth >= 0:
            return 50.0

        if growth >= -10:
            return 35.0

        return 20.0

    @staticmethod
    def _revision_breadth_score(
        up_7d: int,
        down_7d: int,
        up_30d: int,
        down_30d: int,
    ) -> float:
        net_7d = (
            up_7d - down_7d
        )

        net_30d = (
            up_30d - down_30d
        )

        score = 50.0

        if net_30d >= 6:
            score += 30

        elif net_30d >= 3:
            score += 20

        elif net_30d >= 1:
            score += 10

        elif net_30d <= -6:
            score -= 30

        elif net_30d <= -3:
            score -= 20

        elif net_30d <= -1:
            score -= 10

        if net_7d >= 3:
            score += 15

        elif net_7d >= 1:
            score += 8

        elif net_7d <= -3:
            score -= 15

        elif net_7d <= -1:
            score -= 8

        return max(
            0.0,
            min(
                100.0,
                score,
            ),
        )

    @staticmethod
    def _estimate_trend_score(
        change,
    ) -> float:
        if change is None:
            return 50.0

        if change >= 5:
            return 100.0

        if change >= 2:
            return 90.0

        if change >= 1:
            return 80.0

        if change > 0:
            return 65.0

        if change == 0:
            return 50.0

        if change > -1:
            return 40.0

        if change > -2:
            return 30.0

        if change > -5:
            return 20.0

        return 10.0

    @staticmethod
    def _analyst_coverage_score(
        analysts,
    ) -> float:
        if analysts is None:
            return 50.0

        if analysts >= 30:
            return 100.0

        if analysts >= 20:
            return 90.0

        if analysts >= 10:
            return 75.0

        if analysts >= 5:
            return 60.0

        if analysts >= 2:
            return 45.0

        return 30.0

    @staticmethod
    def _num(value):
        if value is None:
            return None

        try:
            return float(value)

        except (
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def _int_or_zero(value):
        if value is None:
            return 0

        try:
            return int(value)

        except (
            TypeError,
            ValueError,
        ):
            return 0

    @staticmethod
    def _int_or_none(value):
        if value is None:
            return None

        try:
            return int(value)

        except (
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def _round_or_none(value):
        if value is None:
            return None

        return round(
            value,
            2,
        )

    @staticmethod
    def _conclusion(
        score: float,
    ) -> str:
        if score >= 85:
            return (
                "Very strong positive "
                "earnings revision profile"
            )

        if score >= 75:
            return (
                "Strong positive "
                "earnings revision profile"
            )

        if score >= 65:
            return (
                "Positive earnings "
                "revision profile"
            )

        if score >= 50:
            return (
                "Neutral earnings "
                "revision profile"
            )

        if score >= 35:
            return (
                "Negative earnings "
                "revision profile"
            )

        return (
            "Very negative earnings "
            "revision profile"
        )
