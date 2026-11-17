# Alpha OS forecast dashboard v1 (research only)

Private, responsive Russian dashboard for the **existing** isolated `alpha_shadow_research` PostgreSQL. It does not issue predictions, retrain models, trade, alter risk thresholds, access raw OHLC, or modify the database.

## Data / semantics

- Read-only `RESEARCH_FORECAST` rows, rolling 120 calendar days (maximum 25,000 rows), six symbols: SPY, QQQ, SOXX, AMD, NVDA, MU.
- Switch symbol, threshold (-5/-10/-15%), horizon (10/20/60 trading sessions), target (`LOW_INTRADAY` or `EOD_CLOSE`), model (`HIST` or `REGIME`).
- **Investor-first display**: one selected model's forecast probability, change since previous issuance of the **same model/scenario**, session date, issuance time, and matured-event count. No meaningless headline difference between HIST and REGIME.
- History defaults to the selected model only; alternative model overlay is an optional diagnostic toggle. 3x3 risk matrix and cross-symbol comparison are secondary.
- Matured outcomes only: Brier score and empirical hit rate for **paired** HIST/REGIME predictions of the same matured events; prequential baseline Brier on matched HIST rows. No score or inferred accuracy when zero matched matured observations.
- Model probabilities are **raw, uncalibrated, not validated**. Forecast means **at least one threshold touch within N trading sessions**, not return at end of horizon. Neither model is a trading signal. Overlapping events are not independent.
- Automatic refresh every five minutes while the page is open, plus manual refresh. Daily job writes to the same database; dashboard reads it without scheduled synchronization.

## Secure deployment prerequisites

**Personal-use first.** Deploy as a separate Railway service in the isolated `alpha-os-shadow-research / research` project. Do not replace the daily worker. Do not expose a public domain until authentication is configured and reviewed. The link is not a security boundary: enforce HTTPS, password, secure cookie, edge authentication and rate limiting. Do not enable additional accounts yet; when sharing is needed, replace the single-password scheme with per-user identities, revocable access, and audit logs.

Set the following **secrets** on the new service, never in GitHub:

- `DASHBOARD_DATABASE_URL`: preferably a **dedicated SELECT-only PostgreSQL account** restricted to forecast, model registry, journal, outcomes and baseline tables; database must be `alpha_shadow_research`. Never grant access to licensed raw payloads.
- `DASHBOARD_PASSWORD`: private passphrase at least 24 characters.
- `DASHBOARD_SESSION_KEY`: independent random signing secret at least 32 characters.
- `PORT`: Railway-provided port, defaults to 8080.

Dockerfile path: `research/forecast_dashboard/Dockerfile` from repository root; service start: `python research/forecast_dashboard/server.py`; `/health` for liveness. For a standalone rootDirectory of `research/forecast_dashboard`, change Dockerfile COPY and start accordingly.

The API uses PostgreSQL transaction read-only mode and an 8-hour Secure / HttpOnly / SameSite=Strict signed cookie. No public API is available without login. All responses use no-store and a restrictive CSP; no third-party JS/CDN. A production review should additionally require Railway edge authentication / access control, HTTPS, and rate limiting. Avoid sharing passwords or DB credentials in chat.

## Validation checklist

1. Private deploy starts and `/health` returns 200.
2. Unauthenticated `/api/data` returns 401; wrong password returns 401.
3. Authenticated `/api/data` returns 216 numeric rows for latest 2026-11-16 session, 648 numeric records total as of 2026-11-17 (historical acceptance snapshot; actual counts may increase).
4. New daily worker issue appears in the dashboard after refresh, without changing dashboard code.
5. No raw prices, API tokens, payloads, or connection strings in HTTP responses.
6. Before sufficient matured outcomes, show "too early" rather than inventing accuracy.
7. No production changes, merges, trades, or automatic deployment of this branch.

**Note:** the worker's own `weekly_report` writes research reports; this dashboard never writes them.
