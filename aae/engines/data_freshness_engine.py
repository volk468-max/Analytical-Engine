from datetime import datetime, timezone
from typing import Any


class DataFreshnessEngine:
    VERSION = "Data-Freshness-Engine-v1"

    HISTORY_MAX_HOURS = 96
    REVISIONS_MAX_HOURS = 72
    FUNDAMENTALS_MAX_HOURS = 24 * 14
    MARKET_MAX_HOURS = 36

    def __init__(self, history_max_hours=None, market_max_hours=None):
        for name, value in (("HISTORY_MAX_HOURS", history_max_hours), ("MARKET_MAX_HOURS", market_max_hours)):
            if value is not None:
                from math import isfinite
                if not isfinite(value) or value <= 0:
                    raise ValueError("Freshness limits must be finite and positive")
                setattr(self, name, value)

    def _parse_datetime(
        self,
        value: Any,
    ) -> datetime | None:
        if not value:
            return None

        if not isinstance(value, str):
            return None

        value = value.strip()

        try:
            parsed = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )

            if parsed.tzinfo is None:
                parsed = parsed.replace(
                    tzinfo=timezone.utc
                )

            return parsed.astimezone(timezone.utc)

        except ValueError:
            return None

    def _age_hours(
        self,
        value: Any,
        now: datetime,
    ) -> float | None:
        parsed = self._parse_datetime(value)

        if parsed is None:
            return None

        age = now - parsed

        return age.total_seconds() / 3600

    def _status(
        self,
        age_hours: float | None,
        max_hours: float,
    ) -> str:
        if age_hours is None:
            return "UNKNOWN"

        if age_hours < 0:
            return "INVALID"

        if age_hours <= max_hours:
            return "FRESH"

        return "STALE"

    def _latest_history_record(
        self,
        history: Any,
    ) -> dict | None:
        if isinstance(history, dict):
            records = history.get("records", [])
        else:
            records = history

        if not isinstance(records, list):
            return None

        valid_records = [
            row
            for row in records
            if isinstance(row, dict)
        ]

        if not valid_records:
            return None

        valid_records.sort(
            key=lambda row: (
                row.get("trade_date")
                or row.get("date")
                or row.get("timestamp")
                or ""
            ),
            reverse=True,
        )

        return valid_records[0]

    def evaluate(
        self,
        fundamentals: dict | None,
        history: Any,
        revisions: dict | None,
        market_summary: dict | None = None,
        now: datetime | None = None,
    ) -> dict[str, Any]:

        now = now or datetime.now(timezone.utc)

        fundamentals = fundamentals or {}
        revisions = revisions or {}
        market_summary = market_summary or {}

        latest_history = self._latest_history_record(
            history
        )

        history_created_at = None
        history_trade_date = None

        if latest_history:
            history_created_at = (
                latest_history.get("created_at")
            )

            history_trade_date = (
                latest_history.get("trade_date")
                or latest_history.get("date")
                or latest_history.get("timestamp")
            )

        fundamentals_time = (
            fundamentals.get("snapshot_time")
            or fundamentals.get("created_at")
        )

        revisions_time = (
            revisions.get("snapshot_time")
            or revisions.get("created_at")
        )

        market_time = (
            market_summary.get("snapshot_time")
            or market_summary.get("created_at")
        )

        market_trade_date = (
            market_summary.get("trade_date")
        )

        fundamentals_age = self._age_hours(
            fundamentals_time,
            now,
        )

        history_age = self._age_hours(
            history_trade_date,
            now,
        )

        revisions_age = self._age_hours(
            revisions_time,
            now,
        )

        market_age = self._age_hours(
            market_trade_date or market_summary.get("snapshot_time"),
            now,
        )

        fundamentals_status = self._status(
            fundamentals_age,
            self.FUNDAMENTALS_MAX_HOURS,
        )

        history_status = self._status(
            history_age,
            self.HISTORY_MAX_HOURS,
        )

        revisions_status = self._status(
            revisions_age,
            self.REVISIONS_MAX_HOURS,
        )

        market_status = self._status(
            market_age,
            self.MARKET_MAX_HOURS,
        )

        statuses = [
            fundamentals_status,
            history_status,
            revisions_status,
            market_status,
        ]

        if all(
            status == "FRESH"
            for status in statuses
        ):
            overall_status = "FRESH"

        elif any(
            status in {"STALE", "INVALID"}
            for status in statuses
        ):
            overall_status = "PARTIALLY_STALE"

        else:
            overall_status = "UNKNOWN"

        warnings = []

        if history_status == "STALE":
            warnings.append(
                "Market history may be stale."
            )

        if revisions_status == "STALE":
            warnings.append(
                "Analyst revisions may be stale."
            )

        if fundamentals_status == "STALE":
            warnings.append(
                "Fundamental snapshot may be stale."
            )

        if market_status == "STALE":
            warnings.append(
                "Market snapshot may be stale."
            )

        for label, status in (("History", history_status), ("Market", market_status)):
            if status in {"UNKNOWN", "INVALID"}:
                warnings.append(f"{label} observation timestamp is missing, invalid or future-dated.")

        return {
            "overall_status": overall_status,

            "history": {
                "status": history_status,
                "age_hours": history_age,
                "trade_date": history_trade_date,
                "collected_at": history_created_at,
            },

            "fundamentals": {
                "status": fundamentals_status,
                "age_hours": fundamentals_age,
                "snapshot_time": fundamentals_time,
            },

            "revisions": {
                "status": revisions_status,
                "age_hours": revisions_age,
                "snapshot_time": revisions_time,
            },

            "market": {
                "status": market_status,
                "age_hours": market_age,
                "trade_date": market_trade_date,
                "snapshot_time": market_time,
            },

            "warnings": warnings,
            "engine_version": self.VERSION,
            "status": "FRESHNESS_READY",
        }
