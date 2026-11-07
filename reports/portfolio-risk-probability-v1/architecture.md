# Research architecture / phased gates

snapshot+source qualification -> synchronous no-trade total-return path label ->
baseline path distribution -> PIT-qualified conditional logit model -> evaluation
and calibration -> experimental policy ledger -> append-only shadow forecast log.

Implementations are intentionally small/offline, no imports from aae/production.
nav_path reprices fixed shares with explicit split/dividend/FX/cash events; input
mark completeness/action evidence must be qualified by provider, not inferred.
Daily marks cannot resolve a negative intraday ANY-point label. Full60-session
maturity required. HWM supplied only from documented unitised cash-flow-adjusted
history; drawdown_budget never infers HWM or promises15% protection.

empirical_synthetic computes frequency and terminal ES from joint NAV paths;
these paths already contain cross-asset dependence/cash/FX. It is a fixture tool,
not an estimator trained on actual returns, no CI or calibrated-risk claim.
Real HIST/VOL/regime fitting, calibration, baselines/12 contrasts and all performance
metrics BLOCKED. Future implementation must use the frozen protocol, all eligible
no-event dates, not crisis-only controls. None of PR20 market probabilities can
be substituted for portfolio probability. Logit attribution is conditional, not
causal, and not unique among correlated features; group duplicates rejected in
prototype, richer jointly trained grouped models require qualified archives.

Policy is an offline candidate-state simulator, not a broker/execution ledger.
Explicit cumulative targets, confirmation, cooldown and next-open pending intent;
settle requires the exact pending target and earliest next session. It tracks prior
trims and reentry intent, but real cash/concentration/tax/partial fills need a fully
specified portfolio ledger before economic evaluation. No real policy call emits
an intent, even if caller claims validated=True. Configuration thresholds35/51/60
are experimental, trim sizes null outside named synthetic demo. Ladder separately
tests fixed-inception-anchor original-unit targets5% per2% move, floor50%; exact
production ladder semantics/fees/cash-constrained fills are not reconstructed.
B&H/risk-matched overlay/ladder/probability economic comparison and combinations
NOT DONE/BLOCKED; no fabricated CAGR/DD/ES/turnover/profit. Such comparisons need
parameter freeze and data qualification before results, not hindsight fitting.

Shadow mock writes only a local artifact. Future record requires UTC actual release
and ingest <=decision<next open, snapshot id/hash, base/model/final P+CI (nullable),
provenance/staleness, code/model/protocol versions, conditional log-odds terms,
immutable previous hash. Labels/corrections separate, full maturity and references
to old records. No live process or prospective observations collected. Hash chain
is tamper evidence, not secure immutable storage by itself (external anchoring,
access controls and signatures require separately approved infrastructure).

Blinded power plan replaces impossible2-year/30-rare-cluster requirements: first
measure usable PIT capture/composition stability and block variance; simulate
1% Brier alternatives with Holm12 at80% power and arrival-rate uncertainty. Publish
feasibility/sample-length before efficacy monitoring.90days is data-quality pilot,
not promised statistical validation. No efficacy peeking or threshold selection.
