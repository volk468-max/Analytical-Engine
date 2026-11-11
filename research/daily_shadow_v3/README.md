# Offline/isolated research forecast preparation

No production import, subscription, cron, deployment or trade entrypoint. Scope:
[owner comment](https://github.com/volk468-max/Analytical-Engine/pull/28#issuecomment-6788172712).

See [Russian report](../../reports/daily-shadow-postgres-v3/executive-summary-ru.md)
and [manual disposable/approval checklist](../../reports/daily-shadow-postgres-v3/approval-checklist-ru.md).
Only `setup_fixture_db`, tests, `rehearsal`, and `backup_restore` are executable
preparation commands. Setup requires an explicit loopback disposable DSN; old
production DATABASE_URL is never inferred. Credentials in local CI are synthetic.

`EODProvider.collect(session)` returns `Snapshot` with separate legal reason,
source status, basis, retrieval/publication, revision, and private raw/action fields.
EODHD collection reads the environment secret only after a reviewed legal gate.
Default `Permit` is unqualified. Fictional fixture permission cannot authorize
real networking. Current actual provider and first-live decision: **NO-GO**.

`runner.run` defaults to SYNTHETIC; RESEARCH_FORECAST requires separate first-live
approval, a pre-registered LIVE legal capability contract, real transport and frozen
models registered before actual issue. Real decision/issue UTC comes after collection,
not a caller-supplied replay clock. No CLI grants this approval. `data_reviewed` and
`finalization_verified` are evidence-based human gates, never set by a passing fixture.
All source/model rights and independently reviewed source checks remain external blockers.

`resolver.resolve_once` reads the original encrypted anchor and appends a complete
full-horizon result; new revisions are stored separately. `ResearchStore.metrics`
reads latest outcomes and pairs HIST/REGIME on identical events, rejecting synthetic
and blocked evidence. Missing models have explicit unavailable audit identities and
NULL probability, never invented count banks. Portfolio A/B/C remain blocked.

Raw bytes/marks live in deletable encrypted `alpha_licensed_v3`; safe immutable audit
lives in `alpha_research_v3`. Permanent metadata/forecast retention also needs explicit
rights. Offboard only purges active vault rows; external backups/WAL/logs require an
independent receipt. Encryption is no retention exception. Restored license tables
are not fresh authority. All current fixtures are self-authored artificial values;
no real daily series or provider payloads are distributed here.
