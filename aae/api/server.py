import asyncio
import json
import os
from pathlib import Path

from fastapi import (
    FastAPI,
    HTTPException,
    Query,
)

from aae.connectors.adc import ADCConnector 
from aae.core.orchestrator import (
    AnalyticalOrchestrator,
)
from aae.engines.company_analysis import (
    CompanyAnalysisEngine,
)
from aae.engines.technical_analysis import (
    TechnicalAnalysisEngine,
)
from aae.storage.database import Database 
from aae.storage.repository import (
    AnalysisRepository,
)
from aae.engines.company_risk import (
    CompanyRiskEngine,
)
from aae.engines.revision_analysis import (
    RevisionAnalysisEngine,
)

app = FastAPI(
    title="Alpha Analytical Engine",
    version="1.5.0",
)

DB_PATH = os.environ.get(
    "ANALYSIS_DB_PATH",
    "data/analysis.sqlite3",
)


CORE_PORTFOLIO = [
    "NVDA",
    "AMD",
    "AVGO",
    "TSM",
    "ASML",
    "AMAT",
    "LRCX",
    "KLAC",
    "MU",
    "MRVL",
    "VRT",
    "ETN",
    "ANET",
    "CRWV",
    "SNOW",
    "PLTR",
    "META",
    "AMZN",
    "GOOGL",
    "MSFT",
    "TSLA",
    "WIX",
    "ARM",
    "ORCL",
    "GEV",
]


def get_adc_url() -> str:
    adc_url = os.environ.get(
        "ADC_BASE_URL"
    )

    if not adc_url:
        raise HTTPException(
            status_code=500,
            detail="ADC_BASE_URL must be configured.",
        )

    return adc_url


def orchestrator():
    adc_url = get_adc_url()

    knowledge_url = os.environ.get(
        "KNOWLEDGE_BASE_URL"
    )

    hypothesis_tracker_url = os.environ.get(
        "HYPOTHESIS_TRACKER_URL"
    )

    if not knowledge_url:
        raise HTTPException(
            status_code=500,
            detail=(
                "KNOWLEDGE_BASE_URL "
                "must be configured."
            ),
        )

    return AnalyticalOrchestrator(
        adc_url=adc_url,
        knowledge_url=knowledge_url,
        hypothesis_tracker_url=(
            hypothesis_tracker_url
        ),
        db_path=DB_PATH,
    )


@app.get("/")
def root():
    return {
        "service": "Alpha Analytical Engine",
        "status": "ok",
        "version": "1.5.0",
        "hypothesis_tracking": bool(
            os.environ.get(
                "HYPOTHESIS_TRACKER_URL"
            )
        ),
        "company_analysis": True,
        "company_ranking": True,
        "technical_analysis": True,
        "technical_ranking": True,
        "alpha_ranking": True,
        "risk_analysis": True,
        "risk_ranking": True,
        "alpha_ranking_v2": True,
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "adc_configured": bool(
            os.environ.get("ADC_BASE_URL")
        ),
        "knowledge_configured": bool(
            os.environ.get(
                "KNOWLEDGE_BASE_URL"
            )
        ),
        "hypothesis_tracker_configured": bool(
            os.environ.get(
                "HYPOTHESIS_TRACKER_URL"
            )
        ),
        "company_analysis": True,
        "company_ranking": True,
        "technical_analysis": True,
        "technical_ranking": True,
        "alpha_ranking": True,
        "risk_analysis": True,
        "risk_ranking": True,
        "alpha_ranking_v2": True,
    }


@app.post("/analysis/run")
async def run_analysis():
    result = await orchestrator().run()

    return result.model_dump()


@app.post("/company/analyze/{symbol}")
async def analyze_company(symbol: str):
    symbol = symbol.strip().upper()

    if not symbol:
        raise HTTPException(
            status_code=400,
            detail="Symbol is required.",
        )

    adc = ADCConnector(
        get_adc_url()
    )

    try:
        fundamentals = await adc.fundamentals(
            symbol
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                f"Unable to obtain fundamentals "
                f"for {symbol}: {exc}"
            ),
        ) from exc

    engine = CompanyAnalysisEngine()

    result = engine.evaluate(
        fundamentals
    )

    return result.model_dump()


