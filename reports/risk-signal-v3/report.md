# Risk Signal Engine v3 — research prototype

**Signals only. No position sizes, weights, trades, orders or production integration. V2 and Decision Engine remain unchanged.**

## Data and historical limits

AMD, NVDA, MU, QQQ and semiconductor index ^SOX: 2020 warm-up, evaluation 2021–22 October 2026. CBOE VIX is supplemental. Source responses, OHLCV, reported corporate actions, retrieval times, version and hashes: data/risk-signal-v3/manifest.json. 23 October is excluded. PR #2 supplies the publication-gated schema and PR #3 supplies causal diagnostic features; neither is modified.

This is retrospective split-adjusted provider OHLC, not an independently verified point-in-time publication archive. Dividend-adjusted closes are not mixed in. Ratios/drawdowns/MA slopes/RSI/log-return volatility are invariant to a constant future split scaling of an earlier prefix; this does not prove historical price-vintage accuracy. Publication is conservatively inferred as next UTC midnight; early closes are delayed. Missing/late required prices or QQQ observations suppress the risk level (DATA_UNAVAILABLE/STALE). Optional stale/missing VIX or SOX are excluded and explicitly labelled; they never become a mandatory risk gate. All outputs say RESEARCH_RULE_MATCH_ONLY.

## Fixed transparent variants and candidate catalogue

