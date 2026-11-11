# Daily shadow research — NOT RUNNING
Independent from production aae; base unmerged DraftPR26. No live provider configured,
no service/cron/DB created on Railway. All222series in default demo are BLOCKED/null.

    python -m research.daily_shadow.demo
    python -m unittest research.daily_shadow.test_core research.daily_shadow.test_reporting -v

PostgreSQL integration must use a DISPOSABLE LOCAL Postgres16 instance/database
named alpha_shadow_research. Tests reject remote hosts. Apply sql/001_isolated.sql
only there as local test owner; never point it at production. Set the explicit
ALPHA_SHADOW_TEST_DSN (never DATABASE_URL) and run:

    python -m unittest research.daily_shadow.test_postgres -v

Dependencies in requirements.txt. CI uses ephemeral service container, no external
providers. Missing DSN skips integration with an explicit message, not a success
claim for Postgres. No automatic remote migrations or live entrypoint exists.
Provider is a Python Protocol, not a production collector integration. Fixture
implements it without network; real licensed provider/release metadata/actions
need separately reviewed adapter before go-live. Do not qualify frozen PR20/24
Yahoo archive as live input. Current model registry qualified=false, all numerical
forecasts unavailable. raw_estimate implements frozen HIST/REGIME only for declared
tasks, maturity-checked immutable model artifact; calibratedP alwaysnull.

Runner accepts explicit session and UTC times for tests; non-synthetic mode also
requires live_approved=True ONLY after human rollout approval. Prospective DB rows
cannot be backdated >10minutes; backfills use separate run mode and model series,
excluded from prospective metrics. Plan is not permission to launch a job.

Idempotence: one key per session/target/symbol/modelversion. Retry of same completed
run returns original IDs. Same modelversion/different params or source revision
raises; use explicit correction event/new parallel series, never overwrite NULL
or a prior forecast. Bounded retries occur BEFORE first commit. Blocked first
issuance is retained; late recovered evidence does not become an earlier forecast.
Global DB advisory transaction lock serialises chain/unique inserts across workers.

Outcome resolver pure function requires full future session calendar/qualified
marks. Store.outcome(...,vintage=...) archives actual outcome raw response and links
new lineage transactionally; IMMATURE/UNRESOLVED and corrections append separately.
No labels pulled from synthetic mocks become prospective evidence. Reporting must
receive original prospective series, order outcome revisions by immutable seq;
no mixing symbols/targets/modelversions. See sql/002_readonly_reports.sql.

resolver.resolve_once reads the original forecast from PostgreSQL, uses its frozen
anchor/basis and archives the outcome response bundle. OutcomeProvider is a separate
interface, not a configured live source. A PROSPECTIVE outcome job has the same
explicit live-approval guard. No resolver scheduling is installed.
