# Validation

## Execution status

Executed full suite:
`PYTHONPATH=/tmp/alpha-risk-test-deps PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider`

**133 tests passed, 20 subtests passed**, including **29 economic tests**.
No failed automated tests. The 29 economic tests cover causal prefixes, signal
publication gates, next-open/gap fills, constant-REDUCE deduplication, CRITICAL
escalation/direct entry/control, short-state chatter, rearming and the 50% floor,
all three recovery confirmations, cash-limited partial buybacks, fees/slippage,
delays 1/2/3, cancellation and conflicting orders, unavailable data, unfinished
cycles and end-of-window orders, retrospective trough confirmation, early
repurchase effects, segregated dividend entitlements, split-unit invariance,
constant-price cost drag, exact NAV and economic attribution, grouping first
REDUCE signals, account-specific horizon censoring, exported account invariants,
and unchanged v3 code/signals.

Offline regeneration:
`PYTHONDONTWRITEBYTECODE=1 python -m aae.research.risk_v3_economic_study`

- 189 summary rows: 105 independent accounts and 84 inherited subperiod slices.
- 2,993 primary/control trades; 40,887 daily-equity records.
- 4,430 signal/lot economics rows and 2,561 FIFO recovery matches.
- All 55 original significant C walk-forward events across six policies:
  330 drawdown-protection rows, including censored recoveries.
- 216 fixed size/recovery/CRITICAL/delay combinations and 18 price-only controls.
- Every primary/sensitivity terminal difference reconciles to lot contributions;
  all recorded source/output SHA-256 checks and git whitespace checks pass.
- Equity/share-position and drawdown plots generated and visually inspected.

Protocol frozen in commit `0190497` before the first economic calculation.
Unchanged v3 inputs are hash-verified before each regeneration. No signal
parameters, recovery thresholds or principal tranche sizes were optimized from
trading results.

## Research/data limitations still unresolved

- No independently verified historical price, corporate-action or publication
  vintages; all prices and dividends are the unchanged retrospective PR #5 pack.
- Source OHLCV, corporate-action metadata, New York opens, publication gates,
  split-date continuity and signal-to-price matches are checked. This does not
  establish exchange calendar completeness or dividend adjustment correctness
  against an independent archive. Price-only controls expose dividend sensitivity.
- Actual dividend payment dates are missing. Gross ex-date receivables count in
  equity but remain unavailable for trading, preventing premature funding of
  buybacks. This differs from an investable account with actual payout dates.
- Early closes inherit conservative PR #5 timestamps. Raw source prices are not
  modified. No same-close fills or unavailable next-open prices are backfilled.
- Signal selection is chronological and fixed, but both signal research and these
  execution-policy choices are retrospective. No reserved prospective holdout,
  execution impact model, significance test or proven investment effectiveness.
- Confirmed troughs, future growth/false labels and eventual peak recoveries are
  evaluation only. Incomplete troughs, risk cycles and +20-session outcomes are
  censored. Positive protection at an intermediate trough is not final profit.
- Missing capacity to buy back shares is retained as a deficit. Lot-level FIFO
  results explain NAV differences exactly; overlapping trough-protection and
  gross missed-growth measures must not be added to portfolio profit/loss.

## Safety scope

Only research files, research tests and generated reports are added. Frozen v3,
Decision Engine, Tactical Risk Overlay and their thresholds are unmodified. No
merge, deploy, production-database operation or real trade is performed.
