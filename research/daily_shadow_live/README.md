# Owner-authorized isolated daily worker

[Deployment handover](../../reports/daily-shadow-live-v4/railway-handover-ru.md).
This service has its own Railway config and Dockerfile; root production railway.json
is unchanged. Exact Railway project/environment/service IDs are hard gates.

Bootstrap applies 001–004 once with hashes, populates pinned calendar and genuine
frozen models. Runtime performs paid-account metadata checks against the owner
confirmation, same-session readiness, paired HIST/REGIME, atomic baseline capture,
full-horizon outcomes and private weekly reports. No fixture import in production
runtime; no trades. Actual API replies, secrets or reconstructible series never
belong in Git. Historical comparison is private, exploratory revised-history replay.

Deployment approval was rejected during this task. Staged config is not live;
no actual first forecast has been accepted. Read the handover before any apply.
