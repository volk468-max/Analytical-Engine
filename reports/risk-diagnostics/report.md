# Risk signal diagnostics: AMD, NVDA, MU

## Scope and causal limits

Daily decisions: 1 September–22 October 2026. Extended recovery study: 2024–22 October 2026. All calculations gate observations by publication time; no future candles enter features or Overlay decisions. The underlying provider-price vintages and inferred availability are still NOT verified point-in-time data. This is the limited price/VIX overlay replay from PR #2, not a reconstructed full Alpha OS decision system.

Risk Engine v2, thresholds and execution/restoration policy are unchanged. Diagnostics call the existing Overlay. Market regime and broad-market breadth are UNAVAILABLE: neither trustworthy constituent histories nor archived regime inputs exist. QQQ is a relative-price benchmark, not fabricated breadth or a reconstructed regime.

## Why TRIM did not occur

When input validity and freshness checks pass under the replay assumptions, the unchanged formula is `VIX >= 30 OR (price < prior_120_bar_low * 0.99 AND (VIX >= 25 OR fresh_defensive_regime))`. A falling stock, a 10–20% decline from a recent peak, MA breakdown, weak RSI or relative weakness is not by itself a TRIM input. An unavailable defensive regime is not a bullish observation; the replay simply cannot exercise that branch. For these observed rows support was not broken, so a defensive regime alone could add REVIEW but could not activate the conjunctive TRIM branch. Full Alpha OS decisions could still differ through other Decision Engine inputs that are unavailable historically.

| Symbol | Sessions | HOLD / REVIEW / TRIM | Max VIX | Min (close/support - 1) % | Worst DD20 / DD60 / DD120 % |
|---|---|---|---|---|---|
| AMD | 37 | 37 / 0 / 0 | 19.99 | 49.96 | -21.79 / -21.79 / -21.79 |
| NVDA | 37 | 37 / 0 / 0 | 19.99 | 11.81 | -11.30 / -11.30 / -11.30 |
| MU | 37 | 37 / 0 / 0 | 19.99 | 67.87 | -21.95 / -23.86 / -29.42 |

## AMD

Prior-support breaks beyond 1%: 0; VIX stress days (>=25): 0; severe days (>=30): 0. Below MA20/MA50: 12/9 sessions.

| Peak date | Threshold | First crossing | Technical deterioration | First REVIEW | TRIM | Trough / loss % | Crossing blockers |
|---|---|---|---|---|---|---|---|
| 2026-06-30 | 10% | 2026-07-02 | 2026-07-07 | none | none | 2026-07-29 / -26.05 | severe_VIX_branch_not_met; support_break_branch_not_met; stress_confirmation_not_met; defensive_regime_unavailable_not_assumed |
| 2026-06-30 | 15% | 2026-07-28 | 2026-07-07 | none | none | 2026-07-29 / -26.05 | severe_VIX_branch_not_met; support_break_branch_not_met; stress_confirmation_not_met; defensive_regime_unavailable_not_assumed |
| 2026-06-30 | 20% | 2026-07-28 | 2026-07-07 | none | none | 2026-07-29 / -26.05 | severe_VIX_branch_not_met; support_break_branch_not_met; stress_confirmation_not_met; defensive_regime_unavailable_not_assumed |
| 2026-08-04 | 10% | 2026-08-19 | 2026-08-05 | none | none | 2026-09-03 / -12.04 | severe_VIX_branch_not_met; support_break_branch_not_met; stress_confirmation_not_met; defensive_regime_unavailable_not_assumed |
| 2026-10-06 | 10% | 2026-10-14 | 2026-10-12 | none | none | 2026-10-22 / -21.79 | severe_VIX_branch_not_met; support_break_branch_not_met; stress_confirmation_not_met; defensive_regime_unavailable_not_assumed |
| 2026-10-06 | 15% | 2026-10-16 | 2026-10-12 | none | none | 2026-10-22 / -21.79 | severe_VIX_branch_not_met; support_break_branch_not_met; stress_confirmation_not_met; defensive_regime_unavailable_not_assumed |
| 2026-10-06 | 20% | 2026-10-22 | 2026-10-12 | none | none | 2026-10-22 / -21.79 | severe_VIX_branch_not_met; support_break_branch_not_met; stress_confirmation_not_met; defensive_regime_unavailable_not_assumed |

Extended period: 3 executed reduction episodes; FIFO missed recovery including residual units marked at period end $1497.37 per $10,000 initial account (gross diagnostic, not total strategy underperformance).

