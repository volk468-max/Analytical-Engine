# Risk Forecast v1 validation

## Automated and reproducibility checks

Final full suite:
`OPENBLAS_NUM_THREADS=1 PYTHONPATH=/tmp/alpha-risk-test-deps PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider`

**160 tests passed, 20 subtests passed**, including **27 new forecast tests**.
No unresolved failed automated checks. Weighted/tied ROC-AUC and average precision
were independently cross-checked against scikit-learn to tolerance 1e-12.

Offline regeneration completed with `OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python -m aae.research.risk_forecast_study`:

- 39,366 anchor/horizon/threshold rows, with separate UP/DOWN probabilities.
- 216 frozen stock/task/year probability banks, each containing eight estimators.
- 576 stock/task/model metric rows; 1,080 paired baseline comparisons.
- 2,032 reliability bins, 288 state-frequency rows and 828 exact-score rows.
- 54 block-length sensitivity rows; 2,304 yearly metric rows.
- 1,447 error-analysis records and 999 Sep–Oct diagnostic rows.
- **0/18** primary tasks meet the predeclared incremental-information criterion.
- Final reliability plots were rerendered from the checked CSVs with matched
  model/interval colors; probability/label/metric outputs were not changed.
- All recorded source/output hashes and whitespace checks verified. The protocol was frozen in commit `8b22cf4` before forecast calculations.
No probability bins, shrinkage, risk thresholds or significance criteria were
selected by 2026 results.

New checks cover anchor-candle exclusion, path hit versus terminal return, both
barriers and first-hit order, ambiguous same-day bars and opening gaps, incomplete
horizons, future-prefix and unit-scale invariance, publication-based horizon
purging even after an early hit, cutoff boundaries, fixed fitting, immutable
predictor whitelists, backoff/LOW_SUPPORT, independent UP/DOWN probabilities,
known Brier/log-loss/ROC/AP values and tied/one-class cases, synchronous cross-stock
calendar resampling, contiguous circular blocks, reduced effective N under serial
dependence, paired identical models, multiplicity correction, unconstrained score
slopes, exported training maturity/censoring and unchanged frozen v3 sources.

A unit-scale test initially detected floating-point handling of exact threshold
touches. It was corrected with a relative price tolerance of 1e-12, preserving the
inclusive mathematical barriers; all outputs were then regenerated. No signal
thresholds were modified.

Source pack/raw outputs are SHA-256 verified before replay. Held-out C levels and
scores must match the original annual walk-forward outputs. Fit-audit records
last horizon publication <= cutoff and excludes all still-unmatured anchors.
Future OHLC/barrier labels do not enter ForecastFeatures or predict().

## Unresolved validity checks

- Barriers refer to reported daily OHLC; unobserved overnight or extended-hours
  paths cannot be reconstructed.
- Independently attested point-in-time price/action/publication vintages and an
  exchange-calendar completeness audit remain unavailable. Existing retrospective
  provider split-adjusted OHLC and next-midnight availability assumptions are
  inherited without modifying source data. Targets are price barriers, not
  dividend total returns or trading profits.
- Probability fitting is strictly chronological, but the signal catalogue and
  present research design were developed after history was observable. There is
  no pristine prospective holdout or evidence of investment effectiveness.
- Bootstrap confidence intervals condition on already fitted models and this
  vintage; they do not include all training/selection uncertainty. Synchronous
  blocks preserve overlaps/common shocks but assume more stability than the
  changing market regimes guarantee. Year and block-length sensitivity are
  descriptive safeguards, not proof of independence.
- Effective N is a capped HAC diagnostic for regular daily panels. Irregular
  conditioned cells report counts, block counts and uncertainty flags rather than
  an invented effective N. Sparse joint cells, rare outcomes and wide intervals
  limit probability reliability. LOW_SUPPORT numeric estimates are research
  audit values, not confident actionable forecasts.
- Holm correction applies to the 18 primary joint-technical-plus-v3 comparisons;
  per-stock comparisons, state/score bins and monotonicity slopes are exploratory.
- Incomplete horizons retain observed partial hits but null primary labels and
  terminal returns; same-day unknown barrier order is explicitly flagged.

Only new research code, tests, optional research dependencies and reports are
added. Existing Risk Engine/Decision Engine and investment recommendations are
unchanged. No economic simulations, orders, merge, deploy or production writes.
