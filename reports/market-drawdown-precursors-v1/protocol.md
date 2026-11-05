# Issue19 — Market drawdown precursors v1: preregistered protocol

2026-11-05. Commit and publish BEFORE associations or model outcome comparisons.
Issue19 is a NEW question: market episodes and their pre-onset conditions, not
PR8 individual-stock anatomy or PR17/18 ensemble replay. Those results were read;
2021–2026 and any earlier familiar crises are exploratory, never pristine holdout.
Research only; no trading backtest, production edits, paid data, Norgate/Windows
acquisition, live infrastructure, merge or deploy. Scope changes require addenda.

## Stage0/1 data gate before outcome analysis
Attempt one free Yahoo chart request each for SPY,QQQ,SOXX,AMD,NVDA,MU,
2000-01-01 through2026-11-02 inclusive, daily regular-session OHLCV/actions.
Freeze raw response/retrieval UTC/URL/SHA256; never silently refresh after outcomes.
One bounded retry only for transient errors, no endpoint circumvention. If any
series fails structural/calendar audit, use a SINGLE already frozen PR11 source
snapshot@5d5092b5d03e16f03241c1b5a5d5a19c1816c9c7 for ALL six instruments, not
stitched vintages. If that fails, stop affected tasks; no synthetic substitutions.
SOXX is the sector ETF price proxy, NOT true breadth. Actual firstTradeDate and
coverage must be recorded; no pre-inception ETF reconstruction. Source PR8/17/18
versions are pinned in source-research.json; base branch PR18@43886c0516b35bcfd61afce583b17112ce94bce0.

Audit separately: duplicate/missing exchange sessions, OHLC consistency/positive
prices/volume, firstTradeDate, split/dividend events, raw-vs-normalized equality,
split-unit continuity and overlap with frozen archives (report differences, never
choose source by outcome). Calendar exchange_calendars4.11.2/XNYS; exact close
including early closes/DST. No filling invested dates. Only uninterrupted windows
can yield features/labels; gaps suppress observations, no return over missing bars.
Treat all OHLC as provider split-normalized price-only basis, never mix adjclose
into features/labels or double-apply splits; retain corporate action evidence.
Decision at next00:00UTC after session, conservative ASSUMPTION, before next open.
Future labels require entire h sessions published, even if barrier was hit early.

Two qualification levels kept distinct. AUDITABLE_RETROSPECTIVE_PRICE means
raw/hash/calendar/causal-prefix reconstruction passes, permits only explicitly
exploratory price-only diagnostics. It does NOT attest original PIT publication
vintages/adjustments; PIT_CERTIFIED requires original dated evidence, absent unless
actually supplied. No 2000–2026 PIT claim from a fresh chart response. Unqualified
factors STOP/NO-GO, never impute revisions or assume present-day breadth membership.
If no PIT-certified panel exists, the original predictive-core deployment gate
stays NO-GO even if limited retrospective diagnostics are calculated.

## Targets and distinct populations
A MARKET:SPY,QQQ,SOXX, each separately; pooled MARKET estimates keep all three
on each date, never pool with B STOCK:AMD,NVDA,MU. B tests incremental stock
features above a common market/sector-information baseline; report each stock.
Primary TOUCH5/10: min Low[t+1:t+10]<=Close[t]*(1-.05), inclusive1e-12
price-relative tolerance. Secondary TOUCH10/10,5/20,10/20,5/60,10/60.
TERMINAL same thresholds/horizons but Close[t+h], separate family. Anchor candle
excluded; incomplete windows explicitly censored. Price returns, not total return.

Catalogue MARKET only: closing observable-history high watermark, latest equal
peak; onset first strictly lower close; threshold first Close<=95%peak; trough
lowest closing price before recovery; recovery first Close>=peak. Retain episodes
>=5%, all nested declines remain in one episode until actual recovery. Peak before
available data UNKNOWN, left truncation flagged; unrecovered end is right-censored.
Report dates5/10/15%, depth, duration, onset-to-threshold/trough, first60-session
post-onset depth and whether enough60 sessions observed. High/Low used for forecast
labels only, not retrospectively substituted into this closing-episode catalogue.
Across proxies, merge overlapping episode intervals into market episode clusters;
nonoverlap is NOT proof of statistical independence. No count of stock-date labels
is called independent events.