| Sale | Restore | Sessions reduced | Sale / restore price | Rebound from post-sale low before restoration % | Missed rise vs sale $ |
|---|---|---|---|---|---|
| 2024-08-06 | 2024-08-13 | 5 | 135.15 / 138.12 | 7.34 | 51.41 |
| 2025-04-04 | 2025-05-02 | 19 | 90.10 / 98.40 | 25.82 | 142.83 |
| 2026-03-30 | 2026-04-07 | 5 | 204.95 / 218.26 | 11.33 | 224.11 |

Extended limited price replay return: Overlay 236.72%, Buy & Hold 251.69%; difference -14.97 percentage points, including modeled costs. This is separate from the gross FIFO diagnostic.

## NVDA

Prior-support breaks beyond 1%: 0; VIX stress days (>=25): 0; severe days (>=30): 0. Below MA20/MA50: 14/9 sessions.

| Peak date | Threshold | First crossing | Technical deterioration | First REVIEW | TRIM | Trough / loss % | Crossing blockers |
|---|---|---|---|---|---|---|---|
| 2026-05-14 | 10% | 2026-05-29 | 2026-05-27 | none | none | 2026-07-29 / -19.40 | severe_VIX_branch_not_met; support_break_branch_not_met; stress_confirmation_not_met; defensive_regime_unavailable_not_assumed |
| 2026-05-14 | 15% | 2026-06-23 | 2026-05-27 | none | none | 2026-07-29 / -19.40 | severe_VIX_branch_not_met; support_break_branch_not_met; stress_confirmation_not_met; defensive_regime_unavailable_not_assumed |
| 2026-10-06 | 10% | 2026-10-16 | 2026-10-12 | none | none | 2026-10-22 / -11.30 | severe_VIX_branch_not_met; support_break_branch_not_met; stress_confirmation_not_met; defensive_regime_unavailable_not_assumed |

Extended period: 3 executed reduction episodes; FIFO missed recovery including residual units marked at period end $2658.67 per $10,000 initial account (gross diagnostic, not total strategy underperformance).

| Sale | Restore | Sessions reduced | Sale / restore price | Rebound from post-sale low before restoration % | Missed rise vs sale $ |
|---|---|---|---|---|---|
| 2024-08-06 | 2024-08-13 | 5 | 103.84 / 112.44 | 13.68 | 436.17 |
| 2025-04-04 | 2025-05-02 | 19 | 98.91 / 114.18 | 21.07 | 759.28 |
| 2026-03-30 | 2026-04-07 | 5 | 168.78 / 175.73 | 6.39 | 333.88 |

Extended limited price replay return: Overlay 303.55%, Buy & Hold 330.51%; difference -26.95 percentage points, including modeled costs. This is separate from the gross FIFO diagnostic.

## MU

Prior-support breaks beyond 1%: 0; VIX stress days (>=25): 0; severe days (>=30): 0. Below MA20/MA50: 13/10 sessions.

| Peak date | Threshold | First crossing | Technical deterioration | First REVIEW | TRIM | Trough / loss % | Crossing blockers |
|---|---|---|---|---|---|---|---|
| 2026-06-25 | 10% | 2026-07-01 | 2026-07-01 | none | none | 2026-07-29 / -39.10 | severe_VIX_branch_not_met; support_break_branch_not_met; stress_confirmation_not_met; defensive_regime_unavailable_not_assumed |
| 2026-06-25 | 15% | 2026-07-02 | 2026-07-01 | none | none | 2026-07-29 / -39.10 | severe_VIX_branch_not_met; support_break_branch_not_met; stress_confirmation_not_met; defensive_regime_unavailable_not_assumed |
| 2026-06-25 | 20% | 2026-07-07 | 2026-07-01 | none | none | 2026-07-29 / -39.10 | severe_VIX_branch_not_met; support_break_branch_not_met; stress_confirmation_not_met; defensive_regime_unavailable_not_assumed |
| 2026-08-17 | 10% | 2026-08-24 | 2026-08-18 | none | none | 2026-08-24 / -10.01 | severe_VIX_branch_not_met; support_break_branch_not_met; stress_confirmation_not_met; defensive_regime_unavailable_not_assumed |
| 2026-09-09 | 10% | 2026-09-14 | 2026-09-14 | none | none | 2026-09-14 / -10.09 | severe_VIX_branch_not_met; support_break_branch_not_met; stress_confirmation_not_met; defensive_regime_unavailable_not_assumed |
| 2026-10-01 | 10% | 2026-10-13 | 2026-10-09 | none | none | 2026-10-22 / -21.95 | severe_VIX_branch_not_met; support_break_branch_not_met; stress_confirmation_not_met; defensive_regime_unavailable_not_assumed |
| 2026-10-01 | 15% | 2026-10-14 | 2026-10-09 | none | none | 2026-10-22 / -21.95 | severe_VIX_branch_not_met; support_break_branch_not_met; stress_confirmation_not_met; defensive_regime_unavailable_not_assumed |
| 2026-10-01 | 20% | 2026-10-22 | 2026-10-09 | none | none | 2026-10-22 / -21.95 | severe_VIX_branch_not_met; support_break_branch_not_met; stress_confirmation_not_met; defensive_regime_unavailable_not_assumed |

