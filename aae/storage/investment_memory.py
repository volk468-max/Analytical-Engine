import json
import logging
import os
from datetime import datetime, timezone

import psycopg

logger = logging.getLogger(__name__)


def save_investment_decision(
    symbol: str,
    decision: dict,
    snapshot: dict,
    market_regime: dict,
    long_term_thesis: dict,
) -> bool:
    """
    Save an immutable investment decision snapshot.

    Database failures must not interrupt the
    analytical API response.
    """

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        logger.warning(
            "Investment Memory: DATABASE_URL missing"
        )
        return False

    now = datetime.now(timezone.utc)

    report = {
        "schema_version": "investment-memory-v1",
        "created_at_utc": now.isoformat(),
        "symbol": symbol.upper(),
        "decision": decision,
        "snapshot": snapshot,
        "market_regime": market_regime,
        "long_term_thesis": long_term_thesis,
        "strategies": {
            "short_term": None,
            "medium_term": None,
            "long_term": None,
        },
    }

    try:
        payload = json.dumps(
            report,
            ensure_ascii=False,
            default=str,
            allow_nan=False,
        )

        with psycopg.connect(
            database_url,
            connect_timeout=5,
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO investment_decisions
                        (symbol, decision_date, report_data)
                    VALUES (%s, %s, %s::json)
                    """,
                    (
                        symbol.upper(),
                        now.date(),
                        payload,
                    ),
                )

        logger.info(
            "Investment Memory: saved decision for %s",
            symbol,
        )
        return True

    except Exception:
        logger.exception(
            "Investment Memory: failed to save %s",
            symbol,
        )
        return False