## Frozen price-only families (all use data available at decision)
Common regime: QQQclose>=MA200 AND R20>0 ->UP; below AND R20<=0 ->DOWN; elseMIXED.
Warmup252 sessions. Compute each daily feature on completed contiguous bars only.
Baseline inputs own logRV20, QQQ and SPY close/MA200-1 and R20 (two trend regimes).
Market M: QQQ R20 minus SPY R20, QQQ RV20/RV60, SPY RV20/RV60.
Sector S: SOXX R20 minus QQQ R20, SOXX RV20/RV60.
Stock X (B only): own close/MA50-1, own R60, own R20 minus QQQ R20,
own RV20/RV60. No stock-family feature claims on MARKET tasks.
No volume/concentration series without stable PIT holdings; no unbounded conjunction
search. Any other novel factor is excluded, not added after observing results.
VIX, credit/yields/liquidity, true market/semiconductor breadth, fixed-survivor
peer breadth/concentration and H4 revisions audited for availability but excluded
from primary fits unless independently documented original timestamps/vintages
AND a scope addendum is published BEFORE their evaluation. No such substitution
is automatic. Excluding fixed survivor breadth avoids implying genuine breadth.

Fixed univariate flags for prevalence/anatomy, not tuned predictors:
market_relative_weakness QQQ R20-SPY R20<=-.03;
market_vol_acceleration max(QQQRV20/RV60,SPYRV20/RV60)>=1.10;
sector_relative_weakness SOXX R20-QQQ R20<=-.03;
sector_vol_acceleration SOXXRV20/RV60>=1.10;
stock_extension ownMA50dist>=.10 AND ownR60>=.20 (B only);
stock_relative_weakness ownR20-QQQ R20<=-.05 (B only);
stock_vol_acceleration ownRV20/RV60>=1.10 (B only).

## Descriptive anatomy and controls
Snapshots at onset minus60/40/20/10/5 sessions. Event peak/trough dates are only
labels used to place snapshots, never features. Snapshots strictly before onset;
future or within-decline snapshots excluded and missing warmup retained as NA.
Controls: ALL eligible non-onset-exposed dates, not only known-crash dates. For
matched anatomy, up to3 nearest same-proxy, same causal regime, same two-calendar-
year block dates; at least60 sessions away from target onset and outside ANY
qualifying market episode on that proxy (including its onset). Rank abs calendar
distance then earlier date, never future feature value. Case-enriched matching is
descriptive only; record reuse/inverse reuse weights, NO_MATCH explicit. Do not
train probabilities on these matched samples. P(flag|touch),P(flag|no touch),
P(touch|flag), unconditional risk, false alarms, recall and lift use ALL eligible
daily anchors, each target/population separately. Pre-onset coverage/lead times
by flag/offset/events separate from predictive-window recall, with cluster counts.
Report near-high anchors own expanding DD>=-.02 as a prespecified diagnostic:
it is a causal near-high filter, NOT evidence every anchor is before future onset.

## Stage2 chronological predictive evaluation
Use whole calendar years eligible given audited history. If earliest source2000,
first test2010; else first test2024 for fallback2020. For testY: base/model train
from earliest eligible anchors up toJan1(Y-1), fully matured labels;20-session
anchor purge (60 for h60). Calibration yearY-1, first/last max(20,h) sessions
purged; its labels must fully mature before the last max(20,h) sessions preceding
Jan1Y. TestY first max(20,h) sessions purged, only full future labels at cutoff.
At least200train and60cal anchors, otherwise NO_FIT. Base/model frozen for year;
no randomized row/stock splits. Earlier tests may become past training later.