Extended period: 3 executed reduction episodes; FIFO missed recovery including residual units marked at period end $5631.35 per $10,000 initial account (gross diagnostic, not total strategy underperformance).

| Sale | Restore | Sessions reduced | Sale / restore price | Rebound from post-sale low before restoration % | Missed rise vs sale $ |
|---|---|---|---|---|---|
| 2024-08-06 | 2024-08-13 | 5 | 89.20 / 96.62 | 11.31 | 220.61 |
| 2025-04-04 | 2025-05-02 | 19 | 70.65 / 79.58 | 22.96 | 260.29 |
| 2026-03-30 | 2026-04-07 | 5 | 362.66 / 374.13 | 16.26 | 324.80 |

Extended limited price replay return: Overlay 862.22%, Buy & Hold 918.61%; difference -56.39 percentage points, including modeled costs. This is separate from the gross FIFO diagnostic.

## Alternative indicators: descriptive evidence, not strategy tuning

Fixed, conventional features are calculated before inspecting outcomes: last-5-session return minus previous-5-session return (fall acceleration); prior-20-close drawdown <= -10%; below/crossing MA20 or MA50; 20-session return relative to QQQ < 0; positive five-observation VIX change. None is added to the running engine. No October-specific threshold fitting or parameter selection is performed.

indicator-evaluation.csv separates 2024–August 2026 from the requested window. It reports both active and inactive observations, full/censored forward-20-session horizons and the frequency of a subsequent >=10% decline measured from the signal close. Labels never cross the period boundary. Daily-signals.csv contains no forward outcomes. These overlapping observations are descriptive and correlated; they are not independent trials, an untouched holdout or proof of predictive value. Missing broad-market breadth cannot be tested. Most late-October signals lack a full follow-up horizon and are censored rather than assigned an invented outcome.

| Symbol | Indicator | Pre-window active / inactive next-20 loss >=10% rate | Requested active / inactive rate |
|---|---|---|---|
| AMD | fall_accelerating_5 | 34.2% (n=228) / 35.7% (n=420) | 0.0% (n=5) / 33.3% (n=12) |
| AMD | local_drawdown_10 | 37.4% (n=222) / 34.0% (n=426) | 0.0% (n=3) / 28.6% (n=14) |
| AMD | below_ma20 | 38.3% (n=300) / 32.5% (n=348) | 0.0% (n=3) / 28.6% (n=14) |
| AMD | below_ma50 | 33.5% (n=316) / 36.7% (n=332) | 0.0% (n=5) / 33.3% (n=12) |
| AMD | cross_below_ma20 | 44.8% (n=29) / 34.7% (n=619) | unavailable (n=0) / 23.5% (n=17) |
| AMD | cross_below_ma50 | 55.0% (n=20) / 34.6% (n=628) | 0.0% (n=1) / 25.0% (n=16) |
| AMD | relative_weak_qqq20 | 33.1% (n=311) / 37.1% (n=337) | 0.0% (n=5) / 33.3% (n=12) |
| AMD | vix_rising5 | 35.7% (n=314) / 34.7% (n=334) | 11.1% (n=9) / 37.5% (n=8) |
| NVDA | fall_accelerating_5 | 21.2% (n=222) / 23.7% (n=426) | 0.0% (n=5) / 0.0% (n=12) |
| NVDA | local_drawdown_10 | 29.1% (n=117) / 21.5% (n=531) | unavailable (n=0) / 0.0% (n=17) |
| NVDA | below_ma20 | 24.3% (n=243) / 22.0% (n=405) | 0.0% (n=6) / 0.0% (n=11) |
| NVDA | below_ma50 | 25.6% (n=215) / 21.5% (n=433) | 0.0% (n=2) / 0.0% (n=15) |
| NVDA | cross_below_ma20 | 26.2% (n=42) / 22.6% (n=606) | 0.0% (n=2) / 0.0% (n=15) |
| NVDA | cross_below_ma50 | 17.2% (n=29) / 23.1% (n=619) | 0.0% (n=1) / 0.0% (n=16) |
| NVDA | relative_weak_qqq20 | 27.2% (n=254) / 20.1% (n=394) | 0.0% (n=5) / 0.0% (n=12) |
| NVDA | vix_rising5 | 24.8% (n=314) / 21.0% (n=334) | 0.0% (n=9) / 0.0% (n=8) |
| MU | fall_accelerating_5 | 34.7% (n=222) / 36.9% (n=426) | 0.0% (n=3) / 42.9% (n=14) |
| MU | local_drawdown_10 | 35.5% (n=217) / 36.4% (n=431) | 0.0% (n=1) / 37.5% (n=16) |
| MU | below_ma20 | 37.3% (n=241) / 35.4% (n=407) | 0.0% (n=3) / 42.9% (n=14) |
| MU | below_ma50 | 35.8% (n=190) / 36.2% (n=458) | 0.0% (n=2) / 40.0% (n=15) |
| MU | cross_below_ma20 | 44.4% (n=36) / 35.6% (n=612) | 0.0% (n=1) / 37.5% (n=16) |
| MU | cross_below_ma50 | 55.0% (n=20) / 35.5% (n=628) | 0.0% (n=2) / 40.0% (n=15) |
| MU | relative_weak_qqq20 | 38.5% (n=244) / 34.7% (n=404) | 0.0% (n=2) / 40.0% (n=15) |
| MU | vix_rising5 | 39.5% (n=314) / 32.9% (n=334) | 22.2% (n=9) / 50.0% (n=8) |