@app.post("/company/technical/{symbol}")
async def technical_company(symbol: str):
    symbol = symbol.strip().upper()

    if not symbol:
        raise HTTPException(
            status_code=400,
            detail="Symbol is required.",
        )

    adc = ADCConnector(
        get_adc_url()
    )

    try:
        history = await adc.history(
            symbol,
            limit=500,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                f"Unable to obtain market history "
                f"for {symbol}: {exc}"
            ),
        ) from exc

    engine = TechnicalAnalysisEngine()

    try:
        result = engine.evaluate(
            history
        )

    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Unable to calculate technical "
                f"analysis for {symbol}: {exc}"
            ),
        ) from exc

    return result
@app.post("/company/risk/{symbol}")
async def company_risk(symbol: str):
    symbol = symbol.strip().upper()

    if not symbol:
        raise HTTPException(
            status_code=400,
            detail="Symbol is required.",
        )

    adc = ADCConnector(
        get_adc_url()
    )

    try:
        fundamentals, history = await asyncio.gather(
            adc.fundamentals(symbol),
            adc.history(
                symbol,
                limit=500,
            ),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                f"Unable to obtain data "
                f"for {symbol}: {exc}"
            ),
        ) from exc

    engine = CompanyRiskEngine()

    try:
        result = engine.evaluate(
            fundamentals,
            history,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Unable to calculate risk "
                f"for {symbol}: {exc}"
            ),
        ) from exc

    return result
@app.post("/company/revisions/{symbol}")
async def company_revisions(symbol: str):
    symbol = symbol.strip().upper()

    if not symbol:
        raise HTTPException(
            status_code=400,
            detail="Symbol is required.",
        )

    adc = ADCConnector(
        get_adc_url()
    )

    try:
        revisions = await adc.revisions(
            symbol
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                f"Unable to obtain revisions "
                f"for {symbol}: {exc}"
            ),
        ) from exc

    engine = RevisionAnalysisEngine()

    try:
        result = engine.evaluate(
            revisions
        )

    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Unable to calculate revisions "
                f"for {symbol}: {exc}"
            ),
        ) from exc

    return result
@app.get("/company/revision-ranking")
async def revision_ranking():
    adc = ADCConnector(
        get_adc_url()
    )

    engine = RevisionAnalysisEngine()

    async def analyze_symbol(symbol: str):
        try:
            revisions = await adc.revisions(
                symbol
            )

            result = engine.evaluate(
                revisions
            )

            return {
                "symbol": symbol,
                "revision_score": (
                    result["revision_score"]
                ),
                "forward_growth_score": (
                    result[
                        "forward_growth_score"
                    ]
                ),
                "revision_breadth_score": (
                    result[
                        "revision_breadth_score"
                    ]
                ),
                "estimate_trend_score": (
                    result[
                        "estimate_trend_score"
                    ]
                ),
                "analyst_coverage_score": (
                    result[
                        "analyst_coverage_score"
                    ]
                ),
                "forward_eps_growth": (
                    result[
                        "forward_eps_growth"
                    ]
                ),
                "estimate_change_30d": (
                    result[
                        "estimate_change_30d"
                    ]
                ),
                "up_7d": result["up_7d"],
                "down_7d": result["down_7d"],
                "up_30d": result["up_30d"],
                "down_30d": result["down_30d"],
                "number_of_analysts": (
                    result[
                        "number_of_analysts"
                    ]
                ),
                "conclusion": (
                    result["conclusion"]
                ),
                "status": "ok",
            }

        except Exception as exc:
            return {
                "symbol": symbol,
                "status": "error",
                "error": str(exc),
            }

    results = await asyncio.gather(
        *[
            analyze_symbol(symbol)
            for symbol in CORE_PORTFOLIO
        ]
    )

    successful = [
        result
        for result in results
        if result.get("status") == "ok"
    ]

    errors = [
        result
        for result in results
        if result.get("status") == "error"
    ]

    successful.sort(
        key=lambda item: item[
            "revision_score"
        ],
        reverse=True,
    )

    for rank, item in enumerate(
        successful,
        start=1,
    ):
        item["revision_rank"] = rank

    return {
        "count": len(successful),
        "errors_count": len(errors),
        "ranking_direction": (
            "strongest_revisions_first"
        ),
        "ranking": successful,
        "errors": errors,
    }
