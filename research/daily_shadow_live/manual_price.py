"""Explicit, non-persistent Alpha Full Price preview for the last XNYS close."""
from datetime import datetime, timedelta, timezone
import os
import uuid

from research.daily_shadow.core import calendar
from research.daily_shadow_v3.store import ResearchStore

from . import alpha_full_price as model
from .alpha_full_price_runtime import collect_frames, export_body, training_records
from .alpha_full_runtime import load_bundle
from .config import ConfigurationError, ENVIRONMENT, PROJECT, dsn, vault_key
from .diagnostics import RunAudit
from .runtime import effective_permit, latest_completed, paid_status


def run_preview(store, audit, permit, *, collector=None):
    session = latest_completed(datetime.now(timezone.utc))
    bundle = load_bundle()
    frames, failures, sources = collect_frames(
        permit, session, collector=collector,
        identities=(bundle or {}).get('instrument_identity'),
        archive=lambda symbol, snapshot: (snapshot.revision, snapshot.retrieved_at),
    )
    cutoff = datetime.now(timezone.utc)
    if latest_completed(cutoff) != session:
        raise ValueError('SESSION_CHANGED_DURING_MANUAL_COLLECTION')
    if not frames:
        raise ValueError('NO_MANUAL_PRICE_INPUTS')
    body = model.forecast(
        frames, failures, session, cutoff.isoformat(), bundle=bundle,
        records=training_records(store, cutoff.isoformat()),
    )
    issued = datetime.now(timezone.utc)
    if latest_completed(issued) != session:
        raise ValueError('SESSION_CHANGED_DURING_MANUAL_CALCULATION')
    body.update(
        run_mode='MANUAL_PREVIEW', issued_at=issued.isoformat(),
        calculation_cutoff_utc=cutoff.isoformat(),
        source_revision_sha256={symbol: source[0] for symbol, source in sources.items()},
        source_retrieved_at_utc={symbol: source[1] for symbol, source in sources.items()},
    )
    for row in body['rows'] + body['market_rows']:
        row['issued_at'] = body['issued_at']
        target = calendar().session_close(row['target_session']).to_pydatetime()
        reason = permit.reason(body['issued_at'], fixture=False,
                               horizon_end=(target + timedelta(days=1)).isoformat())
        if reason and row['expected_return_pct'] is not None:
            row.update(status='STATUS_BLOCKED', reason=reason, license_reason=reason,
                       expected_return_pct=None, band_low_pct=None,
                       band_high_pct=None, direction=None)
    export_body(audit, uuid.uuid4(), body, phase='ALPHA_FULL_PRICE_MANUAL_EXPORT')
    return body


def main():
    audit = RunAudit()
    try:
        if (os.environ.get('RAILWAY_PROJECT_ID'),
                os.environ.get('RAILWAY_ENVIRONMENT_ID'),
                os.environ.get('RAILWAY_SERVICE_ID')) != (
                    PROJECT, ENVIRONMENT, '4644a769-65e7-4a6d-855d-1ddae2b95333'):
            raise ConfigurationError('WRONG_MANUAL_RAILWAY_IDENTITY')
        if os.environ.get('ALPHA_RUN_MODE') != 'RESEARCH_FORECAST':
            raise ConfigurationError('RESEARCH_MODE_REQUIRED')
        if os.environ.get('ALPHA_LIVE_TRADING', 'false').lower() != 'false':
            raise ConfigurationError('TRADING_FORBIDDEN')
        url = dsn()
        paid_status()
        store = ResearchStore(url, vault_key(url))
        run_preview(store, audit, effective_permit(store))
    except Exception as exc:
        audit.failure('ALPHA_FULL_PRICE_MANUAL', exc, persist=False)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
