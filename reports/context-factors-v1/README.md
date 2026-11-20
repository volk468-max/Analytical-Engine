# Q014-v1: context factors and model redundancy audit — 2026-11-20

## Findings and recommendation

New owner question: audit model overlap before connecting signed LLM factors and
Seeking Alpha observations to daily calculations. This is new context integration,
not a repeat of historical accuracy research and not an owner decision to retire
any particular model.

Audit base and actual Railway source: `fd37ef2d347663aaf24b086c6db8d41928a6ea12`,
branch `research/daily-forecast-export`. Read-only Railway describe-service found
live deployment `e244eb8e-4dfa-4754-a037-66a07ee1221b`, SUCCESS, created Nov18.
This is deployment/config evidence, not a new execution or outcome audit.
No deployment/configuration/database/schedule was changed in this task.

| Model | Mathematical role | Recommendation |
|---|---|---|
| VOL | L2 logistic on log RV20; raw daily refit | Keep simple benchmark |
| RISK_FORECAST | Empirical technical_combined cells, Beta prior/shrink20 | Technical challenger; test incremental value |
| ENSEMBLE_RISK | Equal mean of technical_combined, v3_state, technical_plus_v3, empirical volatility and QQQ regime | Experimental comparator; not an independent sixth vote |
| MARKET_PRECURSORS | L2 raw logistic on own/market/sector prices and trends | Market challenger; investigate probability coherence before promotion |
| HIST / REGIME | Frozen legacy baselines | Preserve version/history; no retirement decision in this audit |

The RF estimate is exactly the technical_combined component of Ensemble for the
same training frame/target. Synthetic parity is tested. Ensemble's empirical
volatility component is NOT the separate VOL log-RV logistic estimator. Common
price inputs do not establish duplicate models. No complete forecast model was
merged/deleted or disabled. Do not combine RF and Ensemble as independent evidence.

The archived Nov17 CSV was inspected locally (516 rows; hash in sanitized-audit).
None of six model pairs has identical output on its common 120 targets. This is
a descriptive single-session comparison, not incremental predictive accuracy.
MDP has three adjacent threshold nesting violations. Historical rows are not
corrected/overwritten. Enhanced output flags BASELINE_INCOHERENT and withholds
its affected group rather than silently treating contradictory risks as valid.

Earlier pinned [ensemble research](../../docs/alpha-os-knowledge/research/Q003-v1.md)
reported 0/162 primary successes; this is not proof that every current daily
variant is useless. [Market precursor history](../../docs/alpha-os-knowledge/research/Q004-v1.md)
remains negative/unqualified. No newly mature outcomes are evaluated here.

## Implemented research path

`context_factors.py` normalizes six signed per-instrument LLM factor scores and
three SA revision features (EPS change, revenue change, analyst revision breadth).
Total LLM score and its components are not both included. Quant/Momentum grades
are not blindly multiplied into probabilities. Quality/valuation, earnings
surprises, guidance and event calendar remain candidate extensions, not secretly
active inputs. Alerts feed the evidence-based LLM stage, never the numerical
adapter as instructions or trusted verified financial observations.

Normalized SA input requires exact fiscal period/accounting basis, original
publication and retrieval UTC, canonical source URL, source type MANUAL_VERIFIED
or LICENSED_EXPORT, and VERIFIED_OBSERVATION. No website scraper or paid API was
provisioned. Premium browser access is not proof of licensed API delivery.
Missing/stale/partial/low-confidence inputs do not become neutral zeros.

A separate per-symbol/model/label/threshold logit-offset research estimator fits
`logit(p_context) = logit(p_baseline) + b0 + b*x`. Weights are learned with L2,
not chosen from the sign of an expert score. Training requires at least 252
distinct archived sessions and >=10 events/non-events for the exact target;
labels must mature before fit. This is a conservative engineering support gate,
not evidence that 252 correlated sessions are statistically sufficient. Model
artifact and feature hashes, target, timestamps and fixture boundaries are
checked. No fitting or scoring on real private historical context was performed.

Every artifact remains UNVALIDATED_CONTEXT_RESEARCH, qualified=false. No automatic
promotion or improvement claim is possible. Prospective archive provenance must
be independently audited; hashes/declared timestamps alone cannot prove PIT.
Chronological purged validation with an untouched holdout, block confidence
intervals, Brier/log loss/calibration and ablations are still required.
Independent target fits can violate nesting; contextual export additionally
withholds inconsistent enhanced groups. A future joint coherent estimator is
preferable to hiding violations with an ad hoc sort.

`forecast_export.export_session` retains its existing complete baseline CSV, then
optionally invokes `context_runtime.export_context`. Disabled by default. This
adds no SQL schema/write and no replacement of 516 baseline rows. The separate
CONTEXT_EXPORT JSON log has its own SHA256/chunks/READY and per-row reasons.
A failure in this extra stage does not suppress baseline READY. No downstream
Drive automation was changed to accept the new format.

## Actual readiness, not a deployment claim