@app.get("/company/snapshot/{symbol}")
async def company_snapshot(symbol: str):
    symbol = symbol.upper()

    adc = ADCConnector(
        get_adc_url()
    )

    fundamental_engine = CompanyAnalysisEngine()
    technical_engine = TechnicalAnalysisEngine()
    risk_engine = CompanyRiskEngine()
    revision_engine = RevisionAnalysisEngine()

    try:
        fundamentals, history, revisions, market_summary = await asyncio.gather(
            adc.fundamentals(symbol),
            adc.history(
                symbol,
                limit=500,
            ),
            adc.revisions(symbol),
            adc.market_summary(),
        )

        fundamental = fundamental_engine.evaluate(
            fundamentals
        )

        technical = technical_engine.evaluate(
            history
        )

        risk = risk_engine.evaluate(
            fundamentals,
            history,
        )

        revision = revision_engine.evaluate(
            revisions
        )

        base_alpha = round(
            fundamental.fundamental_score * 0.60
            + technical["technical_score"] * 0.40,
            1,
        )

        fundamental_data = (
            fundamental.model_dump()
            if hasattr(fundamental, "model_dump")
            else fundamental
        )

        return {
            "symbol": symbol,
            "base_alpha": base_alpha,
            "fundamental": fundamental_data,
            "technical": technical,
            "risk": risk,
            "revisions": revision,
            "market": market_summary,
            "status": "ok",
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Snapshot failed for {symbol}: {exc}",
        )

