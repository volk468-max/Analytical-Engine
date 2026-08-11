from aae.models.analysis import CompanyAnalysisResult


class CompanyAnalysisEngine:
    def evaluate(
        self,
        fundamentals: dict,
    ) -> CompanyAnalysisResult:
        symbol = str(
            fundamentals.get("symbol", "")
        ).upper()

        company_name = (
            fundamentals.get("name")
            or symbol
        )

        supporting_factors = []
        opposing_factors = []

        growth_score = self._growth_score(
            fundamentals,
            supporting_factors,
            opposing_factors,
        )

        valuation_score = self._valuation_score(
            fundamentals,
            supporting_factors,
            opposing_factors,
        )

        quality_score = self._quality_score(
            fundamentals,
            supporting_factors,
            opposing_factors,
        )

        balance_sheet_score = (
            self._balance_sheet_score(
                fundamentals,
                supporting_factors,
                opposing_factors,
            )
        )

        fundamental_score = round(
            (
                growth_score * 0.30
                + valuation_score * 0.20
                + quality_score * 0.30
                + balance_sheet_score * 0.20
            ),
            1,
        )

        conclusion = self._conclusion(
            fundamental_score
        )

        return CompanyAnalysisResult(
            symbol=symbol,
            company_name=company_name,
            fundamental_score=fundamental_score,
            growth_score=growth_score,
            valuation_score=valuation_score,
            quality_score=quality_score,
            balance_sheet_score=balance_sheet_score,
            fundamentals=fundamentals,
            supporting_factors=supporting_factors,
            opposing_factors=opposing_factors,
            conclusion=conclusion,
        )

    def _growth_score(
        self,
        f: dict,
        supporting: list[str],
        opposing: list[str],
    ) -> float:
        scores = []

        revenue_growth = self._num(
            f.get("revenue_growth")
        )

        earnings_growth = self._num(
            f.get("earnings_growth")
        )

        if revenue_growth is not None:
            score = self._growth_metric_score(
                revenue_growth
            )
            scores.append(score)

            if revenue_growth >= 0.20:
                supporting.append(
                    f"Strong revenue growth: "
                    f"{revenue_growth * 100:.1f}%."
                )
            elif revenue_growth < 0:
                opposing.append(
                    f"Revenue is contracting: "
                    f"{revenue_growth * 100:.1f}%."
                )

        if earnings_growth is not None:
            score = self._growth_metric_score(
                earnings_growth
            )
            scores.append(score)

            if earnings_growth >= 0.20:
                supporting.append(
                    f"Strong earnings growth: "
                    f"{earnings_growth * 100:.1f}%."
                )
            elif earnings_growth < 0:
                opposing.append(
                    f"Earnings are contracting: "
                    f"{earnings_growth * 100:.1f}%."
                )

        return self._average_or_neutral(scores)

    def _valuation_score(
        self,
        f: dict,
        supporting: list[str],
        opposing: list[str],
    ) -> float:
        scores = []

        trailing_pe = self._num(
            f.get("trailing_pe")
        )

        forward_pe = self._num(
            f.get("forward_pe")
        )

        price_to_sales = self._num(
            f.get("price_to_sales")
        )

        if trailing_pe is not None:
            scores.append(
                self._pe_score(trailing_pe)
            )

            if trailing_pe <= 20:
                supporting.append(
                    f"Trailing P/E is moderate: "
                    f"{trailing_pe:.1f}."
                )
            elif trailing_pe >= 50:
                opposing.append(
                    f"Trailing P/E is elevated: "
                    f"{trailing_pe:.1f}."
                )

        if forward_pe is not None:
            scores.append(
                self._pe_score(forward_pe)
            )

            if forward_pe < (
                trailing_pe
                if trailing_pe is not None
                else float("inf")
            ):
                supporting.append(
                    f"Forward P/E ({forward_pe:.1f}) "
                    f"is below trailing P/E."
                )

        if price_to_sales is not None:
            scores.append(
                self._ps_score(price_to_sales)
            )

            if price_to_sales >= 15:
                opposing.append(
                    f"Price-to-sales is high: "
                    f"{price_to_sales:.1f}."
                )

        return self._average_or_neutral(scores)

    def _quality_score(
        self,
        f: dict,
        supporting: list[str],
        opposing: list[str],
    ) -> float:
        scores = []

        gross_margin = self._num(
            f.get("gross_margin")
        )

        operating_margin = self._num(
            f.get("operating_margin")
        )

        profit_margin = self._num(
            f.get("profit_margin")
        )

        roe = self._num(
            f.get("return_on_equity")
        )

        roa = self._num(
            f.get("return_on_assets")
        )

        if gross_margin is not None:
            scores.append(
                self._margin_score(
                    gross_margin,
                    excellent=0.60,
                    good=0.40,
                    weak=0.20,
                )
            )

            if gross_margin >= 0.60:
                supporting.append(
                    f"Very strong gross margin: "
                    f"{gross_margin * 100:.1f}%."
                )

        if operating_margin is not None:
            scores.append(
                self._margin_score(
                    operating_margin,
                    excellent=0.30,
                    good=0.20,
                    weak=0.10,
                )
            )

            if operating_margin >= 0.30:
                supporting.append(
                    f"Strong operating margin: "
                    f"{operating_margin * 100:.1f}%."
                )

        if profit_margin is not None:
            scores.append(
                self._margin_score(
                    profit_margin,
                    excellent=0.25,
                    good=0.15,
                    weak=0.05,
                )
            )

            if profit_margin >= 0.25:
                supporting.append(
                    f"Strong net margin: "
                    f"{profit_margin * 100:.1f}%."
                )

        if roe is not None:
            scores.append(
                self._return_score(roe)
            )

            if roe >= 0.25:
                supporting.append(
                    f"High ROE: "
                    f"{roe * 100:.1f}%."
                )

        if roa is not None:
            scores.append(
                self._return_score(
                    roa,
                    strong=0.15,
                    good=0.08,
                    weak=0.03,
                )
            )

        return self._average_or_neutral(scores)

    def _balance_sheet_score(
        self,
        f: dict,
        supporting: list[str],
        opposing: list[str],
    ) -> float:
        scores = []

        cash = self._num(
            f.get("total_cash")
        )

        debt = self._num(
            f.get("total_debt")
        )

        free_cash_flow = self._num(
            f.get("free_cash_flow")
        )

        if cash is not None and debt is not None:
            if debt <= 0:
                cash_debt_score = 100.0
            else:
                ratio = cash / debt

                if ratio >= 1.5:
                    cash_debt_score = 100.0
                elif ratio >= 1.0:
                    cash_debt_score = 85.0
                elif ratio >= 0.5:
                    cash_debt_score = 65.0
                elif ratio >= 0.25:
                    cash_debt_score = 45.0
                else:
                    cash_debt_score = 25.0

            scores.append(cash_debt_score)

            if cash >= debt:
                supporting.append(
                    "Cash covers total debt."
                )
            elif debt > cash * 2:
                opposing.append(
                    "Debt is more than twice cash."
                )

        if free_cash_flow is not None:
            if free_cash_flow > 0:
                scores.append(85.0)
                supporting.append(
                    "Free cash flow is positive."
                )
            else:
                scores.append(20.0)
                opposing.append(
                    "Free cash flow is negative."
                )

        return self._average_or_neutral(scores)

    @staticmethod
    def _growth_metric_score(
        value: float,
    ) -> float:
        if value >= 0.40:
            return 100.0
        if value >= 0.25:
            return 90.0
        if value >= 0.15:
            return 80.0
        if value >= 0.08:
            return 70.0
        if value >= 0.03:
            return 60.0
        if value >= 0:
            return 50.0
        if value >= -0.10:
            return 35.0
        return 20.0

    @staticmethod
    def _pe_score(
        value: float,
    ) -> float:
        if value <= 0:
            return 35.0
        if value <= 15:
            return 90.0
        if value <= 20:
            return 85.0
        if value <= 25:
            return 75.0
        if value <= 35:
            return 65.0
        if value <= 50:
            return 50.0
        if value <= 75:
            return 35.0
        return 20.0

    @staticmethod
    def _ps_score(
        value: float,
    ) -> float:
        if value <= 2:
            return 90.0
        if value <= 5:
            return 80.0
        if value <= 10:
            return 65.0
        if value <= 15:
            return 50.0
        if value <= 25:
            return 35.0
        return 20.0

    @staticmethod
    def _margin_score(
        value: float,
        excellent: float,
        good: float,
        weak: float,
    ) -> float:
        if value >= excellent:
            return 100.0
        if value >= good:
            return 85.0
        if value >= weak:
            return 65.0
        if value >= 0:
            return 45.0
        return 20.0

    @staticmethod
    def _return_score(
        value: float,
        strong: float = 0.25,
        good: float = 0.15,
        weak: float = 0.05,
    ) -> float:
        if value >= strong:
            return 100.0
        if value >= good:
            return 85.0
        if value >= weak:
            return 65.0
        if value >= 0:
            return 45.0
        return 20.0

    @staticmethod
    def _average_or_neutral(
        scores: list[float],
    ) -> float:
        if not scores:
            return 50.0

        return round(
            sum(scores) / len(scores),
            1,
        )

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
    def _conclusion(
        score: float,
    ) -> str:
        if score >= 85:
            return "Exceptional fundamental profile"

        if score >= 75:
            return "Strong fundamental profile"

        if score >= 65:
            return "Good fundamental profile"

        if score >= 55:
            return "Mixed but acceptable fundamental profile"

        if score >= 40:
            return "Weak fundamental profile"

        return "High fundamental risk"
