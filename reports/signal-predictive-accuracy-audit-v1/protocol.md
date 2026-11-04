# Signal Predictive Accuracy Audit v1 — frozen protocol
Base main a14ebf9c268bea5cb01de962edfb98b8df94652a.
Sources PR11@5d5092b5d03e16f03241c1b5a5d5a19c1816c9c7, PR10@ef1a3a76c1c0d455f48a9d787f1c04961c244b91, PR9@7135c2bdc0653986d93dfcfc66b202a6fb2f741e.
2021-01-01..2026-11-02 with2020 indicator warmup. No trading/PnL strategy, production changes, deploy, merge or real orders.

## Evidence classes
A original contemporaneous production payloads with verified original timestamp/config.
B saved research/reconstructed snapshots, their calculation date NOT historical decision time.
C new retrospective outcome/diagnostic calculations.
D missing/unverified original production data UNKNOWN; never infer HOLD.
Use exactly PR11 historical sector_flag activation CSV, verify immutable source SHA and exact reconstructed rule/dates.
Fixed7 five-session returns,>=4negative AND mean<QQQreturn5, rising edge; no additional factors.
Inspect available saved Risk Engine/Overlay/Forecast archives separately. Do not represent research archives as live warnings.

## Targets and exact clock convention
Primary assets11 audit stocks, eligibility unchanged (NBIS2024-10-21). Secondary market cohort QQQ,SPY,S&P500,NasdaqComposite,SOX,SOXX,SMH. Never pool stocks and overlapping indices as independent observations.
Anchor OPEN: next available verified regular-session open after warning and after assumed signal availability; no slippage or fees (price predictive audit).
Horizon h consists of h regular sessions starting WITH the execution session: return1 is that session close/open−1. This intentionally differs from PR11 subsequent-full-session labels.
Secondary anchor CLOSE: signal-day close; evaluation bars start next session, same future window.
No future quote invented if final-day warning lacks next open.
Returns1/3/5/10/20, extrema5/10/20, down3/5/10/15% hit/latency, up5% hit and order, min/max20 with dates.
Price-only split-consistent units; dividends not reinvested/total-return adjusted. Nominal displays labelled separately.

## Primary classification
TP: down5 touched before up5 within10 evaluation sessions.
FP: up5 first, or full10sessions without TP (including neither threshold reached).
UNKNOWN: first down/up hit occur in the SAME daily bar; never guess intraday order, even if gap information could refine it.
UNRESOLVED: insufficient observations/anchor to determine outcome.
Partial windows may already establish TP/FP/UNKNOWN, but main precision comparisons use ONLY full10session outcomes, avoiding informative censoring.
Report UNKNOWN separately, not FP. Main precision TP/(TP+FP), conservative/optimistic bounds TP/(TP+FP+UNKNOWN) and(TP+UNKNOWN)/(TP+FP+UNKNOWN).
Secondary matrix: down thresholds3/5/10/15 vs FIXED up5, horizons5/10/20. Primary5/10 unchanged.
Future extrema/orders are outcome labels only, not features.

## Statistics and dependence
134 saved unique warning dates are date clusters, not statistically independent market experiments.
Report stock-level pooled and equal-date-weighted rates separately, per ticker/year/regime and market cohort.
Also report nonoverlapping10session warning subset size and number of60session calendar blocks; neither called exact independent ESS.
Regime frozen PR11 QQQclose/MA200/R20, known signal-close information. No trading effect.
Pre-warning DD20/DD60 and past5/20returns measure already-observed deterioration; compare covered events before threshold.
CI via synchronous moving-calendar-block bootstrap, length60sessions primary,1999replicates, seed20261103.
Stocks on a date and shared control dates resampled together; block20/120 sensitivity. No daily independence assumption.

## Baselines, fixed BEFORE outcomes
1 Random matched date controls: same calendar quarter, known QQQ regime and stock-eligibility signature; full10session evaluable; actual signal dates excluded.
2 Mechanical QQQ warning: QQQ five-session return<0 rising edge, using only past/current completed bars. Match same cells/frequency as above.
Candidates never selected by future outcome. Empty cells remain UNMATCHED, never relax matching after seeing results.
500 deterministic seeded cluster panels with replacement for diagnostic null distributions, preserving per-cell count and simultaneous stock cluster. Reuse disclosed, not independent new samples.
Main control estimator exact candidate mean, paired to each actual warning; bootstrap reweights BOTH actual dates AND shared candidate dates using the same sampled calendar blocks.
Familywise95% inference across two primary contrasts uses97.5% CIs each (Bonferroni); effect sizes in percentage points, block sensitivity also shown.
Additional random controls matched on mean current DD20 bins<3/3–5/5–10/>=10% are prespecified SECONDARY exploratory conditioning.
Report incremental evidence only if improvement survives both primary controls/dependence sensitivity; not imply causality, pristine holdout or trade profitability.
No model fitting/threshold optimization.

## Missed falls: separate event catalogue
Known closing peak seeded by prior20available sessions at study/eligibility start; update peak on new closing highs.
Merge all nested declines until full close recovery of original peak; retain incomplete events. Catalogue >=5% episodes, first close crossing5/10/15%.
This is a full-recovery episode definition, not a claim to enumerate every minor local oscillation.
At each threshold: warning SESSION strictly before threshold session and next-open executable by threshold close.
Windows prior5/10/20sessions. Report signal lead and execution lead separately; same-close warning too late.
Warning dates before asset eligibility cannot count. Recall based on NEW activations, not repeated active state.
Also report sector state already active at threshold to distinguish old active warning vs no recent new warning.
Do not sum nested5/10/15threshold counts as independent events.
Sensitivity seed60 and recovery98% only, fixed before results; never pick favorable episode definition.

## Deliverables / stop
Russian summary, full signals/outcomes/classifications, depth/speed, missed events, stock/year/regime tables, primary/secondary baselines, controls/panels and bootstrap, source inventory, code/tests/verification.
Publish checkpoints. Original publication timestamps/vintages and fixed-current-survivor bias remain explicit limitations.
No production-readiness claim and stop at Draft PR.