@app.get("/company/divergence-ranking")
async def divergence_ranking():
    adc = ADCConnector(
        get_adc_url()
    )

    fundamental_engine = CompanyAnalysisEngine()
    technical_engine = TechnicalAnalysisEngine()
    risk_engine = CompanyRiskEngine()
    revision_engine = RevisionAnalysisEngine()

    async def analyze_symbol(symbol: str):
        try:
            fundamentals, history, revisions = await asyncio.gather(
                adc.fundamentals(symbol),
                adc.history(
                    symbol,
                    limit=500,
                ),
                adc.revisions(symbol),
            )

            fundamental = fundamental_engine.evaluate(
                fundamentals
            )

            technical = technical_engine.evaluate(
                history
            )

            risk = risk_engine.evaluate(
                fundamentals,
                history,
            )

            revision = revision_engine.evaluate(
                revisions
            )

            base_alpha = round(
                fundamental.fundamental_score * 0.60
                + technical["technical_score"] * 0.40,
                1,
            )

            return {
                "symbol": symbol,
                "fundamental_score": (
                    fundamental.fundamental_score
                ),
                "technical_score": (
                    technical["technical_score"]
                ),
                "risk_score": (
                    risk["risk_score"]
                ),
                "revision_score": (
                    revision["revision_score"]
                ),
                "base_alpha": base_alpha,
                "status": "ok",
            }

        except Exception as exc:
            return {
                "symbol": symbol,
                "status": "error",
                "error": str(exc),
            }

    results = await asyncio.gather(
        *[
            analyze_symbol(symbol)
            for symbol in CORE_PORTFOLIO
        ]
    )

    successful = [
        item
        for item in results
        if item.get("status") == "ok"
    ]

    errors = [
        item
        for item in results
        if item.get("status") == "error"
    ]

    def build_ranks(
        key: str,
        reverse: bool = True,
    ):
        ordered = sorted(
            successful,
            key=lambda item: item[key],
            reverse=reverse,
        )

        return {
            item["symbol"]: rank
            for rank, item in enumerate(
                ordered,
                start=1,
            )
        }

    fundamental_ranks = build_ranks(
        "fundamental_score"
    )

    technical_ranks = build_ranks(
        "technical_score"
    )

    revision_ranks = build_ranks(
        "revision_score"
    )

    alpha_ranks = build_ranks(
        "base_alpha"
    )

    risk_ranks = build_ranks(
        "risk_score",
        reverse=False,
    )

    output = []

    for item in successful:
        symbol = item["symbol"]

        fundamental_rank = (
            fundamental_ranks[symbol]
        )

        technical_rank = (
            technical_ranks[symbol]
        )

        revision_rank = (
            revision_ranks[symbol]
        )

        alpha_rank = (
            alpha_ranks[symbol]
        )

        risk_rank = (
            risk_ranks[symbol]
        )

        revision_vs_alpha = (
            alpha_rank - revision_rank
        )

        signal = "NEUTRAL"

        if revision_vs_alpha >= 8:
            signal = (
                "POSITIVE_REVISION_DIVERGENCE"
            )

        elif revision_vs_alpha <= -8:
            signal = (
                "NEGATIVE_REVISION_DIVERGENCE"
            )

        elif (
            fundamental_rank <= 7
            and technical_rank <= 7
            and revision_rank <= 7
            and risk_rank <= 12
        ):
            signal = (
                "MULTI_FACTOR_CONFIRMATION"
            )

        output.append(
            {
                **item,
                "fundamental_rank": (
                    fundamental_rank
                ),
                "technical_rank": (
                    technical_rank
                ),
                "risk_rank": (
                    risk_rank
                ),
                "revision_rank": (
                    revision_rank
                ),
                "alpha_rank": (
                    alpha_rank
                ),
                "revision_vs_alpha": (
                    revision_vs_alpha
                ),
                "divergence_signal": (
                    signal
                ),
            }
        )

    signal_priority = {
        "MULTI_FACTOR_CONFIRMATION": 1,
        "POSITIVE_REVISION_DIVERGENCE": 2,
        "NEGATIVE_REVISION_DIVERGENCE": 3,
        "NEUTRAL": 4,
    }

    output.sort(
        key=lambda item: (
            signal_priority[
                item["divergence_signal"]
            ],
            item["revision_rank"],
        )
    )

    return {
        "count": len(output),
        "errors_count": len(errors),
        "rules": {
            "positive_divergence": (
                "revision rank is at least "
                "8 places stronger than alpha rank"
            ),
            "negative_divergence": (
                "revision rank is at least "
                "8 places weaker than alpha rank"
            ),
            "multi_factor_confirmation": (
                "fundamental, technical and "
                "revision ranks are all top 7 "
                "and risk rank is top 12"
            ),
        },
        "signals": output,
        "errors": errors,
    }

@app.get("/company/ranking")
async def company_ranking():
    adc = ADCConnector(
        get_adc_url()
    )

    engine = CompanyAnalysisEngine()

    async def analyze_symbol(symbol: str):
        try:
            fundamentals = await adc.fundamentals(
                symbol
            )

            result = engine.evaluate(
                fundamentals
            )

            return {
                "symbol": result.symbol,
                "company_name": (
                    result.company_name
                ),
                "fundamental_score": (
                    result.fundamental_score
                ),
                "growth_score": (
                    result.growth_score
                ),
                "valuation_score": (
                    result.valuation_score
                ),
                "quality_score": (
                    result.quality_score
                ),
                "balance_sheet_score": (
                    result.balance_sheet_score
                ),
                "conclusion": (
                    result.conclusion
                ),
                "status": "ok",
            }

        except Exception as exc:
            return {
                "symbol": symbol,
                "status": "error",
                "error": str(exc),
            }

    results = await asyncio.gather(
        *[
            analyze_symbol(symbol)
            for symbol in CORE_PORTFOLIO
        ]
    )

    successful = [
        result
        for result in results
        if result.get("status") == "ok"
    ]

    errors = [
        result
        for result in results
        if result.get("status") == "error"
    ]

    successful.sort(
        key=lambda item: item[
            "fundamental_score"
        ],
        reverse=True,
    )

    for rank, item in enumerate(
        successful,
        start=1,
    ):
        item["rank"] = rank

    return {
        "count": len(successful),
        "errors_count": len(errors),
        "ranking": successful,
        "errors": errors,
    }