## Restoration interpretation and candidates for later tests

The recovery CSV explicitly reconciles the prior simulator diagnostic: matched_repurchase_cost_dollars + terminal_mark_cost_dollars = missed_recovery_fifo_dollars. Rebuying a full portfolio weight at a higher price may leave a smaller share count. The simulator carries unmatched sold FIFO units into later repurchases or terminal marking even after exposure returns to 100%. This is a counterfactual share-deficit diagnostic, not evidence that cash literally remained uninvested. It can greatly exceed the simple price rise up to the first restoration; both are shown separately.

HOLD means the reduction formula is false, not that the price has regained MA20/MA50, relative strength or its prior peak. Three consecutive actionable HOLDs therefore form a risk-clearance delay rather than technical recovery confirmation. Daily-close publication and next-open execution add latency; a rebound can occur while 25% of shares remain sold. Returning at a higher price also buys fewer shares after costs. Conversely, waiting can avoid a continuing decline; a positive missed-recovery diagnostic alone does not establish that earlier entry was better.

Candidate rules deserving separate predeclared walk-forward tests: one actionable HOLD versus three (speed/whipsaw trade-off); staged 1/3 restoration after each cleared-risk session; a close back above MA20 with positive relative strength; volatility normalization with hysteresis. A candidate should retain freshness checks, next-open fills and full cost accounting. Price confirmation can delay entry further; none is recommended as an improvement here and none has been substituted into the engine or simulator.

## Definitions, provenance and reproducibility

- Run `python -m aae.backtest.diagnostics`. Input/output hashes and fixed configuration are in run.json. QQQ source: data/risk-diagnostics/manifest.json; original stocks/VIX: data/backtest/manifest.json.
- Daily change uses the previous available close. MA20/50/200 include the current completed candle, which is available at decision time. RSI14 matches the existing TechnicalAnalysisEngine simple last-14-change RSI (including its flat-window convention), not Wilder smoothing.
- DD20/60/120 use the maximum CLOSE of exactly the prior N trading rows, excluding the current candle. Positive distances above a peak are clipped to zero drawdown. Support is the minimum LOW of the prior 120 available candles, not a recent high; a large drawdown need not be near that low.
- Technical deterioration is the first close below MA50, or below MA20 with negative five-session momentum, after the episode peak. It is a fixed diagnostic definition, not an engine input.
- Episodes are peak-to-recovery closing-price excursions, separately seeded at the highest close in the prior 20, 60 and 120 sessions (also considering the study start close). Identical peak/threshold pairs are deduplicated and reference_windows records the contributing windows. This retains a recent local excursion even when an older, higher peak remains unrecovered (notably MU). Each 10/15/20 threshold is counted once per excursion, not every recross. Nested excursions are descriptive and are not independent system errors. Pre-window threshold crossings and unrecovered episodes are explicitly marked; rolling daily drawdowns provide the complementary continuous view.
- Episode troughs, forward outcome rates and recovery minima are retrospective descriptions only. They never feed indicators or trading decisions. At a threshold crossing, the CSV records the actual known support, VIX, action, blockers and decision cutoff.
- Recovery minima use sale-open and completed closes before the restoration open. Rebound percentage describes the stock; sold_units_rebound_dollars describes the foregone upside on sold units. missed_recovery_vs_sale_dollars measures only positive sale-to-repurchase price change, excluding fees; it is not a full counterfactual profit attribution. Reduced exposure and fee/slippage treatment are unchanged from PR #2.
- Unavailable regime/breadth and retrospective price vintages prevent inference about the full historical Alpha OS system. Absence of TRIM under these rules is an observed signal gap, not proof of an ineffective decision. No production endpoints, databases, deployments or merges were used.
