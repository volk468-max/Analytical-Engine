# Issue23 frozen EOD amendment (2026-11-08, first commit)
Base PR22@9b68d2a9cd5f70d1f50ad430e5f3242bf03ff659, unmerged. Original intraday
contract/functions unchanged. New SECONDARY EOD_CLOSE_TOUCH10_60 only: any future
US close t+1..t+60 NAV<=.9NAVt; full60-session maturity for hits and nonhits.
A weights1/3 AMD/NVDA/MU cash0; B .2/.2/.2 cash.4, zero interest explicit.
C inverse trailing252 daily gross total returns, >=200 valid returns, including
known anchor close, capped10–50%, w_i=clip(lambda/sigma_i,.1,.5), deterministic
bisection for sum1. No covariance experiment. Inception100000USD per independent
anchor, fractional units; same no-trade shares/cash held60sessions, never rebalanced
within label. These reset recipes are NOT continuous self-financing accounts.

Before metrics fetch free Yahoo daily OHLC/split/dividend history2000–2026-11-06
for AMD/NVDA/MU and QQQ. Freeze response/time/URL/hash. If blocked, no fabricated
backtest, connectors/fixtures only. Audit XNYS calendar/duplicates/gaps/currency/
OHLC/actions. RESEARCH_PRICE_REPLAY_NOT_PIT unless original archives certified.
Separate EOD adapter: provider split-normalised Close and dividends on same unit
basis, frozen normalised units. Dividend ex-date receivable included in NAV,
no reinvestment/interest (payment-date cash transfer has no NAV effect at zero
interest). Gross no withholding. Split ratios NOT applied twice; raw response
retained, no adjclose dividend adjustment layered on this ledger. Independent
corporate-action completeness/adjustment verification unavailable => qualification
limitation, not PIT claim. No delisted substitutions; fixed survivor universe.
Daily gross returns for volatility=(Close_t+div_t)/Close_prev-1. FX USD1 only.

All eligible anchors after252warmup; gaps in trailing252/future60 suppress labels.
Snapshot weights/units at each date saved. Known QQQ regime close>=MA200 AND R20>0
UP, both reversed DOWN, else MIXED. Forecasts annual2010–26: train earlier than
Jan1(testyear), full label maturity before cutoff AND anchors60sessions before
cutoff. No current-year fit. HIST Beta(1,1), REGIME frequency shrink20 toHIST,
VOL own trailing portfolio joint-return RV20 (fixed bins annualised .2/.4/.6)
shrink20. No calibration mapping fitted; ten-bin diagnostics, no calibrated claim.
All models common test dates. Brier/logloss, frequency, probability reliability,
date-block CI120/60/180,999 draws seed2308, synchronous draws across recipes,
HAC effectiveN only where regular date series valid. Holm6 paired Brier contrasts
(REGIME/VOL vsHIST x3), exploratory, >=1%gain,CIupper<0 all lengths, logloss not
worse. No untouched holdout2021–26. No news or policy/threshold fitting.

15%HWM separate: continuous ledger NOT implemented; continuous MaxDD/budget NA.
Report descriptive within-anchor peak-to-trough60d scenario inclanchor, not actual
account DD and not15%guarantee. CashB lowers exposure, not alpha. No Tbill sensitivity.
PR22 ladder defect BLOCKING: rises/fixedanchor differs agreed last-executed trade
sell5%initial on−2%,buy5%on+2%,floor50%,cap100%. Do NOT use or silently fix; separate
reviewed patch required. No economic comparisons, production, merge/deploy/orders.
Next gate: independent action/PIT validation, future EOD forecast log; later prereg
rates surprise/credit/dated sentiment vs best simple baseline, no additive pp.