@app.get("/company/technical-ranking")
async def technical_ranking():
    adc = ADCConnector(
        get_adc_url()
    )

    engine = TechnicalAnalysisEngine()

    async def analyze_symbol(symbol: str):
        try:
            history = await adc.history(
                symbol,
                limit=500,
            )

            result = engine.evaluate(
                history
            )

            return {
                "symbol": symbol,
                "technical_score": (
                    result["technical_score"]
                ),
                "trend_score": (
                    result["trend_score"]
                ),
                "momentum_score": (
                    result["momentum_score"]
                ),
                "rsi_score": (
                    result["rsi_score"]
                ),
                "position_52w_score": (
                    result["position_52w_score"]
                ),
                "current_price": (
                    result["current_price"]
                ),
                "ma50": result["ma50"],
                "ma200": result["ma200"],
                "rsi14": result["rsi14"],
                "momentum_1m": (
                    result["momentum_1m"]
                ),
                "momentum_3m": (
                    result["momentum_3m"]
                ),
                "momentum_6m": (
                    result["momentum_6m"]
                ),
                "momentum_1y": (
                    result["momentum_1y"]
                ),
                "distance_from_52w_high": (
                    result[
                        "distance_from_52w_high"
                    ]
                ),
                "conclusion": (
                    result["conclusion"]
                ),
                "status": "ok",
            }

        except Exception as exc:
            return {
                "symbol": symbol,
                "status": "error",
                "error": str(exc),
            }

    results = await asyncio.gather(
        *[
            analyze_symbol(symbol)
            for symbol in CORE_PORTFOLIO
        ]
    )

    successful = [
        result
        for result in results
        if result.get("status") == "ok"
    ]

    errors = [
        result
        for result in results
        if result.get("status") == "error"
    ]

    successful.sort(
        key=lambda item: item[
            "technical_score"
        ],
        reverse=True,
    )

    for rank, item in enumerate(
        successful,
        start=1,
    ):
        item["rank"] = rank

    return {
        "count": len(successful),
        "errors_count": len(errors),
        "ranking": successful,
        "errors": errors,
    }
@app.get("/company/alpha-ranking")
async def alpha_ranking():
    adc = ADCConnector(
        get_adc_url()
    )

    fundamental_engine = (
        CompanyAnalysisEngine()
    )

    technical_engine = (
        TechnicalAnalysisEngine()
    )

    async def analyze_symbol(symbol: str):
        try:
            fundamentals, history = await asyncio.gather(
                adc.fundamentals(symbol),
                adc.history(
                    symbol,
                    limit=500,
                ),
            )

            fundamental_result = (
                fundamental_engine.evaluate(
                    fundamentals
                )
            )

            technical_result = (
                technical_engine.evaluate(
                    history
                )
            )

            fundamental_score = (
                fundamental_result.fundamental_score
            )

            technical_score = (
                technical_result[
                    "technical_score"
                ]
            )

            alpha_score = round(
                fundamental_score * 0.60
                + technical_score * 0.40,
                1,
            )

            return {
                "symbol": symbol,
                "company_name": (
                    fundamental_result.company_name
                ),
                "fundamental_score": (
                    fundamental_score
                ),
                "technical_score": (
                    technical_score
                ),
                "alpha_score": (
                    alpha_score
                ),
                "growth_score": (
                    fundamental_result.growth_score
                ),
                "valuation_score": (
                    fundamental_result.valuation_score
                ),
                "quality_score": (
                    fundamental_result.quality_score
                ),
                "balance_sheet_score": (
                    fundamental_result.balance_sheet_score
                ),
                "trend_score": (
                    technical_result[
                        "trend_score"
                    ]
                ),
                "momentum_score": (
                    technical_result[
                        "momentum_score"
                    ]
                ),
                "rsi_score": (
                    technical_result[
                        "rsi_score"
                    ]
                ),
                "position_52w_score": (
                    technical_result[
                        "position_52w_score"
                    ]
                ),
                "status": "ok",
            }

        except Exception as exc:
            return {
                "symbol": symbol,
                "status": "error",
                "error": str(exc),
            }

    results = await asyncio.gather(
        *[
            analyze_symbol(symbol)
            for symbol in CORE_PORTFOLIO
        ]
    )

    successful = [
        result
        for result in results
        if result.get("status") == "ok"
    ]

    errors = [
        result
        for result in results
        if result.get("status") == "error"
    ]

    fundamental_sorted = sorted(
        successful,
        key=lambda item: item[
            "fundamental_score"
        ],
        reverse=True,
    )

    technical_sorted = sorted(
        successful,
        key=lambda item: item[
            "technical_score"
        ],
        reverse=True,
    )

    alpha_sorted = sorted(
        successful,
        key=lambda item: item[
            "alpha_score"
        ],
        reverse=True,
    )

    fundamental_ranks = {
        item["symbol"]: rank
        for rank, item in enumerate(
            fundamental_sorted,
            start=1,
        )
    }

    technical_ranks = {
        item["symbol"]: rank
        for rank, item in enumerate(
            technical_sorted,
            start=1,
        )
    }

    for rank, item in enumerate(
        alpha_sorted,
        start=1,
    ):
        item["fundamental_rank"] = (
            fundamental_ranks[
                item["symbol"]
            ]
        )

        item["technical_rank"] = (
            technical_ranks[
                item["symbol"]
            ]
        )

        item["alpha_rank"] = rank

    return {
        "count": len(alpha_sorted),
        "errors_count": len(errors),
        "weights": {
            "fundamental": 0.60,
            "technical": 0.40,
        },
        "ranking": alpha_sorted,
        "errors": errors,
    }
