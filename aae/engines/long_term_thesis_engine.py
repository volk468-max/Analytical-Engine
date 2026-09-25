from typing import Any


class LongTermThesisEngine:
    VERSION = "Long-Term-Thesis-Engine-v1"

    THESIS_MAP = {
        "NVDA": {
            "view": "STRONG_BULLISH",
            "confidence_pct": 84,
            "strategic_target_weight_pct": 5.5,
            "role": "CORE",
            "thesis": (
                "AI compute and networking leadership. "
                "Primary beneficiary of continued AI infrastructure buildout."
            ),
            "key_drivers": [
                "AI accelerator demand",
                "Data center growth",
                "Networking growth",
                "Software ecosystem",
            ],
            "key_risks": [
                "Valuation compression",
                "Hyperscaler capex slowdown",
                "Competitive pressure",
            ],
        },

        "AMD": {
            "view": "BULLISH",
            "confidence_pct": 77,
            "strategic_target_weight_pct": 5.0,
            "role": "CORE_GROWTH",
            "thesis": (
                "Second major AI compute platform with potential share gains "
                "in data center CPU and AI accelerators."
            ),
            "key_drivers": [
                "Instinct accelerator growth",
                "EPYC share gains",
                "AI infrastructure demand",
            ],
            "key_risks": [
                "NVIDIA dominance",
                "Execution risk",
                "Valuation compression",
            ],
        },

        "TSM": {
            "view": "STRONG_BULLISH",
            "confidence_pct": 85,
            "strategic_target_weight_pct": 4.0,
            "role": "CORE",
            "thesis": (
                "Critical advanced-node foundry beneficiary regardless of "
                "which AI chip designer wins."
            ),
            "key_drivers": [
                "Advanced node demand",
                "AI accelerator production",
                "Leading-edge process leadership",
            ],
            "key_risks": [
                "Geopolitical risk",
                "Capital intensity",
                "Semiconductor cycle",
            ],
        },

        "AVGO": {
            "view": "STRONG_BULLISH",
            "confidence_pct": 81,
            "strategic_target_weight_pct": 3.5,
            "role": "CORE",
            "thesis": (
                "AI networking and custom accelerator exposure combined "
                "with infrastructure software cash flow."
            ),
            "key_drivers": [
                "AI networking",
                "Custom silicon",
                "Data center connectivity",
            ],
            "key_risks": [
                "Customer concentration",
                "Valuation",
                "AI capex slowdown",
            ],
        },

        "MU": {
            "view": "BULLISH",
            "confidence_pct": 75,
            "strategic_target_weight_pct": 5.0,
            "role": "GROWTH_CYCLICAL",
            "thesis": (
                "HBM and advanced memory are essential components "
                "of AI compute infrastructure."
            ),
            "key_drivers": [
                "HBM demand",
                "Memory pricing",
                "AI server growth",
            ],
            "key_risks": [
                "Memory cycle",
                "Pricing volatility",
                "Capacity expansion",
            ],
        },

        "AMAT": {
            "view": "BULLISH",
            "confidence_pct": 76,
            "strategic_target_weight_pct": 2.8,
            "role": "CORE_INFRASTRUCTURE",
            "thesis": (
                "Increasing semiconductor complexity supports sustained "
                "demand for wafer fabrication equipment."
            ),
            "key_drivers": [
                "Advanced process complexity",
                "Fab capex",
                "AI semiconductor investment",
            ],
            "key_risks": [
                "Semiconductor capex cycle",
                "China restrictions",
            ],
        },

        "LRCX": {
            "view": "BULLISH",
            "confidence_pct": 75,
            "strategic_target_weight_pct": 2.2,
            "role": "CORE_INFRASTRUCTURE",
            "thesis": (
                "Etch and deposition intensity rises with advanced logic "
                "and memory complexity."
            ),
            "key_drivers": [
                "Advanced memory",
                "HBM",
                "Leading-edge logic",
            ],
            "key_risks": [
                "Semiconductor capex cycle",
                "China exposure",
            ],
        },

        "AMZN": {
            "view": "BULLISH",
            "confidence_pct": 76,
            "strategic_target_weight_pct": 2.5,
            "role": "CORE_GROWTH",
            "thesis": (
                "AWS and AI cloud demand provide long-term growth, "
                "supported by proprietary AI infrastructure."
            ),
            "key_drivers": [
                "AWS growth",
                "AI cloud adoption",
                "Custom AI chips",
            ],
            "key_risks": [
                "High capex",
                "Free cash flow pressure",
                "Cloud competition",
            ],
        },

        "META": {
            "view": "BULLISH",
            "confidence_pct": 70,
            "strategic_target_weight_pct": 2.3,
            "role": "GROWTH",
            "thesis": (
                "AI can improve advertising monetization and engagement, "
                "but returns on very large AI capex must be demonstrated."
            ),
            "key_drivers": [
                "Ad monetization",
                "AI recommendation systems",
                "Operating leverage",
            ],
            "key_risks": [
                "AI capex returns",
                "Margin pressure",
                "Regulatory risk",
            ],
        },

        "PLTR": {
            "view": "BULLISH",
            "confidence_pct": 69,
            "strategic_target_weight_pct": 1.2,
            "role": "OPPORTUNISTIC",
            "thesis": (
                "Strong AI software monetization potential, but valuation "
                "and rerating risk justify a smaller strategic allocation."
            ),
            "key_drivers": [
                "Enterprise AI adoption",
                "Government demand",
                "Operating leverage",
            ],
            "key_risks": [
                "Valuation",
                "Sentiment reversal",
                "Rerating risk",
            ],
        },

        "NBIS": {
            "view": "BULLISH_HIGH_RISK",
            "confidence_pct": 64,
            "strategic_target_weight_pct": 2.4,
            "role": "OPPORTUNISTIC",
            "thesis": (
                "High-growth AI infrastructure and cloud exposure "
                "with significant execution and capital intensity risk."
            ),
            "key_drivers": [
                "AI cloud demand",
                "GPU infrastructure expansion",
                "Capacity growth",
            ],
            "key_risks": [
                "Execution",
                "Financing",
                "Capital intensity",
                "Competition",
            ],
        },
    }

    def evaluate(
        self,
        symbol: str,
        current_weight_pct: float | None = None,
    ) -> dict[str, Any]:

        symbol = symbol.upper()

        thesis = self.THESIS_MAP.get(symbol)

        if thesis is None:
            return {
                "symbol": symbol,
                "status": "NO_LONG_TERM_THESIS",
                "engine_version": self.VERSION,
            }

        target = thesis["strategic_target_weight_pct"]

        weight_gap = None
        weight_status = None

        if current_weight_pct is not None:
            weight_gap = round(
                current_weight_pct - target,
                2,
            )

            if current_weight_pct > target * 1.15:
                weight_status = "STRATEGIC_OVERWEIGHT"

            elif current_weight_pct < target * 0.85:
                weight_status = "STRATEGIC_UNDERWEIGHT"

            else:
                weight_status = "NEAR_STRATEGIC_TARGET"

        return {
            "symbol": symbol,
            "long_term_view": thesis["view"],
            "confidence_pct": thesis["confidence_pct"],
            "role": thesis["role"],
            "strategic_target_weight_pct": target,
            "current_weight_pct": current_weight_pct,
            "weight_gap_pct": weight_gap,
            "weight_status": weight_status,
            "thesis": thesis["thesis"],
            "key_drivers": thesis["key_drivers"],
            "key_risks": thesis["key_risks"],
            "engine_version": self.VERSION,
            "status": "LONG_TERM_THESIS_READY",
        }
