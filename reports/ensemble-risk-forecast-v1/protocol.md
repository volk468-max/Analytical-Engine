# Ensemble Risk Forecast v1: frozen exploratory protocol

2026-11-05. New question explicitly requested: does agreement/combination improve
prediction beyond constituent models and baselines? Prior PR5–8/11–12/17 results
have been read. 2021–2026 is reused history, NOT an untouched holdout. Freeze this
protocol in Git before calculating ensemble outcomes; no tuning on test results.

## Fixed source and population
Base PR17 commit 7fe91ab87dcda3607863a19074e6d7b2400503e8, its strict forecast
package, underlying PR7 366f8cd00e8c228d4796d0abbe9997f717a3b6ad real frozen
provider bars. No downloads/new vintages. AMD/NVDA/MU, 2024–2026 test anchors,
2021+ training, 2020 warmup, price cutoff 2026-10-22. All PRs unmerged.
Availability = reconstructed next-midnight UTC, not original forecast evidence.
Use all nine down5/10/15% x 5/10/20-session tasks, TOUCH future Low primary,
TERMINAL future final Close separate secondary. Full-window maturity mandatory.
Anchor excluded, split-normalized price basis, no dividend-adjusted labels.

Five constituent probability estimators for identical task: technical_combined
(Technical Risk proxy, NOT production Technical Risk payload), v3_state
(probability mapping of fixed C/sensitive v3), technical_plus_v3 (Risk Forecast),
volatility (RV20 empirical conditional risk), regime (known QQQ price regime).
Also report v3_score as secondary constituent diagnostic, never a sixth vote.
Historical Beta frequency baseline. Breadth excluded: no verified PIT history.
All mappings use PR17 frozen estimates and its train cutoff Jan1(Y-1), full
maturity and 20-session purge. These are correlated feature families; five votes
are not five independent confirmations. Do not invent missing production models.

## Meta fitting and calibration, fixed before test
For test Y=2024/25/26 use only PR17 calibration-role forecasts in Y-1.
First half of that year's common trading sessions is META_TRAIN, second half
CALIBRATION; discard first20 sessions of second half and require every training
label's availability strictly before first calibration decision. Calibration
labels must mature before test start minus inherited20 sessions. Audit dates.
Pool all three stocks synchronously; no stock random split. Base estimators are
not refit on meta/cal/test. Next annual fold may use earlier test history as past.

Warn constituent at p>=0.5, fixed; no quantiles/target-dependent alert tuning.
A2/A3/A4/A5: count>=2/3/4/5. Probability = Beta-like empirical conditional event
frequency for binary consensus state in META_TRAIN, shrink20 to META_TRAIN
unconditional rate. No fitted calibration for A; later calibration is diagnostic.
B: arithmetic mean of five same-target probabilities, alert>=0.5.
C: logistic stacking on clipped constituent logits (1e-6), sklearn LogisticRegression
C=0.1,L2,lbfgs,max_iter2000, no hyperparameter search/standardization. Fit only
META_TRAIN; calibrate intercept only on separate CALIBRATION with fixed ridge1
penalty on intercept shift, never change slopes using calibration. Class-degenerate
training uses Laplace frequency; same rule for leave-one-model-out ablations.
C alert>=0.5. Export coefficients, calibration intercept, complete forecasts and
maturity audits. No selecting ensemble or trading policy after seeing tests.

## Metrics/inference
Common test rows per task. Export precision, recall, FPR, alert frequency, Brier,
log loss (clip1e-6), ten-bin reliability, calibration bias/ECE, error correlations
(p-y), and fixed C leave-one-out delta Brier (positive=added model helped).
By stock, year and known QQQ regime as well as pooled. Empty denominators = NA.
Synchronous circular calendar blocks preserve common market shocks, missing date
gaps and overlapping horizons; 999 repetitions, seed42117, primary length40,
sensitivity20/60. 95% pointwise conditional bootstrap intervals; no refitting
inside bootstrap, so model/design uncertainty not fully covered. Metrics strata
use399 repetitions length40, including conditional-rate/confusion uncertainty.
Primary family: 9 TOUCH tasks x six ensembles (A2–A5/B/C) x three baselines
(historical/volatility/regime)=162 paired Brier contrasts. Centered one-sided
bootstrap p values, Holm across162; support>=10 calendar40 blocks and>=10 each
class; success additionally >=1% relative Brier gain, upper CI<0 at20/40/60,
negative Brier delta in every stock and year. Others exploratory.

Agreement buckets0/1/2/3+ and exact five-bit patterns: observed event frequency,
matched-date unconditional frequency (all stocks on those dates), overall same-task
frequency, differences/ratio and paired block intervals. Export empty buckets.
Scan of patterns is post-selection exploratory; maximum descriptive uplift
reported explicitly as selected after looking, no confirmed combination. Report
nonoverlapping positive anchor-window clusters pooled across stocks (merge windows
sharing a common date) as de-overlapped clusters, NOT statistically independent
events. True independent-event count UNKNOWN; calendar blocks and CI disclosed.
No IID binomial intervals or multiplying probabilities of correlated votes.

## Economics, fixed policy
Primary economic task TOUCH10/20, all six ensembles separately, no winner choice.
Each stock independent100000USD at first eligible test anchor next open, fractional
shares, matching-cost B&H. Sell25% of current shares once per eligible warning
when flat/no pending reduction; next open delay1 primary, delay2 sensitivity.
Restore at sale+20 sessions at open using segregated sale cash only, quantity
min(sold units,cash/buy cost), surplus cash retained, no topups/leverage. No new
sale until after restoration. Continuous through test years incl. embargo gaps;
no forced sale at cutoff, open lots marked. 5bp fee+5bp adverse slippage each side,
initial costs same for B&H. Idle cash zero interest. Frozen ex-date dividends
accrue as NONSPENDABLE receivables because actual payment dates unknown; report
price-only and accrued-dividend NAV. No taxes/market impact/terminal liquidation.
Full daily/share/cash/order ledger, maxDD, final NAV, cash fraction, missed dividends,
false-warning opportunity mark on restored lots (hit label false; avoid claiming
causal attribution of entire portfolio difference). Delay and costs not optimized.

## Decision
GO impossible without independent/PIT validation. Report RESEARCH ONLY if useful
hypothesis remains; NO-GO for deployment or confirmed advantage if criteria fail.
Prospective plan: freeze code/models/thresholds now, log actual timestamped
forecasts before opens, reserve future data from next session after publication,
minimum two years AND>=30 de-overlapped market episodes; blinded power calculation
using historical block variance for1% Brier improvement, extend if insufficient.
Holm family and independent economic/PIT gates retained; no peeking/reselection.
Separate Draft PR, append-only knowledge, no production edits, merge/deploy,
purchases or trades. Any correction gets explicit note, never silent retuning.