@app.get("/company/risk-ranking")
async def risk_ranking():
    adc = ADCConnector(
        get_adc_url()
    )

    engine = CompanyRiskEngine()

    async def analyze_symbol(symbol: str):
        try:
            fundamentals, history = await asyncio.gather(
                adc.fundamentals(symbol),
                adc.history(
                    symbol,
                    limit=500,
                ),
            )

            result = engine.evaluate(
                fundamentals,
                history,
            )

            return {
                "symbol": symbol,
                "risk_score": (
                    result["risk_score"]
                ),
                "risk_level": (
                    result["risk_level"]
                ),
                "volatility_risk": (
                    result["volatility_risk"]
                ),
                "drawdown_risk": (
                    result["drawdown_risk"]
                ),
                "balance_sheet_risk": (
                    result["balance_sheet_risk"]
                ),
                "valuation_risk": (
                    result["valuation_risk"]
                ),
                "trend_risk": (
                    result["trend_risk"]
                ),
                "cash_flow_risk": (
                    result["cash_flow_risk"]
                ),
                "annualized_volatility": (
                    result[
                        "annualized_volatility"
                    ]
                ),
                "max_drawdown": (
                    result[
                        "max_drawdown"
                    ]
                ),
                "status": "ok",
            }

        except Exception as exc:
            return {
                "symbol": symbol,
                "status": "error",
                "error": str(exc),
            }

    results = await asyncio.gather(
        *[
            analyze_symbol(symbol)
            for symbol in CORE_PORTFOLIO
        ]
    )

    successful = [
        result
        for result in results
        if result.get("status") == "ok"
    ]

    errors = [
        result
        for result in results
        if result.get("status") == "error"
    ]

    successful.sort(
        key=lambda item: item[
            "risk_score"
        ]
    )

    for rank, item in enumerate(
        successful,
        start=1,
    ):
        item["risk_rank"] = rank

    return {
        "count": len(successful),
        "errors_count": len(errors),
        "ranking_direction": (
            "lowest_risk_first"
        ),
        "ranking": successful,
        "errors": errors,
    }
