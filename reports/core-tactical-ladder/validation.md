# Core + Tactical Ladder v1 — validation

Final automated suite: **97 tests passed, 25 subtests passed**. No failing or
skipped tests. This includes 41 new Ladder tests and the 56 tests on the base
feature/risk-backtest-v1 branch. PR #3 diagnostics are a separate branch and are
not required by this research.

## Requested behavioral checks

1. Sequential declines sell fixed ORIGINAL-unit tranches and stop at the Core floor.
2. Growth after reductions queues purchases from the last actually executed fill.
3. Decline / partial bounce / renewed decline produces deterministic alternating actions.
4. Small oscillations do not create threshold trades.
5. Lower bound freezes the reference instead of following an unknown trough.
6. Full package restoration stops buys and freezes the reference instead of trailing a high.
7. A gap across multiple levels executes one tranche at the next available open.
8. No-cash buys are blocked; affordable fractional partials and whole-order rejection are tested.
9. Changing future closes/opens cannot change earlier references, signals or account marks.
10. Fills occur strictly after their signal publication. The daily adapter explicitly rejects
    feeds published after the following open, including across chunk boundaries, rather
    than misordering opens and close valuations. General asynchronous feeds are unsupported.
11. Commission, adverse slippage, affordability and cash conservation match analytic examples.
12. Chunked simulation preserves cash, units, reference and pending orders exactly; actual
    continuous episode rows reconcile with the uninterrupted account journals.
13. Filled order IDs and session fills are unique across all 38,305 reported executions.
14. A known split prospectively adjusts shares, original-unit limits, reference and pending
    quantities without creating gains or a false signal. Duplicate/late split metadata are
    rejected; split-normalized FIFO costs are tested.
15. Every reported account mark equals cash + shares × market price, preserves nonnegative
    cash and respects Core/maximum quantity bounds.

Additional checks cover lot rounding, one-shot partial cancellations, terminal pending
orders, CAGR/Sharpe/Sortino undefined cases, drawdown duration, initial-capital recovery,
complete parameter-grid preservation, >=4 completed-cycle coverage (actual: 7), regime
coverage, exact cash/share decomposition, inherited FIFO ledger boundaries and unchanged original engine/executor hashes.

Python source compilation, input/source/output SHA-256 checks and staged Git whitespace
checks passed. Plots are exported as standalone PNG and SVG using matplotlib.

## Research coverage and execution assumptions

- AMD: 1,458 completed OHLCV sessions, 2021-01-04 through 2026-10-22.
- No interpolated sessions or unfinished 23 October prices enter any simulation.
- Provider reports zero in-window splits and dividends; every retained adjusted close
  equals the corresponding OHLC close. Raw source and action metadata are preserved.
- 7 completed >=10% peak-to-recovery cycles, the open cycle, all 24 calendar-quarter
  windows and the mandated September–October diagnostic; 132 A/B strategy/episode rows.
- 144 parameter combinations × 4 chronological windows = 576 rows; 48 cost/slippage/
  delay combinations; 5 rounding/partial variants. Total sensitivity rows: 629.
- The fixed 2% / 5% / 50% / 2% control is never chosen or replaced based on results.
- Metrics use daily closes, zero cash yield/risk-free rate, no leverage, no tax and
  no forced terminal liquidation. Partial liquidity caps are hypothetical, not a
  reconstruction of historical order-book fills. Floating-point accounting is checked
  within sub-cent tolerances; this is not a brokerage settlement engine.

## Limitations

Retrospective provider prices and inferred next-UTC-midnight publication times are not
an independently verified point-in-time archive. Corporate-action completeness is not
independently attested. The source adapter refuses action-bearing/adjustment-mismatched
packs until a nominal-price conversion and dividend payment-date ledger is supplied;
there are no reported AMD actions in this actual sample. The generic simulator supports
known nominal-price splits, not dividend reinvestment or broker cash-in-lieu rules.

Development (2021–2023) and subsequent chronological validation (2024–2026) are reported
separately, but this is not an unseen prospective validation period. Quarter/cycle
labels and independent restart dates are retrospective diagnostics, never tradable
foreknowledge. Continuous accounts inherit actual state; local episode drawdown peaks
are reporting windows, not artificial trading resets. No investment effectiveness,
parameter optimality or production readiness is established.

No Decision Engine, Tactical Risk Overlay, original simulator, production database,
Railway settings, live service, main branch or existing PR merge was changed.
