from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field

class Observation(BaseModel):
    name: str
    value: str
    direction: str
    explanation: str

class Hypothesis(BaseModel):
    title: str
    probability: float
    supporting_factors: list[str]
    opposing_factors: list[str]

class Scenario(BaseModel):
    name: str
    probability: float
    description: str
    triggers: list[str]
    invalidation_conditions: list[str]

class AnalysisResult(BaseModel):
    analysis_id: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    market_state: str
    market_score: float
    risk_level: str
    risk_score: float
    confidence: float
    observations: list[Observation]
    hypotheses: list[Hypothesis]
    scenarios: list[Scenario]
    conclusion: str
    what_changes_the_view: list[str]
    source_status: dict[str, Any]
    
class CompanyAnalysisResult(BaseModel):
    symbol: str
    company_name: str

    created_at: str = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    fundamental_score: float

    growth_score: float
    valuation_score: float
    quality_score: float
    balance_sheet_score: float

    fundamentals: dict[str, Any]

    supporting_factors: list[str]
    opposing_factors: list[str]

    conclusion: str
