from statistics import mean


class CompanyRiskEngine:
    def evaluate(
        self,
        fundamentals: dict,
        history: dict,
    ) -> dict:
        symbol = str(
            fundamentals.get("symbol", "")
        ).upper()

        records = history.get(
            "records",
            [],
        )

        if len(records) < 200:
            raise ValueError(
                f"Not enough history for {symbol}: "
                f"{len(records)} records."
            )

        records = sorted(
            records,
            key=lambda item: item["trade_date"],
        )

        closes = [
            float(item["close"])
            for item in records
            if item.get("close") is not None
        ]

        if len(closes) < 200:
            raise ValueError(
                f"Not enough valid prices for {symbol}."
            )

        current_price = closes[-1]

        ma200 = mean(
            closes[-200:]
        )

        volatility_annual = (
            self._annualized_volatility(
                closes
            )
        )

        max_drawdown = (
            self._max_drawdown(
                closes
            )
        )

        volatility_risk = (
            self._volatility_risk(
                volatility_annual
            )
        )

        drawdown_risk = (
            self._drawdown_risk(
                max_drawdown
            )
        )

        balance_sheet_risk = (
            self._balance_sheet_risk(
                fundamentals
            )
        )

        valuation_risk = (
            self._valuation_risk(
                fundamentals
            )
        )

        trend_risk = (
            self._trend_risk(
                current_price,
                ma200,
            )
        )

        cash_flow_risk = (
            self._cash_flow_risk(
                fundamentals
            )
        )

        risk_score = round(
            volatility_risk * 0.25
            + drawdown_risk * 0.20
            + balance_sheet_risk * 0.20
            + valuation_risk * 0.15
            + trend_risk * 0.10
            + cash_flow_risk * 0.10,
            1,
        )

        risk_level = (
            self._risk_level(
                risk_score
            )
        )

        risk_factors = []
        protective_factors = []

        if volatility_annual >= 50:
            risk_factors.append(
                f"High annualized volatility: "
                f"{volatility_annual:.1f}%."
            )
        elif volatility_annual <= 25:
            protective_factors.append(
                f"Moderate annualized volatility: "
                f"{volatility_annual:.1f}%."
            )

        if max_drawdown <= -40:
            risk_factors.append(
                f"Large historical drawdown: "
                f"{max_drawdown:.1f}%."
            )
        elif max_drawdown >= -20:
            protective_factors.append(
                f"Limited historical drawdown: "
                f"{max_drawdown:.1f}%."
            )

        cash = self._num(
            fundamentals.get("total_cash")
        )

        debt = self._num(
            fundamentals.get("total_debt")
        )

        if (
            cash is not None
            and debt is not None
        ):
            if cash >= debt:
                protective_factors.append(
                    "Cash covers total debt."
                )
            elif debt > cash * 2:
                risk_factors.append(
                    "Debt is more than twice cash."
                )

        forward_pe = self._num(
            fundamentals.get("forward_pe")
        )

        if (
            forward_pe is not None
            and forward_pe >= 50
        ):
            risk_factors.append(
                f"Elevated forward P/E: "
                f"{forward_pe:.1f}."
            )

        price_to_sales = self._num(
            fundamentals.get("price_to_sales")
        )

        if (
            price_to_sales is not None
            and price_to_sales >= 15
        ):
            risk_factors.append(
                f"High price-to-sales ratio: "
                f"{price_to_sales:.1f}."
            )

        if current_price < ma200:
            risk_factors.append(
                "Price is below MA200."
            )
        else:
            protective_factors.append(
                "Price is above MA200."
            )

        free_cash_flow = self._num(
            fundamentals.get("free_cash_flow")
        )

        if free_cash_flow is not None:
            if free_cash_flow > 0:
                protective_factors.append(
                    "Free cash flow is positive."
                )
            else:
                risk_factors.append(
                    "Free cash flow is negative."
                )

        return {
            "symbol": symbol,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "volatility_risk": volatility_risk,
            "drawdown_risk": drawdown_risk,
            "balance_sheet_risk": (
                balance_sheet_risk
            ),
            "valuation_risk": valuation_risk,
            "trend_risk": trend_risk,
            "cash_flow_risk": cash_flow_risk,
            "annualized_volatility": round(
                volatility_annual,
                2,
            ),
            "max_drawdown": round(
                max_drawdown,
                2,
            ),
            "current_price": round(
                current_price,
                4,
            ),
            "ma200": round(
                ma200,
                4,
            ),
            "risk_factors": risk_factors,
            "protective_factors": (
                protective_factors
            ),
        }

    @staticmethod
    def _annualized_volatility(
        closes: list[float],
    ) -> float:
        returns = []

        for index in range(
            1,
            len(closes),
        ):
            previous = closes[
                index - 1
            ]

            if previous == 0:
                continue

            returns.append(
                closes[index]
                / previous
                - 1
            )

        if len(returns) < 2:
            return 0.0

        average = mean(returns)

        variance = sum(
            (
                value - average
            ) ** 2
            for value in returns
        ) / (
            len(returns) - 1
        )

        daily_volatility = (
            variance ** 0.5
        )

        return (
            daily_volatility
            * (252 ** 0.5)
            * 100
        )

    @staticmethod
    def _max_drawdown(
        closes: list[float],
    ) -> float:
        peak = closes[0]
        max_drawdown = 0.0

        for price in closes:
            if price > peak:
                peak = price

            if peak == 0:
                continue

            drawdown = (
                price / peak - 1
            ) * 100

            if drawdown < max_drawdown:
                max_drawdown = drawdown

        return max_drawdown

    @staticmethod
    def _volatility_risk(
        volatility: float,
    ) -> float:
        if volatility < 20:
            return 20.0
        if volatility < 30:
            return 35.0
        if volatility < 40:
            return 50.0
        if volatility < 50:
            return 65.0
        if volatility < 70:
            return 80.0
        return 95.0

    @staticmethod
    def _drawdown_risk(
        drawdown: float,
    ) -> float:
        magnitude = abs(drawdown)

        if magnitude < 15:
            return 20.0
        if magnitude < 25:
            return 35.0
        if magnitude < 35:
            return 50.0
        if magnitude < 50:
            return 70.0
        if magnitude < 65:
            return 85.0
        return 100.0

    def _balance_sheet_risk(
        self,
        fundamentals: dict,
    ) -> float:
        cash = self._num(
            fundamentals.get("total_cash")
        )

        debt = self._num(
            fundamentals.get("total_debt")
        )

        if cash is None or debt is None:
            return 50.0

        if debt <= 0:
            return 10.0

        ratio = cash / debt

        if ratio >= 1.5:
            return 15.0
        if ratio >= 1.0:
            return 25.0
        if ratio >= 0.5:
            return 45.0
        if ratio >= 0.25:
            return 70.0
        return 90.0

    def _valuation_risk(
        self,
        fundamentals: dict,
    ) -> float:
        risks = []

        forward_pe = self._num(
            fundamentals.get("forward_pe")
        )

        price_to_sales = self._num(
            fundamentals.get("price_to_sales")
        )

        if forward_pe is not None:
            if forward_pe <= 15:
                risks.append(20.0)
            elif forward_pe <= 25:
                risks.append(35.0)
            elif forward_pe <= 40:
                risks.append(55.0)
            elif forward_pe <= 60:
                risks.append(75.0)
            else:
                risks.append(95.0)

        if price_to_sales is not None:
            if price_to_sales <= 3:
                risks.append(20.0)
            elif price_to_sales <= 7:
                risks.append(40.0)
            elif price_to_sales <= 12:
                risks.append(60.0)
            elif price_to_sales <= 20:
                risks.append(80.0)
            else:
                risks.append(95.0)

        if not risks:
            return 50.0

        return round(
            sum(risks)
            / len(risks),
            1,
        )

    @staticmethod
    def _trend_risk(
        current_price: float,
        ma200: float,
    ) -> float:
        if current_price >= ma200 * 1.15:
            return 20.0

        if current_price >= ma200:
            return 35.0

        if current_price >= ma200 * 0.90:
            return 65.0

        return 90.0

    def _cash_flow_risk(
        self,
        fundamentals: dict,
    ) -> float:
        free_cash_flow = self._num(
            fundamentals.get(
                "free_cash_flow"
            )
        )

        if free_cash_flow is None:
            return 50.0

        if free_cash_flow > 0:
            return 20.0

        return 90.0

    @staticmethod
    def _risk_level(
        score: float,
    ) -> str:
        if score < 30:
            return "LOW"

        if score < 45:
            return "MODERATE"

        if score < 60:
            return "ELEVATED"

        if score < 75:
            return "HIGH"

        return "VERY_HIGH"

    @staticmethod
    def _num(
        value,
    ) -> float | None:
        if value is None:
            return None

        try:
            return float(value)

        except (
            TypeError,
            ValueError,
        ):
            return None