@app.get("/company/alpha-ranking-v2")
async def alpha_ranking_v2():
    adc = ADCConnector(
        get_adc_url()
    )

    fundamental_engine = CompanyAnalysisEngine()
    technical_engine = TechnicalAnalysisEngine()
    risk_engine = CompanyRiskEngine()

    def risk_penalty(
        risk_score: float,
    ) -> float:
        if risk_score <= 45:
            return 0.0

        if risk_score <= 60:
            return round(
                (risk_score - 45) * 0.10,
                1,
            )

        if risk_score <= 75:
            return round(
                1.5
                + (risk_score - 60) * 0.30,
                1,
            )

        return round(
            6.0
            + (risk_score - 75) * 0.40,
            1,
        )

    async def analyze_symbol(symbol: str):
        try:
            fundamentals, history = await asyncio.gather(
                adc.fundamentals(symbol),
                adc.history(
                    symbol,
                    limit=500,
                ),
            )

            fundamental_result = (
                fundamental_engine.evaluate(
                    fundamentals
                )
            )

            technical_result = (
                technical_engine.evaluate(
                    history
                )
            )

            risk_result = (
                risk_engine.evaluate(
                    fundamentals,
                    history,
                )
            )

            fundamental_score = (
                fundamental_result.fundamental_score
            )

            technical_score = (
                technical_result[
                    "technical_score"
                ]
            )

            risk_score = (
                risk_result[
                    "risk_score"
                ]
            )

            base_alpha = round(
                fundamental_score * 0.60
                + technical_score * 0.40,
                1,
            )

            penalty = risk_penalty(
                risk_score
            )

            alpha_score_v2 = round(
                max(
                    0.0,
                    base_alpha - penalty,
                ),
                1,
            )

            return {
                "symbol": symbol,
                "company_name": (
                    fundamental_result.company_name
                ),
                "fundamental_score": (
                    fundamental_score
                ),
                "technical_score": (
                    technical_score
                ),
                "base_alpha": (
                    base_alpha
                ),
                "risk_score": (
                    risk_score
                ),
                "risk_level": (
                    risk_result[
                        "risk_level"
                    ]
                ),
                "risk_penalty": (
                    penalty
                ),
                "alpha_score_v2": (
                    alpha_score_v2
                ),
                "status": "ok",
            }

        except Exception as exc:
            return {
                "symbol": symbol,
                "status": "error",
                "error": str(exc),
            }

    results = await asyncio.gather(
        *[
            analyze_symbol(symbol)
            for symbol in CORE_PORTFOLIO
        ]
    )

    successful = [
        result
        for result in results
        if result.get("status") == "ok"
    ]

    errors = [
        result
        for result in results
        if result.get("status") == "error"
    ]

    v1_sorted = sorted(
        successful,
        key=lambda item: item[
            "base_alpha"
        ],
        reverse=True,
    )

    v2_sorted = sorted(
        successful,
        key=lambda item: item[
            "alpha_score_v2"
        ],
        reverse=True,
    )

    v1_ranks = {
        item["symbol"]: rank
        for rank, item in enumerate(
            v1_sorted,
            start=1,
        )
    }

    for rank, item in enumerate(
        v2_sorted,
        start=1,
    ):
        item["alpha_rank_v1"] = (
            v1_ranks[
                item["symbol"]
            ]
        )

        item["alpha_rank_v2"] = rank

        item["rank_change"] = (
            item["alpha_rank_v1"]
            - item["alpha_rank_v2"]
        )

    return {
        "count": len(v2_sorted),
        "errors_count": len(errors),
        "base_weights": {
            "fundamental": 0.60,
            "technical": 0.40,
        },
        "risk_adjustment": (
            "nonlinear_penalty"
        ),
        "ranking": v2_sorted,
        "errors": errors,
    }

@app.get("/analysis/latest")
def latest():
    result = AnalysisRepository(
        Database(DB_PATH)
    ).latest()

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="No analysis has been run.",
        )

    return result


@app.get("/analysis/history")
def history(
    limit: int = Query(
        default=50,
        ge=1,
        le=1000,
    )
):
    return {
        "records": AnalysisRepository(
            Database(DB_PATH)
        ).history(limit)
    }


@app.get("/version")
def version():
    path = Path("version.json")

    if path.exists():
        return json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    return {
        "version": "unknown"
    }
