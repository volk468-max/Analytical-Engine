# Validation and unresolved limits

## Automated checks

Final full-suite command:
`OPENBLAS_NUM_THREADS=1 PYTHONPATH=/tmp/alpha-risk-test-deps PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider`

**186 tests passed, 20 subtests passed**, including **26 new anatomy tests**.
No unresolved failed automated tests. One initial exact-float assertion was
corrected to a numeric-tolerance assertion; the final suite passes.

Offline study completed from frozen sources:
- 18 stocks: 3 primary and 15 additional; 142 non-nested principal episodes,
  including 38 primary-stock episodes; 710 presnapshots.
- 1,314 fixed cohort anchors; 5,792 matched/control records, with 921 explicit
  NO_MATCH entries. Some primary sideways cells have no eligible controls;
  they are not assigned invented frequencies. Expanded/all-stock cells remain
  separately available in matched-control-comparison.csv.
- 1,440 anchor-target and 720 exploratory path-target frozen model fits;
  no nonconverged fits. Original primary v3 states/scores match archived values.
- 34,380 anchor-target and 17,190 path-target daily probability records,
  stored as deterministic gzip CSVs; required event/control CSVs stay plain.
- 360 episode/hypothesis sensitivity records, 80 exploratory path comparisons,
  420 baseline metric rows and 672 stock/year stability rows.
- 0/4 original primary hypotheses meet the predefined incremental criterion.
  Exploratory path sensitivity does not replace or independently confirm it.
- Price/action/raw-response consistency, original-source hashes, final output
  hashes and git whitespace checks verified. Plots generated and inspected.

Data-source checks verified identical observed QQQ/SOX calendars and finite
nonnegative volumes. Added strict missing-branch/nonfinite-volume guards do not
alter these observed rows; incomplete data are unknown rather than false.
Discovery outcome horizons and discovery catalogues are truncated at December2022.
The separate target-sensitivity protocol (commit3d53761) was added after the first
primary result, before its own calculation, and is explicitly exploratory.

Checks cover causal feature-prefix invariance, confirmed-low timing, future
benchmark/yield exclusion, incomplete windows, nested episode deduplication,
recovery/censoring, episode sensitivity, split-unit invariance, correct training
publication cutoffs, no future outcome/peak/trough predictors, train-only
standardization, unavailable hypotheses, true calendar blocks for sparse controls,
actual snapshot dates, nonoverlapping events and unchanged original v3 modules.

## Unresolved historical evidence

- No independently attested historical price/corporate-action/publication archive.
  Raw source/action/checksum consistency and absence of obvious split-sized price
  jumps are checked, but do not prove vendor adjustment correctness. Volume ratios
  use provider-reported history; historical volume revision/adjustment vintages
  are not independently verified.
- The primary catalogue starts with observable2020 history; it cannot establish
  lifetime ATHs before that date. High/low sensitivity uses close-confirmed
  recovery and does not invent the intraday order of extremes. Incomplete
  prehistory, open episodes, warmup and missing matches remain visible.
- Fixed2026 surviving companies are not a point-in-time sector universe.
  Semiconductors are a fixed proxy panel, not whole-market breadth. PLTR has a
  shorter warmup, explicitly flagged. No delisted-company comparison is present.
- FRED DGS10 history is retrospective, with assumed conservative two-session
  publication lag. No ALFRED/original H.15 vintage attestation. EPS, guidance,
  forward valuation and original news archives are absent; H4 cannot be tested.
- 2021–2026 was previously studied. Chronological walk-forward prevents future
  labels entering training but is not an untouched independent holdout.
- Synchronous blocks preserve many common shocks/overlaps; four held-out years
  contain few120-session blocks. Intervals condition on already fitted models
  and do not include all training, research or regime-change uncertainty.
- Case/control matches can repeat and are descriptive; inverse-reuse weights do
  not make them independent. Empirical population risks use the full fixed grid,
  never a case-enriched matched sample. Unknown conditions are not false flags.
- A positive conditional association does not imply incremental prediction,
  causal explanation, investment effectiveness or readiness for live use.

No signal parameters, production services, live recommendations, databases,
merges, deployments, sizing policies or real trades are changed/performed.