- **A, drawdown + trend:** WATCH at prior-20-close drawdown 5% (or fast five-session loss with price below MA20); REDUCE at 8% with price below falling MA20; CRITICAL at prior-60-close drawdown 20% below falling MA50. Balanced defaults shown.
- **B, grouped confirmation:** price-path stress (DD20 >=8% or five-session loss >=7%) plus at least three of four groups: price path, trend, relative weakness, volatility. Trend requires below falling MA20 plus below MA50 or RSI<45; relative weakness is <=-3 pp versus QQQ or SOX over 20 matched sessions; volatility is RV20/RV60 >=1.25, RV20 growth >=25% in five sessions, or VIX>=25. Four groups (or severe DD60 with three) yield CRITICAL. Groups are conceptually distinct, not statistically independent.
- **C, capped score:** price-path up to 3 points, trend up to 3, relative up to 2, volatility up to 2, prior-support break 1. WATCH/REDUCE/CRITICAL at 3/6/9 balanced points. Every predicate and raw/capped family contribution is retained. Correlated MA/RSI conditions cannot accumulate unlimited votes. VIX alone is insufficient; support is optional.
catalogue.json freezes sensitive/balanced/conservative alternatives. It is a small predeclared policy catalogue, not an October fit. MA20/50 slopes are five-session percentage changes and their change versus the preceding five-session slope. RSI is Wilder14 (the unchanged PR #3 simple RSI remains separately computed). Realized volatility uses sample SD of 20/60 daily log returns, annualized sqrt(252). Support excludes the current bar, and rolling maxima use exactly the prior 20/60 closes. No future returns or extrema enter any signal.

## Comparison

| Mode | Variant | Eligible drops | REDUCE before 10% / 15% / 20%, % | Median lead to 10%, sessions | False REDUCE after growth, % (n) | High-risk time % | Late after half the observed fall % |
|---|---|---|---|---|---|---|---|
| fixed_balanced | A | 85 | 17.6 / 50.0 / 81.8 | -2.0 | 52.5 (158) | 31.2 | 71.2 |
| fixed_balanced_test_period | A | 55 | 14.5 / 48.6 / 78.9 | -2.0 | 55.3 (103) | 25.3 | 78.3 |
| fixed_balanced | B | 85 | 12.9 / 46.3 / 72.7 | -2.0 | 48.6 (173) | 24.1 | 71.9 |
| fixed_balanced_test_period | B | 55 | 10.9 / 42.9 / 68.4 | -2.5 | 51.0 (102) | 18.9 | 81.6 |
| fixed_balanced | C | 85 | 34.1 / 83.3 / 93.9 | 0.0 | 42.9 (224) | 35.8 | 60.0 |
| fixed_balanced_test_period | C | 55 | 29.1 / 74.3 / 89.5 | 0.0 | 48.9 (135) | 29.8 | 68.0 |
| walk_forward | A | 55 | 14.5 / 48.6 / 78.9 | -2.0 | 54.2 (96) | 29.1 | 78.7 |
| walk_forward | B | 55 | 12.7 / 42.9 / 68.4 | -2.5 | 49.1 (106) | 20.9 | 81.6 |
| walk_forward | C | 55 | 61.8 / 82.9 / 94.7 | 1.0 | 54.8 (157) | 40.6 | 49.1 |

Coverage recall includes an already-active warning at the event peak; carried_high_risk_events and recall_before_10_new_entry_pct separately show inherited versus newly initiated warnings. first_reduce_entry_date records the actual high-risk entry, which can precede the peak. First REDUCE in event tables means first high-risk observation within the excursion, not necessarily a new signal. Lead is positive only if the warning preceded the threshold session; zero is same-session, negative is late. Median lead includes late detections and excludes completely missed events; recall includes misses. False REDUCE is a new high-risk entry followed by a higher close at +20 sessions with no >=10% additional closing decline in the horizon. It is a descriptive false-warning label, not proof that a risk decision was economically wrong. Complete horizons and censored entries are reported separately. Five/ten/twenty-session returns and adverse excursions are in entry-outcomes.csv and summary.csv.

## Walk-forward selection

Expanding training: 2021–2022 -> 2023, 2021–2023 -> 2024, 2021–2024 -> 2025, 2021–2025 -> 2026. A single configuration per variant is selected across all three stocks using earlier-period labels only, then frozen throughout the next test year. Training outcomes never extend past the training cutoff. Training objective = recall-before-10% - 0.5*false-growth rate - 0.25*high-risk time fraction - 0.01*switches per symbol-year. Ties prefer conservative, then balanced. No optimization of weights or October outcomes; all training candidates are exported.

| Test year | Variant | Frozen configuration | Training end | Recall before 10% % | False REDUCE % |
|---|---|---|---|---|---|
| 2023 | A | sensitive | 2022-12-31 | 0.0 | 65.0 |
| 2023 | B | sensitive | 2022-12-31 | 7.7 | 63.6 |
| 2023 | C | sensitive | 2022-12-31 | 84.6 | 59.1 |
| 2024 | A | sensitive | 2023-12-31 | 28.6 | 47.8 |
| 2024 | B | sensitive | 2023-12-31 | 14.3 | 38.1 |
| 2024 | C | sensitive | 2023-12-31 | 50.0 | 53.8 |
| 2025 | A | sensitive | 2024-12-31 | 0.0 | 50.0 |
| 2025 | B | sensitive | 2024-12-31 | 22.2 | 50.0 |
| 2025 | C | sensitive | 2024-12-31 | 77.8 | 41.4 |
| 2026 | A | sensitive | 2025-12-31 | 21.1 | 47.8 |
| 2026 | B | sensitive | 2025-12-31 | 10.5 | 41.7 |
| 2026 | C | sensitive | 2025-12-31 | 47.4 | 59.5 |

The expanding-window experiment prevents computational label leakage; it is not an untouched prospective study because the catalogue and retrospective source vintage were assembled after history was observable. Parameter changes occur only at fold boundaries; chronological risk states are carried into change explanations. First entries are not duplicated merely because a reporting year starts.

## September–October 2026 diagnostic (not a tuning sample)

| Symbol | Variant | First WATCH | First REDUCE or CRITICAL | VIX at first REDUCE | Support broken then |
|---|---|---|---|---|---|
| AMD | A | 2026-09-04 | 2026-09-01 | 16.3 | False |
| AMD | B | 2026-09-04 | 2026-09-01 | 16.3 | False |
| AMD | C | 2026-09-08 | 2026-09-01 | 16.3 | False |
| NVDA | A | 2026-09-01 | 2026-09-14 | 17.1 | False |
| NVDA | B | 2026-09-01 | 2026-09-14 | 17.1 | False |
| NVDA | C | 2026-09-01 | 2026-09-14 | 17.1 | False |
| MU | A | 2026-09-02 | 2026-09-01 | 16.3 | False |
| MU | B | 2026-09-01 | 2026-10-16 | 20.0 | False |
| MU | C | 2026-09-01 | 2026-09-14 | 17.1 | False |

This table uses walk-forward frozen configurations. The first high-risk date in a window can be a carried state from before the window; it is not automatically a new entry. Event-specific leads below are measured from each event peak, and left-censored peaks are excluded from recall denominators.


### October peak-linked events (walk-forward)

| Symbol | Peak | Variant | First high-risk observation / actual entry | Carried at peak | Lead before 10% / 15% / 20%, sessions |
|---|---|---|---|---|---|
| AMD | 2026-10-06 | A | 2026-10-20 / 2026-10-20 | False | -4 / -2 / 2 |
| NVDA | 2026-10-06 | A | 2026-10-20 / 2026-10-20 | False | -2 / — / — |
| MU | 2026-10-01 | A | 2026-10-16 / 2026-10-16 | False | -3 / -2 / 4 |
| AMD | 2026-10-06 | B | 2026-10-20 / 2026-10-20 | False | -4 / -2 / 2 |
| NVDA | 2026-10-06 | B | — / — | False | — / — / — |
| MU | 2026-10-01 | B | 2026-10-16 / 2026-10-16 | False | -3 / -2 / 4 |
| AMD | 2026-10-06 | C | 2026-10-12 / 2026-10-12 | False | 2 / 4 / 8 |
| NVDA | 2026-10-06 | C | 2026-10-14 / 2026-10-14 | False | 2 / — / — |
| MU | 2026-10-01 | C | 2026-10-09 / 2026-10-09 | False | 2 / 3 / 9 |
## AMD: complete fixed-balanced event table

| Peak | First 10% / 15% / 20% date | A first REDUCE (lead10) | B first REDUCE (lead10) | C first REDUCE (lead10) |
|---|---|---|---|---|
| 2021-01-11 | 2021-01-28 / 2021-02-25 / 2021-03-04 | 2021-01-15 (8) | 2021-01-15 (8) | 2021-01-15 (8) |
| 2021-04-26 | 2021-05-10 / — / — | 2021-05-05 (3) | 2021-05-05 (3) | 2021-05-03 (5) |
| 2021-08-04 | 2021-08-10 / 2021-09-29 / — | 2021-09-20 (-28) | 2021-09-20 (-28) | 2021-08-20 (-8) |
| 2021-11-29 | 2021-12-03 / 2021-12-13 / 2022-01-19 | 2021-12-09 (-4) | 2021-12-13 (-6) | 2021-12-03 (0) |
| 2022-03-29 | 2022-03-31 / 2022-04-06 / 2022-04-11 | 2022-03-31 (0) | 2022-04-06 (-4) | 2022-03-31 (0) |
| 2022-05-17 | 2022-05-24 / — / — | 2022-05-18 (4) | — (—) | 2022-05-24 (0) |
| 2022-06-02 | 2022-06-10 / 2022-06-13 / 2022-06-16 | 2022-06-10 (0) | 2022-06-15 (-3) | 2022-06-10 (0) |
| 2022-08-04 | 2022-08-22 / 2022-08-30 / 2022-09-01 | 2022-08-30 (-6) | 2022-08-29 (-5) | 2022-08-22 (0) |
| 2022-11-30 | 2022-12-09 / 2022-12-16 / — | 2022-12-14 (-3) | 2022-12-12 (-1) | 2022-12-06 (3) |
| 2023-02-02 | 2023-02-17 / — / — | — (—) | — (—) | 2023-02-17 (0) |
| 2023-03-23 | 2023-04-17 / 2023-04-25 / — | 2023-04-18 (-1) | 2023-04-18 (-1) | 2023-04-14 (1) |
| 2023-06-12 | 2023-06-21 / 2023-06-26 / 2023-08-24 | 2023-06-27 (-4) | 2023-06-21 (0) | 2023-06-21 (0) |
| 2023-10-10 | 2023-10-25 / — / — | 2023-10-27 (-2) | 2023-10-30 (-3) | 2023-10-23 (2) |
| 2024-03-07 | 2024-03-14 / 2024-03-21 / 2024-04-04 | 2024-03-28 (-10) | 2024-03-28 (-10) | 2024-03-20 (-4) |
| 2024-07-10 | 2024-07-17 / 2024-07-18 / 2024-07-24 | 2024-07-23 (-4) | 2024-07-19 (-2) | 2024-07-17 (0) |
| 2024-08-21 | 2024-09-03 / — / — | 2024-08-28 (3) | — (—) | 2024-09-03 (0) |
| 2024-10-08 | 2024-10-22 / 2024-10-31 / 2024-11-15 | 2024-10-23 (-1) | 2024-10-23 (-1) | 2024-10-15 (5) |
| 2025-03-25 | 2025-03-28 / 2025-04-03 / 2025-04-04 | 2025-03-28 (0) | 2025-04-04 (-5) | 2025-03-28 (0) |
| 2025-08-13 | 2025-08-20 / 2025-09-05 / — | 2025-08-26 (-4) | 2025-09-05 (-11) | 2025-08-25 (-3) |
| 2025-10-29 | 2025-11-06 / 2025-11-19 / 2025-11-20 | 2025-11-20 (-10) | 2025-11-20 (-10) | 2025-11-19 (-9) |
| 2026-01-23 | 2026-02-04 / 2026-02-04 / 2026-02-04 | 2026-02-10 (-4) | 2026-02-04 (0) | 2026-02-04 (0) |
| 2026-03-25 | 2026-03-30 / — / — | 2026-03-26 (2) | — (—) | 2026-03-30 (0) |
| 2026-06-03 | 2026-06-05 / 2026-06-10 / — | — (—) | — (—) | 2026-06-10 (-3) |
| 2026-06-30 | 2026-07-02 / 2026-07-28 / 2026-07-28 | 2026-07-20 (-11) | 2026-07-28 (-17) | 2026-07-17 (-10) |
| 2026-10-06 | 2026-10-14 / 2026-10-16 / 2026-10-22 | 2026-10-20 (-4) | 2026-10-20 (-4) | 2026-10-15 (-1) |
## NVDA: complete fixed-balanced event table

| Peak | First 10% / 15% / 20% date | A first REDUCE (lead10) | B first REDUCE (lead10) | C first REDUCE (lead10) |
|---|---|---|---|---|
| 2021-02-16 | 2021-02-25 / 2021-03-03 / 2021-03-08 | 2021-03-04 (-5) | 2021-03-01 (-2) | 2021-02-25 (0) |
| 2021-04-15 | 2021-05-04 / 2021-05-13 / — | 2021-05-11 (-5) | 2021-05-12 (-6) | 2021-05-11 (-5) |
| 2021-07-06 | 2021-07-16 / — / — | — (—) | — (—) | 2021-07-16 (0) |
| 2021-09-03 | 2021-09-29 / — / — | 2021-09-28 (1) | 2021-09-28 (1) | 2021-09-28 (1) |
| 2021-11-29 | 2021-12-06 / 2021-12-13 / 2022-01-13 | 2021-12-14 (-6) | 2021-12-14 (-6) | 2021-12-06 (0) |
| 2022-03-29 | 2022-04-06 / 2022-04-07 / 2022-04-11 | 2022-04-13 (-5) | 2022-04-13 (-5) | 2022-04-06 (0) |
| 2022-08-04 | 2022-08-09 / 2022-08-26 / 2022-08-31 | 2022-08-26 (-13) | 2022-08-26 (-13) | 2022-08-09 (0) |
| 2022-12-13 | 2022-12-19 / 2022-12-22 / 2022-12-27 | 2022-12-23 (-4) | 2022-12-27 (-5) | 2022-12-16 (1) |
| 2023-02-14 | 2023-02-21 / — / — | — (—) | — (—) | — (—) |
| 2023-07-18 | 2023-08-09 / — / — | 2023-08-11 (-2) | 2023-08-11 (-2) | 2023-08-10 (-1) |
| 2023-08-31 | 2023-09-15 / 2023-09-21 / — | 2023-09-20 (-3) | 2023-09-20 (-3) | 2023-09-12 (3) |
| 2023-10-12 | 2023-10-18 / — / — | 2023-10-26 (-6) | 2023-10-27 (-7) | 2023-10-18 (0) |
| 2024-03-25 | 2024-04-09 / 2024-04-19 / — | 2024-04-08 (1) | 2024-04-17 (-6) | 2024-04-10 (-1) |
| 2024-06-18 | 2024-06-24 / 2024-07-24 / 2024-07-30 | 2024-07-17 (-16) | 2024-07-17 (-16) | 2024-07-16 (-15) |
| 2024-08-19 | 2024-09-03 / 2024-09-03 / 2024-09-06 | 2024-09-03 (0) | 2024-09-16 (-9) | 2024-09-03 (0) |
| 2024-11-07 | 2024-12-16 / — / — | 2024-11-27 (12) | 2024-11-27 (12) | 2024-11-25 (14) |
| 2025-01-06 | 2025-01-13 / 2025-01-27 / 2025-01-27 | 2025-01-13 (0) | 2025-01-13 (0) | 2025-01-13 (0) |
| 2025-10-29 | 2025-11-18 / 2025-12-12 / — | 2025-11-24 (-4) | 2025-11-06 (8) | 2025-11-06 (8) |
| 2026-01-29 | 2026-02-05 / — / — | 2026-02-04 (1) | 2026-02-04 (1) | 2026-02-03 (2) |
| 2026-02-25 | 2026-03-20 / 2026-03-30 / — | 2026-02-27 (15) | 2026-02-27 (15) | 2026-02-27 (15) |
| 2026-05-14 | 2026-05-29 / 2026-06-23 / — | 2026-06-10 (-8) | 2026-06-05 (-5) | 2026-05-22 (4) |
| 2026-07-15 | 2026-07-29 / — / — | — (—) | — (—) | 2026-07-29 (0) |
| 2026-10-06 | 2026-10-16 / — / — | 2026-10-20 (-2) | — (—) | 2026-10-15 (1) |
## MU: complete fixed-balanced event table

| Peak | First 10% / 15% / 20% date | A first REDUCE (lead10) | B first REDUCE (lead10) | C first REDUCE (lead10) |
|---|---|---|---|---|
| 2021-01-19 | 2021-01-27 / — / — | — (—) | — (—) | 2021-01-27 (0) |
| 2021-03-01 | 2021-03-04 / — / — | — (—) | — (—) | 2021-03-04 (0) |
| 2021-03-17 | 2021-03-24 / — / — | 2021-03-24 (0) | 2021-03-24 (0) | 2021-03-23 (1) |
| 2021-04-12 | 2021-04-22 / 2021-05-10 / — | 2021-04-20 (2) | 2021-04-19 (3) | 2021-04-15 (5) |
| 2021-06-30 | 2021-07-16 / — / — | 2021-07-08 (6) | 2021-07-08 (6) | 2021-07-01 (10) |
| 2021-08-06 | 2021-08-12 / — / — | 2021-08-12 (0) | 2021-08-12 (0) | 2021-08-10 (2) |
| 2021-09-27 | 2021-10-12 / — / — | 2021-10-12 (0) | 2021-10-12 (0) | 2021-10-12 (0) |
| 2022-01-14 | 2022-01-20 / 2022-01-21 / — | 2022-01-24 (-2) | 2022-01-24 (-2) | 2022-01-20 (0) |
| 2022-02-16 | 2022-03-01 / 2022-03-07 / 2022-03-07 | 2022-03-07 (-4) | 2022-03-09 (-6) | 2022-03-01 (0) |
| 2022-05-17 | 2022-05-24 / — / — | 2022-05-18 (4) | 2022-05-24 (0) | 2022-05-20 (2) |
| 2022-06-02 | 2022-06-09 / 2022-06-10 / 2022-06-13 | 2022-06-10 (-1) | 2022-06-09 (0) | 2022-06-07 (2) |
| 2022-08-12 | 2022-08-22 / 2022-09-06 / 2022-09-20 | 2022-08-22 (0) | 2022-08-22 (0) | 2022-08-17 (3) |
| 2022-11-15 | 2022-11-28 / 2022-12-15 / 2022-12-22 | 2022-12-07 (-7) | 2022-12-07 (-7) | 2022-11-21 (4) |
| 2023-01-27 | 2023-02-22 / 2023-03-13 / — | 2023-02-23 (-1) | 2023-03-01 (-5) | 2023-02-09 (8) |
| 2023-03-29 | 2023-04-05 / — / — | — (—) | 2023-04-04 (1) | 2023-04-04 (1) |
| 2023-05-26 | 2023-06-08 / 2023-07-05 / — | 2023-06-23 (-10) | 2023-06-30 (-15) | 2023-06-08 (0) |
| 2023-07-31 | 2023-08-16 / — / — | 2023-08-18 (-2) | 2023-08-18 (-2) | 2023-08-11 (3) |
| 2023-09-14 | 2023-10-26 / — / — | 2023-10-26 (0) | — (—) | — (—) |
| 2024-01-22 | 2024-02-16 / — / — | 2024-02-15 (1) | 2024-02-15 (1) | 2024-02-13 (3) |
| 2024-04-03 | 2024-04-18 / 2024-04-19 / — | 2024-04-24 (-4) | — (—) | 2024-04-18 (0) |
| 2024-06-18 | 2024-06-27 / 2024-07-11 / 2024-07-17 | 2024-07-11 (-9) | 2024-07-15 (-11) | 2024-06-27 (0) |
| 2024-10-17 | 2024-10-31 / — / — | — (—) | — (—) | 2024-11-01 (-1) |
| 2024-11-07 | 2024-11-13 / 2024-11-15 / — | 2024-11-14 (-1) | 2024-11-14 (-1) | 2024-11-13 (0) |
| 2024-12-17 | 2024-12-19 / 2024-12-19 / 2024-12-30 | 2024-12-19 (0) | 2024-12-19 (0) | 2024-12-19 (0) |
| 2025-01-21 | 2025-01-27 / 2025-01-27 / 2025-03-10 | 2025-01-28 (-1) | 2025-02-06 (-8) | 2025-01-27 (0) |
| 2025-06-24 | 2025-07-17 / 2025-08-01 / — | 2025-07-18 (-1) | 2025-07-21 (-2) | 2025-07-16 (1) |
| 2025-11-10 | 2025-11-19 / 2025-11-20 / 2025-11-20 | 2025-11-26 (-5) | — (—) | 2025-11-20 (-1) |
| 2025-12-10 | 2025-12-16 / — / — | 2025-12-17 (-1) | — (—) | 2025-12-16 (0) |
| 2026-02-02 | 2026-02-04 / 2026-03-06 / — | 2026-03-03 (-18) | 2026-03-03 (-18) | 2026-03-03 (-18) |
| 2026-03-18 | 2026-03-23 / 2026-03-25 / 2026-03-26 | 2026-03-25 (-2) | 2026-03-25 (-2) | 2026-03-24 (-1) |
| 2026-05-13 | 2026-05-18 / 2026-05-18 / — | — (—) | — (—) | — (—) |
| 2026-06-03 | 2026-06-05 / 2026-06-05 / — | — (—) | — (—) | — (—) |
| 2026-06-22 | 2026-06-23 / — / — | — (—) | — (—) | — (—) |
| 2026-06-25 | 2026-07-01 / 2026-07-02 / 2026-07-07 | 2026-07-08 (-4) | 2026-07-02 (-1) | 2026-07-01 (0) |
| 2026-08-17 | 2026-08-24 / — / — | 2026-08-18 (4) | — (—) | 2026-08-24 (0) |
| 2026-09-09 | 2026-09-14 / — / — | 2026-09-14 (0) | — (—) | 2026-09-14 (0) |
| 2026-10-01 | 2026-10-13 / 2026-10-14 / 2026-10-22 | 2026-10-16 (-3) | 2026-10-16 (-3) | 2026-10-12 (1) |

## Main finding

The walk-forward C model detects REDUCE before 10% in 61.8% of eligible excursions, with median lead 1.0 sessions among detected events. Its false-growth warning rate is 54.8% and high-risk duty cycle 40.6%. This supports feasibility of VIX-independent detection, but does not establish sufficiently reliable warnings: false alerts and late detections remain substantial. October C warnings precede 10% by two sessions for each studied stock; this diagnostic alone cannot validate the model.


## Regimes, recommendation and interpretation

All calendar quarters are retained in regime-metrics.csv: strong uptrend >=20% close return, deep decline <=-20%, sideways |return|<=10% with >=15% closing range, otherwise mixed. These are retrospective descriptions, never input regime labels. The full event set includes deep 2022/2024–2025 corrections and fast drawdown/recovery episodes; no favorable episodes are selected.

Training-only candidate for further testing: **variant C / sensitive**, selected from 2021–2025 training metrics, not from 2026 or full-history rankings. This is a provisional research choice under the explicit objective, not a validated live recommendation. Inspect false warnings, late detections, duty cycle and switching alongside recall before retaining it.

A price-local risk signal can fire with low VIX and intact long-term support by construction; the diagnostic tests whether it actually did so and how often it warned too late or during later growth. Not every decline is predictable. Correlated repeated events/horizons, low sample sizes and retrospective revisions prevent strong reliability claims. No position-size or profitability inference is made.

## Definitions and reproduction

- Run `python scripts/fetch_risk_v3_data.py` only to refresh documented source responses; `python -m aae.research.risk_v3_study` reproduces the offline study. The source pack is frozen through 22 October; 2020 observations warm up all indicators.
- Significant-event rule: excursion since a known trailing-20 closing high, ending on the next trailing-20 high (which need not recover an older all-time peak). Every event reaching 10% is retained; 15/20% labels are added when observed. Nested old peak drawdowns are not treated as independent predictions. Left-censored peaks and still-open episodes are explicit. Trough/fraction-of-fall and future-return fields are labels only, in separate evaluation files.
- first_watch means actual WATCH; a direct jump to REDUCE does not invent an earlier WATCH. first_warning_at_least_watch records either. REDUCE detection includes CRITICAL. Over-half-fall timing uses the observed eventual trough; reduce_after_trough is separately counted. These are retrospective quality diagnostics, never decision inputs.
- Aggregate fixed-balanced results use 2021–2026; walk-forward results use only generated test signals in 2023–2026. Their different periods must not be compared as like-for-like performance. Rows fixed_balanced_test_period provide the same 2023–2026 dates as walk-forward; annual CSVs give further detail. Invalid mandatory data produce no risk level, not HOLD. Optional source gaps are disclosed. Switches count valid risk-level transitions; yearly tables show raw observed counts, with 2026 incomplete and no extrapolation.
- Daily CSV is compact; daily-signals.jsonl.gz retains full ticker/time/state, all indicator values, every condition, capped contributions, change reasons and source-quality metadata. It contains no sizing or execution fields. New REDUCE episode outcomes are isolated in entry-outcomes.csv; each 5/10/20 horizon is independently censored at its evaluation endpoint.
- Source/code/output hashes, frozen catalogue, fold-selection and training-candidates record reproducibility. Existing production modules and services are untouched; test results/limits are in validation.md.
