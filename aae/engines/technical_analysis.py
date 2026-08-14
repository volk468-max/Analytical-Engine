from statistics import mean


class TechnicalAnalysisEngine:
    def evaluate(
        self,
        history: dict,
    ) -> dict:
        symbol = str(
            history.get("symbol", "")
        ).upper()

        records = history.get(
            "records",
            [],
        )

        if len(records) < 200:
            raise ValueError(
                f"Not enough history for {symbol}: "
                f"{len(records)} records. "
                "At least 200 are required."
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

        highs = [
            float(item["high"])
            for item in records
            if item.get("high") is not None
        ]

        if len(closes) < 200:
            raise ValueError(
                f"Not enough valid closing prices "
                f"for {symbol}."
            )

        current_price = closes[-1]

        ma50 = mean(
            closes[-50:]
        )

        ma200 = mean(
            closes[-200:]
        )

        rsi14 = self._rsi(
            closes,
            period=14,
        )

        momentum_1m = self._momentum(
            closes,
            21,
        )

        momentum_3m = self._momentum(
            closes,
            63,
        )

        momentum_6m = self._momentum(
            closes,
            126,
        )

        momentum_1y = self._momentum(
            closes,
            252,
        )

        lookback_52w = min(
            len(highs),
            252,
        )

        high_52w = max(
            highs[-lookback_52w:]
        )

        distance_from_52w_high = (
            (
                current_price
                / high_52w
            )
            - 1
        ) * 100

        trend_score = self._trend_score(
            current_price=current_price,
            ma50=ma50,
            ma200=ma200,
        )

        momentum_score = (
            self._momentum_score(
                momentum_1m,
                momentum_3m,
                momentum_6m,
                momentum_1y,
            )
        )

        rsi_score = self._rsi_score(
            rsi14
        )

        position_52w_score = (
            self._position_52w_score(
                distance_from_52w_high
            )
        )

        technical_score = round(
            trend_score * 0.35
            + momentum_score * 0.30
            + rsi_score * 0.15
            + position_52w_score * 0.20,
            1,
        )

        supporting_factors = []
        opposing_factors = []

        if current_price > ma50:
            supporting_factors.append(
                "Price is above MA50."
            )
        else:
            opposing_factors.append(
                "Price is below MA50."
            )

        if current_price > ma200:
            supporting_factors.append(
                "Price is above MA200."
            )
        else:
            opposing_factors.append(
                "Price is below MA200."
            )

        if ma50 > ma200:
            supporting_factors.append(
                "MA50 is above MA200."
            )
        else:
            opposing_factors.append(
                "MA50 is below MA200."
            )

        if momentum_3m is not None:
            if momentum_3m > 0:
                supporting_factors.append(
                    f"3M momentum is positive: "
                    f"{momentum_3m:.1f}%."
                )
            else:
                opposing_factors.append(
                    f"3M momentum is negative: "
                    f"{momentum_3m:.1f}%."
                )

        if rsi14 >= 70:
            opposing_factors.append(
                f"RSI is elevated: {rsi14:.1f}."
            )

        elif rsi14 <= 30:
            opposing_factors.append(
                f"RSI is weak: {rsi14:.1f}."
            )

        elif 45 <= rsi14 <= 65:
            supporting_factors.append(
                f"RSI is constructive: "
                f"{rsi14:.1f}."
            )

        if distance_from_52w_high >= -10:
            supporting_factors.append(
                "Price is within 10% of "
                "the 52-week high."
            )

        elif distance_from_52w_high <= -30:
            opposing_factors.append(
                "Price is more than 30% below "
                "the 52-week high."
            )

        return {
            "symbol": symbol,
            "technical_score": technical_score,
            "trend_score": trend_score,
            "momentum_score": momentum_score,
            "rsi_score": rsi_score,
            "position_52w_score": position_52w_score,
            "current_price": round(
                current_price,
                4,
            ),
            "ma50": round(
                ma50,
                4,
            ),
            "ma200": round(
                ma200,
                4,
            ),
            "rsi14": round(
                rsi14,
                2,
            ),
            "momentum_1m": self._round_or_none(
                momentum_1m
            ),
            "momentum_3m": self._round_or_none(
                momentum_3m
            ),
            "momentum_6m": self._round_or_none(
                momentum_6m
            ),
            "momentum_1y": self._round_or_none(
                momentum_1y
            ),
            "high_52w": round(
                high_52w,
                4,
            ),
            "distance_from_52w_high": round(
                distance_from_52w_high,
                2,
            ),
            "supporting_factors": (
                supporting_factors
            ),
            "opposing_factors": (
                opposing_factors
            ),
            "conclusion": self._conclusion(
                technical_score
            ),
        }

    @staticmethod
    def _momentum(
        closes: list[float],
        periods: int,
    ) -> float | None:
        if len(closes) <= periods:
            return None

        old_price = closes[
            -(periods + 1)
        ]

        if old_price == 0:
            return None

        return (
            (
                closes[-1]
                / old_price
            )
            - 1
        ) * 100

    @staticmethod
    def _rsi(
        closes: list[float],
        period: int = 14,
    ) -> float:
        if len(closes) <= period:
            return 50.0

        changes = [
            closes[index]
            - closes[index - 1]
            for index in range(
                len(closes) - period,
                len(closes),
            )
        ]

        gains = [
            max(change, 0)
            for change in changes
        ]

        losses = [
            abs(min(change, 0))
            for change in changes
        ]

        average_gain = mean(gains)
        average_loss = mean(losses)

        if average_loss == 0:
            return 100.0

        rs = (
            average_gain
            / average_loss
        )

        return 100 - (
            100
            / (1 + rs)
        )

    @staticmethod
    def _trend_score(
        current_price: float,
        ma50: float,
        ma200: float,
    ) -> float:
        score = 0.0

        if current_price > ma50:
            score += 35
        else:
            score += 10

        if current_price > ma200:
            score += 35
        else:
            score += 10

        if ma50 > ma200:
            score += 30
        else:
            score += 10

        return min(
            score,
            100.0,
        )

    @staticmethod
    def _momentum_score(
        momentum_1m,
        momentum_3m,
        momentum_6m,
        momentum_1y,
    ) -> float:
        values = [
            (
                momentum_1m,
                0.15,
            ),
            (
                momentum_3m,
                0.30,
            ),
            (
                momentum_6m,
                0.30,
            ),
            (
                momentum_1y,
                0.25,
            ),
        ]

        total_score = 0.0
        total_weight = 0.0

        for value, weight in values:
            if value is None:
                continue

            if value >= 40:
                score = 100

            elif value >= 25:
                score = 90

            elif value >= 15:
                score = 80

            elif value >= 8:
                score = 70

            elif value >= 3:
                score = 60

            elif value >= 0:
                score = 50

            elif value >= -5:
                score = 40

            elif value >= -15:
                score = 25

            else:
                score = 10

            total_score += (
                score * weight
            )

            total_weight += weight

        if total_weight == 0:
            return 50.0

        return round(
            total_score
            / total_weight,
            1,
        )

    @staticmethod
    def _rsi_score(
        rsi: float,
    ) -> float:
        if 50 <= rsi <= 65:
            return 100.0

        if 45 <= rsi < 50:
            return 90.0

        if 65 < rsi <= 70:
            return 85.0

        if 40 <= rsi < 45:
            return 75.0

        if 70 < rsi <= 75:
            return 65.0

        if 30 <= rsi < 40:
            return 55.0

        if 75 < rsi <= 80:
            return 45.0

        if rsi < 30:
            return 30.0

        return 25.0

    @staticmethod
    def _position_52w_score(
        distance: float,
    ) -> float:
        if distance >= -3:
            return 100.0

        if distance >= -7:
            return 90.0

        if distance >= -12:
            return 80.0

        if distance >= -20:
            return 65.0

        if distance >= -30:
            return 50.0

        if distance >= -40:
            return 35.0

        return 20.0

    @staticmethod
    def _round_or_none(
        value,
    ):
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
            return "Very strong technical profile"

        if score >= 75:
            return "Strong technical profile"

        if score >= 65:
            return "Positive technical profile"

        if score >= 55:
            return "Neutral technical profile"

        if score >= 40:
            return "Weak technical profile"

        return "Very weak technical profile"
