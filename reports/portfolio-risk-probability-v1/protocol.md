# Issue21 preregistration — Portfolio Risk Probability Engine v1

2026-11-07. FIRST research commit, before prototype/results. Base unmerged PR20
8e9aec99c7eee8b384e35a3bc1aa734f2d54800d; PR8/17/18/20 negative evidence retained.
First publish minimal Draft with protocol/qualification/contract; only then code.
No production/broker/orders/paid data/Norgate/Windows acquisition/live scheduler.

PRIMARY: P(min NAV(t,u)/NAV(t,t) <= .90, u in next60 US exchange sessions).
NAV(t,u) is a no-trade shadow book with original shares/cash/FX base currency
frozen in snapshot t; corporate splits transform units, not economic exposure.
Value on synchronous marks at every available intraday valuation timestamp;
60 sessions include future sessions only, never decision candle. Full maturity
required even after early hit. Daily-close-only history is a separate lower-bound
TOUCH proxy, not exact ANY-point probability; summing asynchronous asset Lows
is prohibited. Unknown intraday path => exact primary label NA, even if daily
proxy no hit. Close hit proves a primary hit only after full label maturity.
Decision after official market close and after all inputs actually released AND
ingested; earliest candidate execution next session open. No assumed release times.
Raw unadjusted marks+explicit splits (no double split adjustment), dividend
receivable at ex-date on entitled shares, cash at documented payment date;
FX at each synchronous mark in snapshot base_currency; cash interest requires
actual accrual data. No external flows in shadow path. Delisted/missing asset,
FX, event/payment history or unsynchronised marks => NA, no forward fill/zero.
Actual rebalancing/deposits/withdrawals cannot change original shadow label.
Separate snapshots each decision, stable id/hash, PIT holdings and timestamps.

DRAWDOWN: current NAV / preceding observed HWM -1, HWM from flow-adjusted
unitised actual-account history (document flows/unit values). 15% is a risk
preference, no guarantee. Report loss from HWM in base currency and remaining
budget max(0,NAV-.85*HWM), plus fraction of current NAV. Missing HWM/flows =>NA.
SECONDARY: terminal60 loss distribution, ES5% = mean worst5% loss outcomes with
fractional boundary weights, distinct from path maximum loss/TOUCH. Asset10/20
optional NOT IMPLEMENTED, no substitution for primary portfolio target.

Actual positions/base currency/NAV/HWM, total-return/action/FX histories and PIT
archives missing: live personalised probability, calibration and economic claims
BLOCKED. Implement contracts/fixtures only; no inferred holdings or percentage.
Synthetic demo labelled SYNTHETIC_NOT_USER_PORTFOLIO at every output. No proxy
historical backtest required or allowed without further frozen portfolio spec.

Baseline design: historical rolling60-session joint asset/FX total-return paths,
reprice same frozen shadow book incl cash (not mean marginal stock probabilities).
VOL/regime baselines with same target/common dates; annual expanding train,
separate prior-year calibration, test nextyear. All labels mature before cutoff;
60-session purge/embargo at boundaries (full horizon plus gap), no random splits.
Only PIT-qualified factor families: baseline; +rates/credit; +breadth; +fundamentals;
+timestamped news. Each vs baseline (4), each vs VOL/REGIME (8): Holm12, missing
families p=1/UNTESTABLE. Fixed ridge logistic C=.1 train-only scaling, calibration
intercept on separate calibration data; no feature/threshold search. Conditional
logit contributions beta*x; shared correlation group/dedup and note attribution
non-unique, NOT independent confirmations. No additive +5/+10 percentage points.
No eligible real data here => estimators/ablations not fitted, metrics NA.

Future evaluation: Brier/logloss, bias/ECE/10 bins, precision/recall/FPR and false
alarm fraction separately, coverage/lead, base rate/lift at .35/.51/.60. Paired
synchronous calendar blocks120 primary,60/180 sensitivity,9999 draws, date-level
HAC effectiveN only where valid. No IID stock-window independence. >=1% relative
Brier gain preliminary; Holm<.05, all CI upper<0, no positive logloss delta or ECE
worsening, sign stable across eligible years/regimes. No untouched2021–2026 holdout.
No formal power claim from fixtures; all unsupported metrics NA.

Policy experimental ONLY: WATCH .35 no sale; .51/.60 cumulative original exposure
trim targets explicitly supplied by caller, never inferred/optimised. Hysteresis,
confirmation, cooldown, single pending next-open intent, no repeated daily sale;
reentry separately confirmed with cash constraints. Fees/slippage/tax require
explicit assumptions, unknown => no economic metrics.15% budget breach is alert,
not automatic sell or proof protection. Original Tactical Ladder separate:5% of
original units per +/-2% from fixed inception anchor, remaining floor50%, no
borrowing; test mechanism separately. B&H/risk-matched simple overlay/ladder/new
policy economic comparison BLOCKED pending portfolio/data/execution assumptions.
Combinations NOT DONE, require new preregistration. No actual orders ever emitted.

Shadow log: append-only hash chain with timestamps, input/code/protocol SHA,
snapshot id/hash, baseline/final P and CI (nullable), provenance/quality/logit
attribution; separate matured label/correction records. Runnable offline mock
only; no live collection claim. Power: pilot actual PIT shadow inputs first,
blinded block-variance simulation of sample size needed for1% Brier gain at80%
power/Holm12; estimate episode arrival rate and precision, monitoring data-quality
only, no interim efficacy peeking.90 days insufficient for power guarantee;
no requirement of30 rare independent market clusters in2years.

GO only for review of contracts/fixtures. NO-GO calibrated personalised forecast,
protective deployment/economic advantage until qualified real inputs and genuinely
new independent evidence. Results must separate DONE/BLOCKED/NOT DONE.
