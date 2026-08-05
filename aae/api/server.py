import json
import os
from pathlib import Path

from fastapi import (
    FastAPI,
    HTTPException,
    Query,
)

from aae.core.orchestrator import (
    AnalyticalOrchestrator,
)
from aae.storage.database import Database
from aae.storage.repository import (
    AnalysisRepository,
)


app = FastAPI(
    title="Alpha Analytical Engine",
    version="1.1.0",
)

DB_PATH = os.environ.get(
    "ANALYSIS_DB_PATH",
    "data/analysis.sqlite3",
)


def orchestrator():
    adc_url = os.environ.get(
        "ADC_BASE_URL"
    )

    knowledge_url = os.environ.get(
        "KNOWLEDGE_BASE_URL"
    )

    hypothesis_tracker_url = os.environ.get(
        "HYPOTHESIS_TRACKER_URL"
    )

    if not adc_url or not knowledge_url:
        raise HTTPException(
            status_code=500,
            detail=(
                "ADC_BASE_URL and "
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
        "version": "1.1.0",
        "hypothesis_tracking": bool(
            os.environ.get(
                "HYPOTHESIS_TRACKER_URL"
            )
        ),
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
    }


@app.post("/analysis/run")
async def run_analysis():
    result = await orchestrator().run()

    return result.model_dump()


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
