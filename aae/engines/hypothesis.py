from aae.models.analysis import Hypothesis

class HypothesisEngine:
    def build(self, summary: dict, market_state: str, risk_level: str, knowledge: list[dict]):
        bull_support, bull_opp, bear_support, bear_opp = [], [], [], []
        if summary.get("market_trend")=="BULLISH":
            bull_support.append("Market trend is bullish.")
            bear_opp.append("Trend remains positive.")
        else:
            bear_support.append(f"Market trend is {summary.get('market_trend')}.")
        if summary.get("breadth_proxy")=="BROAD":
            bull_support.append("Breadth is broad.")
        elif summary.get("breadth_proxy")=="NARROW":
            bear_support.append("Breadth is narrow.")
        critical = [x for x in knowledge if float(x.get("importance_score",0) or 0)>=85]
        if critical:
            bear_support.append(f"{len(critical)} critical events are active.")
            bull_opp.append("Critical events increase uncertainty.")
        bull = 60 + (15 if market_state in ("RISK_ON","SELECTIVE_RISK_ON") else 0) - (20 if risk_level in ("HIGH","EXTREME") else 0)
        bull = max(5,min(90,bull))
        return [
            Hypothesis(title="Current trend can continue", probability=float(bull), supporting_factors=bull_support or ["No strong bullish factor."], opposing_factors=bull_opp or ["No major opposition."]),
            Hypothesis(title="Risk conditions can reverse the trend", probability=float(100-bull), supporting_factors=bear_support or ["No strong bearish factor."], opposing_factors=bear_opp or ["No major opposition."]),
        ]
