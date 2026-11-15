# Worker fix protocol — 2026-11-15

Base/deployed revision f066a5ecc4dc8c1984905b748d5781fe7235bb94, new fix branch
from research/daily-shadow-postgres-v1. Scope read-only Railway investigation,
mocked tests, code and dependent PR only. Deployment/config changes/manual writes
require a separate explicit owner approval under the current task.

Evidence first: inspect structured log attributes as well as message. Deployment
SUCCESS and DNS resolution are not forecasting/API success. Nov12 failed with
SOURCE_STILL_REVISING; Nov13/14 have ISSUE216 and ACCEPTANCE_SQL432, earliest UTC
2026-11-13T02:05:45.498639+00:00. These are application SQL-log observations, not
fresh independent SQL. Private DB has no TCP proxy; no authenticated CLI/query tool
available here. Mark direct SQL counts/distribution/duplicates UNVERIFIED.

Confirmed failed guard compares whole raw response bundle including the entire US
symbol directory; it aborts on any byte difference without retry or persisted failed
pair. The lost snapshots prevent identifying the historical changed field. Do not
claim actual quote revision, metadata-only drift, invalid auth or bad cron as proven.

Keep 0 2 * * 2-6. It maps to21:00NY winter/22:00summer on previous local day, after
20:30 gate. Compare canonical validated forecasting/quality inputs of SIX tickers,
not unrelated global directory entries/JSON formatting. Include OHLCV and corporate
split/dividend lineage, exclude unused total-return adjusted_close and retrieval time.
Preserve both original raw snapshots encrypted, even when readiness fails. Allow at
most3consecutive readiness pairs >=60s; meaningful instability/stale/missing inputs
remain fail-closed. Never amend original forecast or fill a failed historical day.

Add structured run lifecycle, human message plus attributes, UUID/UTC, sanitized
exception chain/traceback (no locals/source text), explicit success/partial/failure
codes. HTTP logging includes actual status/endpoint/attempt/latency, no query/token;
3bounded attempts for transient failures, no retry401/403, honor bounded Retry-After.
Keep immutable model/version/date uniqueness and transaction atomicity. Existing
partial batches are not success; missing optional history is partial, not swallowed.
Expand read-only persistence audit by actual schema/columns. All real acceptance
items remain UNVERIFIED until approved deployment and independent SQL/live inspection.

Evidence qualification: the old second snapshot legal_reason was not checked before
revision comparison. A blocked second snapshot/revisionNULL is another possible
path to the same error, not excluded by logs. Do not assert two completed HTTP
bundles for the failed run. New per-fetch checks keep the specific legal error.
