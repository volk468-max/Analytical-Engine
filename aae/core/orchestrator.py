import asyncio
import hashlib
import json
from datetime import datetime, timezone

from aae.connectors.adc import ADCConnector
from aae.connectors.knowledge import KnowledgeConnector
from aae.connectors.hypothesis_tracker import (
    HypothesisTrackerConnector,
)
from aae.engines.market_state import MarketStateEngine
from aae.engines.risk import RiskEngine
from aae.engines.hypothesis import HypothesisEngine
from aae.engines.scenario import ScenarioEngine
from aae.models.analysis import AnalysisResult
from aae.storage.database import Database
from aae.storage.repository import AnalysisRepository


class AnalyticalOrchestrator:
    def __init__(
        self,
        adc_url: str,
        knowledge_url: str,
        hypothesis_tracker_url: str | None = None,
        db_path: str = "data/analysis.sqlite3",
    ):
        self.adc = ADCConnector(adc_url)
        self.knowledge = KnowledgeConnector(knowledge_url)

        self.hypothesis_tracker = (
            HypothesisTrackerConnector(
                hypothesis_tracker_url
            )
            if hypothesis_tracker_url
            else None
        )

        self.market = MarketStateEngine()
        self.risk = RiskEngine()
        self.hypothesis = HypothesisEngine()
        self.scenario = ScenarioEngine()

        self.repo = AnalysisRepository(
            Database(db_path)
        )

    async def run(self) -> AnalysisResult:
        # Одновременно получаем данные из ADC
        # и Knowledge Engine.
        summary, latest, important = await asyncio.gather(
            self.adc.market_summary(),
            self.knowledge.latest(50),
            self.knowledge.high_importance(
                70,
                50,
            ),
        )

        # Определяем состояние рынка.
        market = self.market.evaluate(summary)

        # Рассчитываем риск.
        risk = self.risk.evaluate(
            summary,
            important,
            market["market_score"],
        )

        # Формируем конкурирующие гипотезы.
        hypotheses = self.hypothesis.build(
            summary,
            market["market_state"],
            risk["risk_level"],
            important,
        )

        # Формируем сценарии.
        scenarios = self.scenario.build(
            market["market_score"],
            risk["risk_score"],
        )

        confidence = round(
            min(
                100,
                float(
                    summary.get(
                        "average_quality_score",
                        0,
                    )
                    or 0
                )
                * 0.7
                + 30,
            ),
            1,
        )

        # Analysis ID создается до отправки гипотез
        # в Tracker, чтобы сохранить происхождение.
        analysis_id = hashlib.sha256(
            (
                datetime.now(
                    timezone.utc
                ).isoformat()
                + json.dumps(
                    summary,
                    sort_keys=True,
                )
            ).encode("utf-8")
        ).hexdigest()[:24]

        tracking_results = await self._register_hypotheses(
            hypotheses=hypotheses,
            analysis_id=analysis_id,
        )

        result = AnalysisResult(
            analysis_id=analysis_id,
            market_state=market["market_state"],
            market_score=market["market_score"],
            risk_level=risk["risk_level"],
            risk_score=risk["risk_score"],
            confidence=confidence,
            observations=market["observations"],
            hypotheses=hypotheses,
            scenarios=scenarios,
            conclusion=(
                f"Market state is "
                f"{market['market_state']} with "
                f"{risk['risk_level']} risk. "
                f"Leading hypothesis: "
                f"{hypotheses[0].title} "
                f"({hypotheses[0].probability}%)."
            ),
            what_changes_the_view=[
                "Material change in breadth",
                "VIX above 30 or below 17",
                (
                    "New critical policy or "
                    "geopolitical event"
                ),
                "ADC data quality deterioration",
            ],
            source_status={
                "adc": "ok",
                "knowledge_engine": "ok",
                "knowledge_records": len(latest),
                "high_importance_records": len(
                    important
                ),
                "trade_date": summary.get(
                    "trade_date"
                ),
                "hypothesis_tracking": (
                    tracking_results
                ),
            },
        )

        # Анализ сохраняется независимо от того,
        # сработал Tracker или нет.
        self.repo.save(result)

        return result

    async def _register_hypotheses(
        self,
        hypotheses,
        analysis_id: str,
    ) -> list[dict]:
        """
        Отправляет гипотезы в Tracker.

        Ошибка Tracker не должна останавливать
        основной аналитический процесс.
        """

        if self.hypothesis_tracker is None:
            return [
                {
                    "status": "SKIPPED",
                    "reason": (
                        "HYPOTHESIS_TRACKER_URL "
                        "is not configured"
                    ),
                }
            ]

        tracking_results = []

        for index, hypothesis in enumerate(
            hypotheses
        ):
            direction = self._direction_for_hypothesis(
                hypothesis.title,
                index,
            )

            payload = {
                "title": hypothesis.title,
                "description": (
                    "Automatically generated by "
                    "Alpha Analytical Engine. "
                    f"Supporting factors: "
                    f"{'; '.join(hypothesis.supporting_factors)}. "
                    f"Opposing factors: "
                    f"{'; '.join(hypothesis.opposing_factors)}."
                ),
                "probability": (
                    hypothesis.probability
                ),
                "symbol": "^GSPC",
                "horizon_days": 20,
                "direction": direction,
                "confirmation_threshold_pct": 0,
                "max_drawdown_limit_pct": 5,
                "source_analysis_id": analysis_id,
                "source_engine_version": "1.0.0",
                "tags": [
                    "automated",
                    "market",
                    "analytical-engine",
                ],
                "metadata": {
                    "hypothesis_index": index,
                    "market_scope": "US equities",
                },
            }

            try:
                saved = (
                    await self.hypothesis_tracker.register(
                        payload
                    )
                )

                tracking_results.append(
                    {
                        "status": "REGISTERED",
                        "title": hypothesis.title,
                        "hypothesis_id": saved.get(
                            "hypothesis_id"
                        ),
                        "baseline_price": saved.get(
                            "baseline_price"
                        ),
                        "due_at": saved.get(
                            "due_at"
                        ),
                    }
                )

            except Exception as exc:
                tracking_results.append(
                    {
                        "status": "FAILED",
                        "title": hypothesis.title,
                        "error": str(exc),
                    }
                )

        return tracking_results

    def _direction_for_hypothesis(
        self,
        title: str,
        index: int,
    ) -> str:
        """
        Определяет направление гипотезы.

        Первая гипотеза обычно является
        продолжением тренда, вторая —
        гипотезой разворота.
        """

        title_lower = title.lower()

        bearish_terms = (
            "reverse",
            "decline",
            "fall",
            "bear",
            "risk conditions",
        )

        if any(
            term in title_lower
            for term in bearish_terms
        ):
            return "DOWN"

        if index == 0:
            return "UP"

        return "DOWN"