The real coefficient run `impact-20261120T074017Z-initial-v1` has cutoff
2026-11-20T07:40:17Z, ten partial/LOW-confidence numerical records and 49 additional
null records. It cannot affect already-issued 02:xx UTC baseline forecasts.
It also has missing constituent factors. Complete normalized SA revisions for
the ten names, a delivery channel to the worker, and a trained prospective
context artifact are absent. Therefore current effective state is
COEFFICIENT_NOT_CONSUMED_BY_ALPHA / BASELINE_ONLY. Not a first enhanced forecast.
There is no existing 30-session LLM coefficient; those outputs explicitly report
NO_30_SESSION_COEFFICIENT. Do not stretch the 10-session score across horizons.

Regular sequence requires sources (including Junk alerts) -> verified normalized
snapshot and saved coefficient -> worker baseline + separate enhanced research ->
interpretation. To affect the existing 05:00 Moscow worker, its inputs must be
available BEFORE that execution; the 05:30 export/audit cannot retroactively alter
it. Schedules were preserved. Analyst event/sentiment scores are not expected
returns, volatility estimates, causal effects, or calibrated probabilities.

## Run / delivery contract

A private JSON bundle contains `session`, `coefficients` (existing schema1.0),
`seeking` (SA_CONTEXT_V1), and optional `artifacts` from fit_correction. Never put
licensed snapshots, mail, tokens, or real context values in this public repo.
Tests contain only self-authored synthetic observations.

Opt-in research worker settings, not applied:
- ALPHA_CONTEXT_RESEARCH_ENABLED=true
- ALPHA_CONTEXT_BUNDLE_PATH=/private-mounted-input/context.json

Bundle must already be delivered securely to that local path. This implementation
does not invent an upload endpoint or read credentials. A dated immutable bundle
and manifest/checksum delivery must be added before scheduling live consumption.

Offline private calculation, exclusive-create output (no baseline overwrite):
`python -m research.daily_shadow_live.context_runtime --baseline PRIVATE.csv --bundle PRIVATE.json --output NEW_PRIVATE.json`

The full normalized contract is exercised in test_context_factors.inputs; every
SA field has value, fiscal_period, accounting_basis, source_url, source_type,
published_at_utc, retrieved_at_utc. Four fields: eps_revision_30d_pct,
revenue_revision_30d_pct, eps_up_revisions_90d, eps_down_revisions_90d. Up/down
counts must refer to the same stated fiscal year as EPS/revenue revisions.

## Retirement acceptance before any removal

Keep immutable baseline vintages. Compare RF/MDP/Ensemble/VOL on identical mature
targets, masks and first-available vintages. Separate LOW_SUPPORT and blocked
coverage; do not reward a model for refusing difficult cases. Use synchronous
blocks for overlapping horizons/correlated symbols, purged chronological splits,
fixed metrics and multiplicity correction. Test each ensemble component and
new feature family by ablation. Retire only after no defensible incremental
benefit or a strict exact-duplicate proof, preserving ability to replay histories.
No new data acquisition, trades, API purchase, merge or deployment occurred.

Source PRs checked open/draft/unmerged Nov20: #34 head
f4042bf070c9d8ef1640d82bf72b5117a25484f1; #36 head
f2e17ec10d90326edaf7baf0328d345c40a08c71; #38 head
5ded52b0f309874e3ca08016be9bb87cd8fdffd3; #40 head
fef6da030befa977ed352473482f8eec040e835a; #42 head
2253ba2b2069a87d1b6b299a73505ecf3442cdae. Source PR heads differ from deployed
calculation SHA and are not deployment evidence. Existing Q013 records retained.

## Validation checkpoint
32 new context tests +9knowledge tests PASS; existing model suites run through
canonical python -m unittest:80run,56pass,24database-dependent skips,0failures.
A broader pytest invocation exposed existing package-alias/mock-patching failures;
the canonical existing CI unittest invocation passes. No missing DB tests are
claimed as passed. Offline knowledge check passes; online check recorded separately.

## Publication checkpoint
Local implementation commit was created, but external git push was rejected by
automatic approval review: external repository publication authorization and
research artifact privacy concerns. No alternative write path was attempted.
No PR exists for this implementation yet; prepared local changes await explicit
publication approval. This is separate from any future deployment decision.

Online validator was attempted and interrupted with exit130 after no completed
result was obtained. No online validation PASS or diagnosis of network failure
is asserted. The related PR states/source were separately read via connectors.


### Q014 publication approved — 2026-11-20
Owner explicitly approved publishing the prepared branch to GitHub.
Draft PR45 https://github.com/volk468-max/Analytical-Engine/pull/45 is open,
unmerged; published implementation dc93b42e7d636b3a7494a20cbce0c692008f1b95.
This supersedes LOCAL_ONLY/publication-block status above; previous rejection
is preserved as history. Shell push lacked credentials; connected GitHub service
published the approved identical net changes. No merge/deploy or runtime
activation; actual worker remains fd37ef2d347663aaf24b086c6db8d41928a6ea12.
Context remains BASELINE_ONLY pending verified inputs/delivery/training.
