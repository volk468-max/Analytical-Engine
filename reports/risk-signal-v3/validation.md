# Validation and limits

## Automated checks

New tests cover normal HOLD, REDUCE with low VIX and intact support, grouped
confirmation and capped correlated contributions, CRITICAL, mandatory missing or
stale data, future publications, optional VIX exclusion, explanations, rejected
forward fields, absent sizing/execution, invalid values/configurations, Wilder
RSI, prefix invariance after changing future prices, future benchmark exclusion,
split-scale invariance, censored forward horizons/events, false-warning labels,
reporting-boundary entries, negative warning leads, training/test separation,
actual exported signal metadata and unchanged v2/Decision Engine/PR2/PR3 modules.

Executed `PYTHONPATH=/tmp/alpha-risk-test-deps PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider`: **104 passed, 20 subtests passed**. The 27 v3 tests also passed separately. No automated checks failed.

Executed `PYTHONDONTWRITEBYTECODE=1 python -m aae.research.risk_v3_study` offline: 21,717 daily records, 444 event rows, 933 entry outcomes, 12 frozen walk-forward folds. Source pack
hashes are checked by the loader; code and generated output hashes are recorded in
run.json. Offline regeneration uses no production services.

## Unresolved historical validity checks

- Independent point-in-time publication vintages have not been obtained. Yahoo
  split-adjusted OHLC and CBOE history are retrospective downloads. Assumed next-
  midnight availability is conservative scheduling, not evidence of actual
  historical publication or revision timestamps.
- The source provider's corporate-action and price history is retained, but has
  not been independently reconciled against an exchange-licensed archive.
- Rules/catalogue were designed after historical outcomes were observable.
  Walk-forward selection prevents computational future-label leakage but is not
  pristine prospective out-of-sample validation. A fresh future holdout is needed.
- Distinct indicator families remain correlated. Events and overlapping forward
  horizons are dependent; percentages are descriptive, without reliability or
  statistical significance claims. False-warning labels depend on the explicitly
  chosen 20-session horizon and additional 10% loss definition.
- Last 5/10/20-session outcomes and unfinished episodes are censored rather than
  extrapolated. 2026 is incomplete. No live recommendation, trade-size, execution
  or profitability backtest is included.

No merge, deployment, database write or trading operation forms part of this study.
