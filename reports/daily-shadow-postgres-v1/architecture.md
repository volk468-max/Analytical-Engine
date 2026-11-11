# Issue27 — daily prospective shadow design (NOT RUNNING)

Base PR26 head82eebbd95579c022040065f67e30c369d0999906, not merged. PR20/24 frozen
research sources retained, no historical qualification magically upgraded. New
independent package, no production imports. No source is configured/approved for
live ingestion yet. All default outputs BLOCKED/null, no fake calibrated51%.

Pipeline: explicit provider interface -> archive raw bytes/SHA/publication+ingestion
and licence/action evidence -> session/quality gate -> pinned HIST/REGIME model
artifact -> atomic append-only PostgreSQL event+typed projections -> later resolver.
No same-close fills; decision after close and publication, issued after ingestion,
recorded_at server-generated. Backfills/retries cannot claim earlier issuance.
Session plan: proposed23:30UTC weekdays, exchange_calendars XNYS/XNAS checks,
holidays/weekends health rows only, early closes/DST actual exchange schedule.
Bounded provider retries, durable failure health; no last-price forward fill.

Universe6symbols x LOW_INTRADAY/EOD_CLOSE x5/10/15 x10/20/60 xHIST/REGIME =216
requested series plus A/B/C EOD_CLOSE10/60 x2 =6. Unsupported models/targets persist
null+reason. Existing PR20 supports only its predeclared tasks; no extrapolation.
Current provider/PIT/action gates block ALL222series. No prospective rows exist.
Portfolio snapshot factory supports exact A/B/C, fractional100kUSD, immutable
weights/cash/units, C trailing252totalreturns min200valid, deterministic caps10–50.
No dynamic in-window rebalance. Portfolio resolver consumes separately qualified
synchronous EOD total-return NAV, never sum(assetLow), no custom secondary targets.

Migration is a design file only, never automatically applied to remote DB. New
schema alpha_shadow_v1 in NEW isolated DB preferred. One global append-only audit
chain, advisory transaction lock, server timestamps, per-stream idempotency keys;
canonical JSON text+SHA binds payload/previous hash. Typed tables reference events.
Different content at same key raises conflict, not overwrite. No UPDATE/DELETE/
TRUNCATE by application role, triggers also block modifications. Model versions
immutable: params/code/source hashes, no latest mutable model. Outcomes/corrections
append new events; original forecast never changes. Chain protects against ordinary
app tampering, NOT DB owner/superuser: daily offsite signed/WORM anchor needed
before strong immutability claim. Transactions rollback run/vintage/records together.

Resolver requires exact nextN sessions fully published even after early hit, matching
basis/actions; low vsclose distinct, MAE andtime-to-hit. Missing/revision/split basis
conflict =>UNRESOLVED; immature attempts append status, later mature records append
separately. Corrected evidence supersedes via separate correction references.
Performance reports use ORIGINAL issue-time forecast and latest explicit resolved
label, retain prior versions. Data-quality metrics separate from model quality.

False Signal Anatomy follow-up explicitly deferred (Issue27 permits): original
SPY2164flags/297hits/1867nonhits; UP55/864 DOWN136/492 MIXED106/808 are dependent
stock-days, not episodes. Before follow-up freeze0–2/2–5loss, latehit11–20/21–60,
rebound/rally groups, clusteredalerts and controls; latehit never upgrades original
10dFP. No current efficacy or policy claims. No automatic trims/ladder calls.
