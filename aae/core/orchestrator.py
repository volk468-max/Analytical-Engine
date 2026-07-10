import asyncio, hashlib, json
from datetime import datetime, timezone

from aae.connectors.adc import ADCConnector
from aae.connectors.knowledge import KnowledgeConnector
from aae.engines.market_state import MarketStateEngine
from aae.engines.risk import RiskEngine
from aae.engines.hypothesis import HypothesisEngine
from aae.engines.scenario import ScenarioEngine
from aae.models.analysis import AnalysisResult
from aae.storage.database import Database
from aae.storage.repository import AnalysisRepository

class AnalyticalOrchestrator:
    def __init__(self,adc_url:str,knowledge_url:str,db_path:str="data/analysis.sqlite3"):
        self.adc=ADCConnector(adc_url)
        self.knowledge=KnowledgeConnector(knowledge_url)
        self.market=MarketStateEngine()
        self.risk=RiskEngine()
        self.hypothesis=HypothesisEngine()
        self.scenario=ScenarioEngine()
        self.repo=AnalysisRepository(Database(db_path))

    async def run(self):
        summary,latest,important=await asyncio.gather(
            self.adc.market_summary(),
            self.knowledge.latest(50),
            self.knowledge.high_importance(70,50),
        )
        market=self.market.evaluate(summary)
        risk=self.risk.evaluate(summary,important,market["market_score"])
        hypotheses=self.hypothesis.build(summary,market["market_state"],risk["risk_level"],important)
        scenarios=self.scenario.build(market["market_score"],risk["risk_score"])
        confidence=round(min(100,float(summary.get("average_quality_score",0) or 0)*.7 + 30),1)
        analysis_id=hashlib.sha256((datetime.now(timezone.utc).isoformat()+json.dumps(summary,sort_keys=True)).encode()).hexdigest()[:24]
        result=AnalysisResult(
            analysis_id=analysis_id,
            market_state=market["market_state"],
            market_score=market["market_score"],
            risk_level=risk["risk_level"],
            risk_score=risk["risk_score"],
            confidence=confidence,
            observations=market["observations"],
            hypotheses=hypotheses,
            scenarios=scenarios,
            conclusion=f"Market state is {market['market_state']} with {risk['risk_level']} risk. Leading hypothesis: {hypotheses[0].title} ({hypotheses[0].probability}%).",
            what_changes_the_view=[
                "Material change in breadth",
                "VIX above 30 or below 17",
                "New critical policy or geopolitical event",
                "ADC data quality deterioration",
            ],
            source_status={
                "adc":"ok",
                "knowledge_engine":"ok",
                "knowledge_records":len(latest),
                "high_importance_records":len(important),
                "trade_date":summary.get("trade_date"),
            }
        )
        self.repo.save(result)
        return result
