# Risk Forecast v1 — frozen protocol

Written and committed before calculating forecast study results. Research only:
no trades, position sizing, economic simulation or changes to v3 rules.

## Inputs and outcome definitions

Reuse the hash-verified retrospective PR #5 source pack and archived causal
indicators carried by PR #6. AMD/NVDA/MU, 2021–22 October 2026; 2020 is existing
indicator warmup. No invented observations or unfinished October 23 session.
For an anchor completed close P, thresholds 5/10/15%, horizons 5/10/20 subsequent
stock sessions. DOWN: any subsequent Low <= P*(1-threshold); UP: any High >=
P*(1+threshold). Exclude the anchor candle. Label each direction independently;
both may occur. Compare first-hit sessions; on a same-session tie opening below
DOWN establishes DOWN_FIRST, opening above UP establishes UP_FIRST, otherwise
UNKNOWN_INTRADAY. Terminal close return is separate. If horizon is incomplete,
primary labels and terminal return are null, observed-to-date hits are retained
as censored descriptive bounds. Labels mature only when the full horizon's last
bar has been published, even if a barrier was hit earlier.

## Signal and probability walk-forward

Use unchanged model C with the original annual walk-forward profile from PR #5:
2023/2024/2025/2026 choices must have training ends before the test year. For each
fold replay the SAME original profile on archived 2021+ indicators for fitting
probabilities; no future profile is chosen for an earlier test year. Replay uses
unmodified evaluate(), not a reconstruction of its rules. Test states/scores must
match archived walk-forward signals. 2026 remains the original C/sensitive.
2021–2022 are training/descriptive only; do not invent out-of-sample forecasts.

Freeze probabilities at Jan 1 UTC each test year. Include only anchors >=2021,
valid inputs, anchor earlier than cutoff and FULL horizon publication <= cutoff.
No within-test-year updating, future training labels or test-driven tuning.

Fit transparent per-stock empirical probabilities with fixed shrinkage strength
20 to that stock's training unconditional probability (Beta(1,1) smoothed).
All bins are fixed before calculation, not sample quantiles:
- dd20 severity: boundaries 5/10/15/25 percent;
- annualized RV20: 20/40/60/80/120 percent;
- MA50/RSI: below-MA50 flag and RSI bins at 30/45/55/70;
- v3 states HOLD/WATCH/REDUCE/CRITICAL;
- v3 score bins 0–2, 3–4, 5–6, 7–8, 9–11;
- technical_combined: joint dd20, RV20, MA50/RSI cell;
- technical_plus_v3: joint technical cell plus state and score bin, shrunk to
  technical_combined's training probability (same parent model, no leakage).
Absent cells back off to their parent. No model or probability weight selection.

Numeric point estimates remain auditable research values, never confident live
probabilities. Mark LOW_SUPPORT if a conditioning cell has <60 training anchors,
<10 positive or <10 negative outcomes, or occurrences in <5 fixed 40-session
calendar blocks. Export raw cell counts/backoff, train maturity and support status.

## Dependence and metrics

Held-out per-stock and pooled metrics for all 18 direction/horizon/threshold
combinations: event rate, Brier, log loss (clip only numerical scoring at 1e-6),
ROC-AUC and noninterpolated average precision (explicit PR-AUC convention),
calibration. Ten fixed reliability bins. Export state/exact-score observed rates,
score-frequency slopes and their uncertainty; higher score need not imply a
monotone DOWN probability, particularly if it predicts volatility in both directions.

Synchronous calendar moving-block bootstrap preserves overlaps AND common stock
shocks: block length 40 sessions, 399 resamples for metric/calibration intervals;
1999 for paired primary loss differences, deterministic seeds. Keep all symbols
for a sampled date together. Bootstrap conditions on already-fitted chronological
models; it does not remove model-design bias or all training uncertainty.
95% intervals, effective N from capped Bartlett/Newey–West variance on calendar-
daily panel means (lag40), raw N, date count and number of 40-session blocks.
Effective N is a diagnostic, not independent daily trials. Calibration subsets
report block counts; no made-up effective N for irregular conditional samples.
Also inspect block20/60 and calendar-year results, no independent-window t-tests.

Primary incremental comparison: technical_plus_v3 vs technical_combined for all
18 tasks, paired Brier/log-loss differences with shared date-block draws.
One-sided centered bootstrap Brier tests, Holm across these 18 hypotheses.
Practical improvement criterion fixed at >=1% relative reduction in Brier score;
require multiplicity-adjusted p<0.05, negative 95% Brier-difference interval and
stability to block20/60 before claiming evidence. Other model contrasts/score
slopes are exploratory, not 18 independent confirmations or causal attribution.
No selection of a best horizon, stock, threshold or October configuration.

## Error analysis

Export all complete 20-session/10% examples of REDUCE-or-CRITICAL with UP hit and
HOLD with DOWN hit, including simultaneous barriers. Late REDUCE uses original
v3 event diagnostics (more than half observed fall before warning / after trough).
Gradual deterioration while HOLD: three consecutive HOLD, dd20 worsens >=3 pp
versus five sessions ago AND (RV20 rises >=10% or RSI falls >=10 points).
Retrospective labels never enter predictors. Report first chronological example
per stock/category, and state explicitly when none qualifies. September–October
2026 is a diagnostic slice, never a fitting or selection sample.

## Historical validity

Retrospective split-adjusted price vintages and inferred publication timestamps
are not an independently verified point-in-time archive. Constant split-scale
invariance is useful but not proof of vintage correctness. This is price-barrier
research, not dividend total returns. No production readiness, profitability or
investment effectiveness inference. Report insufficient support and absence of
incremental predictive evidence plainly.
