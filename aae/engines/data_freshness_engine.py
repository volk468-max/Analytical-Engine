from datetime import datetime, timezone
from typing import Any


class DataFreshnessEngine:
    VERSION = "Data-Freshness-Engine-v1"

    HISTORY_MAX_HOURS = 36
    REVISIONS_MAX_HOURS = 72
    FUNDAMENTALS_MAX_HOURS = 24 * 14

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

        return round(
            age.total_seconds() / 3600,
            1,
        )

    def _status(
        self,
        age_hours: float | None,
        max_hours: float,
    ) -> str:
        if age_hours is None:
            return "UNKNOWN"

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
    ) -> dict[str, Any]:

        now = datetime.now(timezone.utc)

        fundamentals = fundamentals or {}
        revisions = revisions or {}

        latest_history = (
            self._latest_history_record(history)
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
            )

        fundamentals_time = (
            fundamentals.get("snapshot_time")
            or fundamentals.get("created_at")
        )

        revisions_time = (
            revisions.get("snapshot_time")
            or revisions.get("created_at")
        )

        fundamentals_age = self._age_hours(
            fundamentals_time,
            now,
        )

        history_age = self._age_hours(
            history_created_at,
            now,
        )

        revisions_age = self._age_hours(
            revisions_time,
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

        statuses = [
            fundamentals_status,
            history_status,
            revisions_status,
        ]

        if all(
            status == "FRESH"
            for status in statuses
        ):
            overall_status = "FRESH"

        elif any(
            status == "STALE"
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

            "warnings": warnings,
            "engine_version": self.VERSION,
            "status": "FRESHNESS_READY",
        }
