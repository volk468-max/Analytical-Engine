from aae.engines.market_state import MarketStateEngine
from aae.engines.risk import RiskEngine
from aae.engines.hypothesis import HypothesisEngine
from aae.engines.scenario import ScenarioEngine

def test_market_and_risk():
    summary={"market_trend":"BULLISH","breadth_proxy":"BROAD","vix":16.5,"average_quality_score":100}
    market=MarketStateEngine().evaluate(summary)
    risk=RiskEngine().evaluate(summary,[],market["market_score"])
    assert market["market_state"]=="RISK_ON"
    assert risk["risk_level"] in {"LOW","MODERATE"}

def test_hypotheses_and_scenarios():
    h=HypothesisEngine().build(
        {"market_trend":"BULLISH","breadth_proxy":"BROAD","vix":16},
        "RISK_ON","LOW",[]
    )
    s=ScenarioEngine().build(82,25)
    assert len(h)==2
    assert len(s)==3
    assert round(sum(x.probability for x in s),1)==100.0
