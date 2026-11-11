# PR28 supervised preparation — NOT RUNNING

Task: PR28 comment6743417658. Depends on PR26 head291762bb951ce806f7e289bd261e6797664e9dd7.
No production imports, migrations-on-start, live network provider or scheduler.
Source-contract blocker and raw field matrix: reports/daily-shadow-postgres-v2/.

Models: `python -m research.daily_shadow.artifacts` verifies frozen PR20/PR24 hashes
and creates immutable content-addressed per-event HIST/REGIME count artifacts.
Existing version filenames cannot change content. Actual preparation time is
recorded separately from fit_cutoff; training midnight-availability is explicitly a
REPLAY assumption, never genuine historical publication. All qualified/calibrated
flags false. `python -m research.daily_shadow.verify_preparation` reproduces222
versions without sockets. Do not recompute historical counts in a daily job; load
reviewed frozen files through load_artifact and register unchanged manifests.
Changed versions become parallel series; registration cannot overwrite old versions.

`python -m research.daily_shadow.coverage` reports222requested/0liveeligible/222NULL.
It is a registry/qualification assessment, not dated prospective issuance.
UnavailableLiveProvider has no network calls and never invents release/ingestion time.
No approved licensed publication/action contract exists, so no live adapter is wired.

Disposable PostgreSQL18 (PG16 regression also in CI), explicit local database
alpha_shadow_research, admin only for initial manual local migration:
1. Apply sql/001_isolated.sql then sql/002_contract_hardening.sql.
2. LOCAL/CI ONLY: apply sql/local_fixture_roles.sql; fake credentials are test-only.
3. Set ALPHA_SHADOW_TEST_DSN to localhost local owner for permission tests, and
ALPHA_SHADOW_STAGE_DSN to localhost alpha_shadow_test_app for rehearsal. Both name
only alpha_shadow_research. No DATABASE_URL lookup or Railway credentials.

    python -m unittest research.daily_shadow.test_core research.daily_shadow.test_postgres research.daily_shadow.test_reporting research.daily_shadow.test_preparation -v
    python -m research.daily_shadow.rehearsal

Rehearsal physically terminates its OWN synthetic LOGIN backend after a first
forecast insert; never signals another process, never grants pg_signal_backend.
Rolls back partial transaction and reconnects/retries. Full222blocked run plus
separate HIST/REGIME synthetic-contract scores0.5, correction archive, provider
failure, IMMATURE afterearlyhit, fullhorizon MATURED, label retry and hash chain.
No synthetic artifact/source can enter PROSPECTIVE mode. Real qualified model
registration requires the separate model registrar role; app writer cannot promote
itself. No group is superuser/tableowner/schemaowner. The owner can still bypass
triggers, so external anchoring is a future launch gate.

Backup: pg_dump schema alpha_shadow_v1, restore into NEW disposable database
alpha_shadow_restore in same local cluster (never existing application DB), then
set ALPHA_SHADOW_RESTORE_DSN to the same fake local LOGIN and run:

    python -m research.daily_shadow.backup_restore

This checks content/hash chain read-only with explicit loopback/name/user guards.
CI performs the actual pg_dump/createdb/pg_restore drill on both PostgreSQL16/18.
Initial local restore allocation was blocked by disk capacity (checkpoint retained).
After removing only this task owned test image/container, final PostgreSQL18-alpine
restore into a fresh DB passed:992audit rows/payloads and chain matched.
Cross-host PITR/WORM is not certified.
See separate Russian manual migration/access/backup/cost/alert/approval runbook.
