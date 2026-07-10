from aae.models.analysis import Scenario

class ScenarioEngine:
    def build(self, market_score: float, risk_score: float):
        bull_raw=max(5,market_score-risk_score*.2)
        bear_raw=max(5,risk_score*.65)
        base_raw=max(10,100-bull_raw-bear_raw)
        total=bull_raw+base_raw+bear_raw
        bull=round(bull_raw/total*100,1)
        base=round(base_raw/total*100,1)
        bear=round(100-bull-base,1)
        return [
            Scenario(name="Bull case", probability=bull, description="Trend and breadth remain supportive.", triggers=["Breadth remains broad","VIX remains contained"], invalidation_conditions=["VIX above 30","Breadth deteriorates"]),
            Scenario(name="Base case", probability=base, description="Selective leadership and mixed conditions.", triggers=["No major shock"], invalidation_conditions=["Strong broadening","Sharp risk-off"]),
            Scenario(name="Bear case", probability=bear, description="Risk events trigger defensive conditions.", triggers=["VIX rises","Critical events accumulate"], invalidation_conditions=["Volatility falls","Breadth broadens"]),
        ]