Fit per instrument/task, fixed L2 logistic C=.1,max_iter2000, training-only
standardization (zero variance ->scale1), no feature/hyperparameter selection.
Degenerate training class ->Beta(1,1) frequency, no invented convergence.
Models: HIST expanding frequency fixed at each annual fit; VOL logRV20;
REGIME empirical UP/DOWN/MIXED rate shrink20 to HIST; SIMPLE logistic on own
logRV20 + QQQ/SPY MA200distance/R20; SIMPLE+M, SIMPLE+S, MINIMAL=SIMPLE+M+S.
B additionally MINIMAL+X (stock-specific incremental model); no market/stock
labels merged. For each logistic model calibrate ONLY intercept on separate cal
year, ridge1 penalty on shift; fixed slopes, no refit on test. HIST/REGIME remain
uncalibrated raw baselines. Report raw and calibrated probabilities separately;
primary metrics use calibrated logits and raw HIST/REGIME. No winner chosen later.

Operating thresholds p>=.20 and p>=.50 for EVERY probability estimator/task.
Scores Brier/logloss(clip1e-6), bias, ten fixed-bin reliability/ECE, precision,
recall,FPR,warning frequency,conditional base-rate lift and event counts; empty
ratio=NA. Per instrument, year, causal regime, era(2000–02,2003–07,2008–09,
2010–19,2020,2021,2022,2023–26 where observed), and causal near-high subset.
Report pure pre-onset anatomy separately from daily ongoing-decline forecasts.

Primary paired Brier contrasts on TOUCH5/10 ONLY:
MARKET3 proxies x [SIMPLE+M vsSIMPLE; SIMPLE+S vsSIMPLE; MINIMAL vsSIMPLE;
MINIMAL vsHIST; MINIMAL vsVOL; MINIMAL vsREGIME] =18;
STOCK3 x [MINIMAL+X vsMINIMAL; MINIMAL+X vsHIST; MINIMAL+X vsVOL;
MINIMAL+X vsREGIME; MINIMAL+X vsSIMPLE] =15; family33 total.
No replacement family when a task cannot fit; missing contrasts UNTESTABLE.
Holm across33 (missing p=1). Every secondary contrast explicit exploratory.
Synchronous circular calendar-block bootstrap, all symbols sampled together on
same date; primary9999 repeats, seed19319; lengths40primary,20/60sensitivity.
Secondary contrasts999repeats,length max(40,h); metric/prevalence intervals399.
Effective N descriptive date-level Bartlett HAC with lag=max(40,h), capped at
observed dates; undefined with gaps/zero variance; no fabricated independent N.
Primary success: Holm<.05, >=1%relativeBrier improvement, paired CIupper<0 at all
three lengths, >=10full40calendar blocks and>=10eachclass; delta<0 each test year
where>=60anchors and>=10eachclass, at least2 such years. Logloss must not worsen.
Both families report raw deltas/sign instability, failures and sparse support.
CI conditional on fitted models, not all fitting/design uncertainty; correlation
across instruments/stocks and repeated history prohibits independent validation.

## Deliverables and prospective gate
Save protocol/registration/data-qualification/source hashes/missing-PIT flags,
market catalogue/clusters/snapshots/matched controls/all-flag prevalence/lead times,
all row-level forecasts/fit audits, predictive-evaluation.csv including uncertainty
and all specified contrasts, calibration/stability, Russian executive-summary,
code/tests/knowledge updates. No NAV or B&H comparison in this work.
Prospective shadow log schema: immutable forecast_id, decision_at/input_available_at,
code SHA/protocol hash/model version/input vintage, symbol/task/horizon/threshold,
p_raw/p_calibrated/quality flags, future maturity/label resolved separately, hash
chain+append-only label records. SPECIFICATION ONLY, no infrastructure launch.
Reserve next session after publication onward, at least2years AND30 distinct
market episode clusters; blinded power study for1%Brier gain (historical block
variance), extend if insufficient; no interim tuning, retain33-wayHolm and PIT gate.

Decisions: GO for validated predictive core requires new prospective data and PIT
attestation; impossible on reused history alone. RESEARCH-ONLY for correctly
qualified retrospective diagnostics; NO-GO for unqualified factors/data windows,
production or an unsupported predictive-advantage claim. Explicitly separate a
statistically exploratory improvement from an independently validated core.
