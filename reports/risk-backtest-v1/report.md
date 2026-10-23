# Alpha OS historical research v1

**No full Alpha OS v1 versus v2 performance comparison is available without archived point-in-time decision inputs.**

The price-only overlay below is NOT the full Risk Engine v2 Decision Engine. Public prices are retrospective provider vintages; publication times are assumed. These results do not establish strict point-in-time strategy effectiveness.

Requested window: 2026-09-01T00:00:00+00:00 through 2026-10-24T00:00:00+00:00. Actual per-symbol coverage appears below. No missing sessions or future bars are invented.

| Symbol | First obtained bar | Last completed obtained bar | Rows |
|---|---|---|---|
| AMD | 2023-01-03T21:00:00+00:00 | 2026-10-22T20:00:00+00:00 | 955 |
| NVDA | 2023-01-03T21:00:00+00:00 | 2026-10-22T20:00:00+00:00 | 955 |
| MU | 2023-01-03T21:00:00+00:00 | 2026-10-22T20:00:00+00:00 | 955 |
| TSM | 2023-01-03T21:00:00+00:00 | 2026-10-22T20:00:00+00:00 | 955 |
| AVGO | 2023-01-03T21:00:00+00:00 | 2026-10-22T20:00:00+00:00 | 955 |
| AMAT | 2023-01-03T21:00:00+00:00 | 2026-10-22T20:00:00+00:00 | 955 |
| AMZN | 2023-01-03T21:00:00+00:00 | 2026-10-22T20:00:00+00:00 | 955 |
| META | 2023-01-03T21:00:00+00:00 | 2026-10-22T20:00:00+00:00 | 955 |
| PLTR | 2023-01-03T21:00:00+00:00 | 2026-10-22T20:00:00+00:00 | 955 |
| LRCX | 2023-01-03T21:00:00+00:00 | 2026-10-22T20:00:00+00:00 | 955 |
| NBIS | 2024-10-21T20:00:00+00:00 | 2026-10-22T20:00:00+00:00 | 503 |

## Limited price replay

| Window | Symbol | Strategy | Return % | Max drawdown % | False/censored sells | Missed recovery $ |
|---|---|---|---|---|---|---|
| requested | AMD | buy_hold | 10.33 | -21.79 | 0/0 | 0.00 |
| requested | AMD | risk_overlay_only | 10.33 | -21.79 | 0/0 | 0.00 |
| extended_2024_2026 | AMD | buy_hold | 251.69 | -63.00 | 0/0 | 0.00 |
| extended_2024_2026 | AMD | risk_overlay_only | 236.72 | -61.83 | 3/0 | 1497.37 |
| requested | NVDA | buy_hold | -2.19 | -11.30 | 0/0 | 0.00 |
| requested | NVDA | risk_overlay_only | -2.19 | -11.30 | 0/0 | 0.00 |
| extended_2024_2026 | NVDA | buy_hold | 330.51 | -36.89 | 0/0 | 0.00 |
| extended_2024_2026 | NVDA | risk_overlay_only | 303.55 | -36.13 | 3/0 | 2658.67 |
| requested | MU | buy_hold | -9.08 | -21.95 | 0/0 | 0.00 |
| requested | MU | risk_overlay_only | -9.08 | -21.95 | 0/0 | 0.00 |
| extended_2024_2026 | MU | buy_hold | 918.61 | -57.82 | 0/0 | 0.00 |
| extended_2024_2026 | MU | risk_overlay_only | 862.22 | -57.72 | 2/0 | 5631.35 |
| requested | TSM | buy_hold | -1.40 | -15.12 | 0/0 | 0.00 |
| requested | TSM | risk_overlay_only | -1.40 | -15.12 | 0/0 | 0.00 |
| extended_2024_2026 | TSM | buy_hold | 302.87 | -37.06 | 0/0 | 0.00 |
| extended_2024_2026 | TSM | risk_overlay_only | 272.66 | -36.02 | 3/0 | 2991.48 |
| requested | AVGO | buy_hold | -11.35 | -14.15 | 0/0 | 0.00 |
| requested | AVGO | risk_overlay_only | -11.35 | -14.15 | 0/0 | 0.00 |
| extended_2024_2026 | AVGO | buy_hold | 195.68 | -41.48 | 0/0 | 0.00 |
| extended_2024_2026 | AVGO | risk_overlay_only | 165.30 | -41.31 | 3/0 | 3012.57 |
| requested | AMAT | buy_hold | -16.75 | -30.74 | 0/0 | 0.00 |
| requested | AMAT | risk_overlay_only | -16.75 | -30.74 | 0/0 | 0.00 |
| extended_2024_2026 | AMAT | buy_hold | 134.50 | -50.21 | 0/0 | 0.00 |
| extended_2024_2026 | AMAT | risk_overlay_only | 120.68 | -50.87 | 3/0 | 1395.06 |
| requested | AMZN | buy_hold | -1.84 | -5.00 | 0/0 | 0.00 |
| requested | AMZN | risk_overlay_only | -1.84 | -5.00 | 0/0 | 0.00 |
| extended_2024_2026 | AMZN | buy_hold | 65.06 | -30.88 | 0/0 | 0.00 |
| extended_2024_2026 | AMZN | risk_overlay_only | 56.32 | -30.91 | 3/0 | 856.79 |
| requested | META | buy_hold | 16.09 | -16.56 | 0/0 | 0.00 |
| requested | META | risk_overlay_only | 16.09 | -16.56 | 0/0 | 0.00 |
| extended_2024_2026 | META | buy_hold | 84.50 | -34.21 | 0/0 | 0.00 |
| extended_2024_2026 | META | risk_overlay_only | 72.20 | -33.48 | 3/0 | 1209.53 |
| requested | PLTR | buy_hold | 7.11 | -11.01 | 0/0 | 0.00 |
| requested | PLTR | risk_overlay_only | 7.11 | -11.01 | 0/0 | 0.00 |
| extended_2024_2026 | PLTR | buy_hold | 1056.31 | -48.22 | 0/0 | 0.00 |
| extended_2024_2026 | PLTR | risk_overlay_only | 930.13 | -48.57 | 3/0 | 12548.56 |
| requested | LRCX | buy_hold | -21.94 | -33.77 | 0/0 | 0.00 |
| requested | LRCX | risk_overlay_only | -21.94 | -33.77 | 0/0 | 0.00 |
| extended_2024_2026 | LRCX | buy_hold | 199.08 | -47.58 | 0/0 | 0.00 |
| extended_2024_2026 | LRCX | risk_overlay_only | 182.14 | -47.52 | 3/0 | 1676.98 |
| requested | NBIS | buy_hold | -20.46 | -36.30 | 0/0 | 0.00 |
| requested | NBIS | risk_overlay_only | -20.46 | -36.30 | 0/0 | 0.00 |
| extended_2024_2026 | NBIS | buy_hold | 1012.74 | -58.27 | 0/0 | 0.00 |
| extended_2024_2026 | NBIS | risk_overlay_only | 946.20 | -58.27 | 2/0 | 6612.78 |

