
from datetime import datetime, timezone
from typing import Any
import math


class InvestmentReturnEngine:
    VERSION = "Investment-Return-Engine-v1.0"

    DEFAULT_SCENARIOS = {
        "bear": {
            "eps_growth": 0.05,
            "terminal_pe": 18.0,
            "weight": 0.25,
        },
        "base": {
            "eps_growth": 0.20,
            "terminal_pe": 30.0,
            "weight": 0.50,
        },
        "bull": {
            "eps_growth": 0.35,
            "terminal_pe": 45.0,
            "weight": 0.25,
        },
    }

    def evaluate(
        self,
        symbol: str,
        current_price: float,
        fundamentals: dict[str, Any],
        revisions: dict[str, Any],
        years: int = 5,
        target_cagr: float = 0.30,
        scenarios: dict | None = None,
    ) -> dict[str, Any]:

        symbol = symbol.upper()

        warnings = []

        price = self._positive(current_price)

        eps_next_y = self._positive(
            revisions.get("eps_next_y")
        )

        eps_current_y = self._positive(
            revisions.get("eps_current_y")
        )

        forward_pe = self._positive(
            fundamentals.get("forward_pe")
        )

        if price is None or eps_next_y is None:
            return {
                "symbol": symbol,
                "engine_version": self.VERSION,
                "status": "INSUFFICIENT_DATA",
                "warnings": [
                    "Valid current price and next-year EPS "
                    "forecast are required."
                ],
            }

        if not isinstance(years, int) or years < 1:
            raise ValueError("years must be >= 1")

        if not math.isfinite(target_cagr) or target_cagr <= -1:
            raise ValueError("Invalid target CAGR")

        scenario_inputs = (
            scenarios
            if scenarios is not None
            else self.DEFAULT_SCENARIOS
        )

        if not scenario_inputs:
            raise ValueError("No scenarios supplied")

        total_weight = 0.0

        for params in scenario_inputs.values():
            weight = float(params["weight"])

            if not math.isfinite(weight) or weight < 0:
                raise ValueError("Invalid scenario weight")

            total_weight += weight

        if not math.isclose(
            total_weight, 1.0, abs_tol=0.000001
        ):
            raise ValueError(
                "Scenario weights must sum to 1.0"
            )

        if eps_current_y is not None:
            eps_growth_next_year = (
                eps_next_y / eps_current_y - 1
            )
        else:
            eps_growth_next_year = None

        if forward_pe is not None:
            implied_forward_pe = price / eps_next_y

            discrepancy_pct = (
                implied_forward_pe / forward_pe - 1
            ) * 100

            if abs(discrepancy_pct) > 10:
                warnings.append(
                    "Forward P/E differs materially "
                    "from price divided by next-year EPS."
                )
        else:
            implied_forward_pe = price / eps_next_y

        results = {}

        weighted_terminal_price = 0.0

        for name, params in scenario_inputs.items():

            growth = float(params["eps_growth"])
            terminal_pe = float(params["terminal_pe"])
            weight = float(params["weight"])

            if (
                not math.isfinite(growth)
                or growth <= -1
                or not math.isfinite(terminal_pe)
                or terminal_pe <= 0
            ):
                raise ValueError(
                    f"Invalid assumptions for {name}"
                )

            # Next-year EPS is the forecast for year 1.
            # Growth applies from year 2 through year N.

            future_eps = (
                eps_next_y
                * (1 + growth) ** (years - 1)
            )

            target_price = future_eps * terminal_pe

            total_return = (
                target_price / price - 1
            )

            cagr = (
                (target_price / price) ** (1 / years)
                - 1
            )

            max_entry_price = (
                target_price
                / (1 + target_cagr) ** years
            )

            weighted_terminal_price += (
                target_price * weight
            )

            results[name] = {
                "weight_pct": round(weight * 100, 2),
                "annual_eps_growth_pct": round(
                    growth * 100, 2
                ),
                "terminal_pe": round(terminal_pe, 2),
                "future_eps": round(future_eps, 4),
                "target_price": round(
                    target_price, 2
                ),
                "total_return_pct": round(
                    total_return * 100, 2
                ),
                "cagr_pct": round(cagr * 100, 2),
                "max_entry_price_for_target_cagr": round(
                    max_entry_price, 2
                ),
            }

        weighted_total_return = (
            weighted_terminal_price / price - 1
        )

        weighted_terminal_cagr = (
            (weighted_terminal_price / price)
            ** (1 / years)
            - 1
        )

        max_entry_price_weighted = (
            weighted_terminal_price
            / (1 + target_cagr) ** years
        )

        if scenarios is None:
            warnings.append(
                "Scenario growth rates, terminal P/E "
                "and weights are illustrative assumptions, "
                "not calibrated forecasts."
            )

        warnings.append(
            "The model excludes dividends, dilution, "
            "taxes, fees and intermediate cash flows."
        )

        return {
            "symbol": symbol,
            "engine_version": self.VERSION,
            "created_at_utc": (
                datetime.now(timezone.utc).isoformat()
            ),
            "status": "SCENARIO_ESTIMATE_READY",
            "current_price": round(price, 4),
            "forecast_eps_current_year": eps_current_y,
            "forecast_eps_next_year": eps_next_y,
            "next_year_eps_growth_pct": (
                round(eps_growth_next_year * 100, 2)
                if eps_growth_next_year is not None
                else None
            ),
            "forward_pe": forward_pe,
            "implied_forward_pe": round(
                implied_forward_pe, 2
            ),
            "horizon_years": years,
            "target_cagr_pct": round(
                target_cagr * 100, 2
            ),
            "scenarios": results,
            "weighted_scenario": {
                "terminal_price": round(
                    weighted_terminal_price, 2
                ),
                "total_return_pct": round(
                    weighted_total_return * 100, 2
                ),
                "terminal_value_cagr_pct": round(
                    weighted_terminal_cagr * 100, 2
                ),
                "max_entry_price_for_target_cagr": round(
                    max_entry_price_weighted, 2
                ),
            },
            "assumptions_status": (
                "USER_SUPPLIED"
                if scenarios is not None
                else "ILLUSTRATIVE_DEFAULTS"
            ),
            "warnings": warnings,
        }

    @staticmethod
    def _positive(value):
        try:
            number = float(value)

            if math.isfinite(number) and number > 0:
                return number

        except (TypeError, ValueError, OverflowError):
            pass

        return None