Observed short-window overlay action counts: {'HOLD': 403, 'REVIEW': 4}.
No claim about a full Alpha OS strategy follows from these limited results.

## Sensitivity ranges (all variants retained)

| Symbol | Variants | Return range % | Drawdown range % |
|---|---|---|---|
| AMD | 27 | 10.33 to 10.33 | -21.79 to -21.79 |
| NVDA | 27 | -2.19 to -2.19 | -11.30 to -11.30 |
| MU | 27 | -9.08 to -9.08 | -21.95 to -21.95 |
| TSM | 27 | -1.40 to -1.40 | -15.12 to -15.12 |
| AVGO | 27 | -11.35 to -11.35 | -14.15 to -14.15 |
| AMAT | 27 | -16.75 to -16.75 | -30.74 to -30.74 |
| AMZN | 27 | -1.84 to -1.84 | -5.00 to -5.00 |
| META | 27 | 16.09 to 16.09 | -16.56 to -16.56 |
| PLTR | 27 | 7.11 to 7.11 | -11.01 to -11.01 |
| LRCX | 27 | -21.94 to -21.94 | -33.77 to -33.77 |
| NBIS | 27 | -20.46 to -20.46 | -36.30 to -36.30 |

## Unavailable comparisons

For each symbol/window summary.csv records missing full alpha_v1 and risk_v2 results as UNAVAILABLE with empty metrics, never zero-filled. Strict mode also refuses retrospective price vintages.

## Assumptions and interpretation

- Each symbol: independent $10,000 long-only account; first eligible open entry, no leverage or shorting.
- 5 bps commission and 5 bps adverse slippage per side; zero cash interest, taxes and liquidity impact. No forced terminal liquidation.
- Signals after bar publication; one later eligible session open delay. No same-close fills. Terminal pending orders remain unfilled.
- Default TRIM once per risk episode; additional TRIM signals are logged but suppressed. Compound mode is explicit and has a 25% exposure floor.
- Restore to full exposure after three consecutive actionable HOLD sessions, at a later open. REVIEW interrupts the sequence; unverified data cancel queued orders.
- False signal: executed sell followed by a higher close five sessions after its execution. Insufficient follow-up is censored, not counted as correct.
- Missed recovery: positive price appreciation on sold FIFO units through their repurchase or terminal mark; dollars, gross of costs. Not a causal attribution or total strategy underperformance.
- Maximum drawdown includes initial capital and close marks; intraday drawdown is not measured. No dividends or corporate-action cash flows: returns are provider-price replay only, not total returns.
- Predeclared sensitivity grid: VIX stress 20/25/30 (severe=stress+5), prior support 60/120/200 bars, trim 10/25/50%. All variants retained; no best setting selected. Extended window is a robustness exploration, not an untouched validation set.
The requested full period is incomplete: obtained bars end before 2026-10-23.

See docs/risk-backtest-v1.md and data/backtest/manifest.json for provenance, strict input contract, missing inputs and reproduction.
