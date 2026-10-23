# Historical Drawdown Anatomy v1 — frozen event-first protocol

Research only. No changes to HOLD/WATCH/REDUCE/CRITICAL or trading operations.
Freeze definitions before feature/event associations are calculated. Build the
catalogue first; only then compare prespecified features and user hypotheses.
2021–2022 are discovery/training. Annual 2023–2026 tests are chronological but
NOT untouched independent validation: this history has already informed Alpha OS
research. Newly added stocks offer cross-stock transport diagnostics, not a
survivorship-free or historically blind holdout.

## Catalogue

One consistent provider split-adjusted OHLC basis. Closing high-water mark since
first available 2020 observation; NOT a claim of lifetime all-time high before
available history. Equal highs reset to the latest equal high. An episode begins
at the first strictly lower close following that peak, ends only on first close
>= that peak, and includes every nested decline until then. Retain all >=10%
episodes intersecting 2021–22 October2026, including those starting in2020 and
left-censored/missing prehistory. Buckets [10,15), [15,25], (25,infinity). Crossing
-5/-10/-15/-20 and trough use closes. Recovery is genuine prior-peak recovery,
not merely a rolling high. Right-censored and left-truncated events stay marked.
Sensitivity: high/low instead of close extrema, recovery at 98% instead of 100%
of peak, and retain threshold12% instead of10%. No definition is selected by fit.

## Causal features

Snapshots 60/40/20/10/5 sessions BEFORE first declining session; no future peak or
trough passed as a feature. Only observations published by snapshot time. Prior
significant low is the most recent confirmed five-left/five-right local closing
low at least5% below the maximum over the preceding20 sessions; confirmation
must already have happened. No unconfirmed future troughs. Compute 20/60/120
returns, rise since confirmed low, 20-vs-previous20 growth change, MA20/50/200
distances; matched QQQ/SOX relative returns10/20/60 and changes; peers; RV20/60,
RV20 change20, WilderRSI14, five-session MA slopes, current volume/prior20 mean,
negative-close frequency20, five-session return acceleration, market correlation
20 vs preceding20; VIX and lagged DGS10 if actually obtained.

Price publication conservatively next UTC midnight; yield observations become
available after two subsequent stock-calendar sessions and the next midnight.
This is an assumed conservative lag, not an original-vintage attestation. Do not
fill unavailable fundamentals or market-wide breadth with present-day values.

## Controls and single features

Cohort anchors every20th stock session from 2021 (fixed grid). Label next60 fully
observed closes: large correction if min return<=-10%; small if -10%<min<=-3%;
growth if min>-3% and terminal>=5%; sideways if min>-3%, |terminal|<5% and closing
range<=15%; otherwise mixed. Keep mixed/censored rows, do not reassign/drop them.

For each event/presnapshot match up to3 cohort anchors PER outcome class, same
stock, same causal QQQ regime (aboveMA200 and ret60>0 / below and ret60<0 / mixed),
same two-year calendar block (2021–22,2023–24,2025–26), excluding within20 sessions
of snapshot. Rank by absolute calendar distance then earlier date, never by
feature value. Retain NO_MATCH rows. Controls can repeat; mark reuse counts and
inverse-reuse weights. Matched comparisons are descriptive and not a source of
population probabilities or independent tests. Predictive rates use the entire
fixed cohort/daily panels, never case-enriched probabilities.

Prespecified individual flags: ret20>=10%, ret60>=20%, ret120>=40%, confirmed-low
rise>=30%, growth deceleration>=5pp, MA50 distance>=10%, MA200 distance>=20%,
relative20 weakness<=-5pp, sector weakness>=50%, RV20/RV60>=1.1, RSI>=70,
MA20 slope<=0, volume/prior20>=1.5, negative20>=60%, fall acceleration<=-3pp,
correlation20 rise>=.15, VIX>=25, |yield20 change|>=25bp.
Report all flags, not a winner chosen from many combinations. Exploratory flag
associations receive Holm correction across the complete tested flag family.

## Fixed hypothesis definitions (no search)

H1 overheating: ret60>=20%, distanceMA50>=10%, RV20/RV60>=1.10.
H2 lost leadership: relative20<=-5pp versus QQQ or SOX while THAT benchmark's
20-session return is positive.
H3 sector deterioration: >=50% of available other semiconductor peers have
ret10<0 AND relative20 versus QQQ<=-3pp; require>=5 peers. Fixed survivor basket,
exclude target itself. Never call this market-wide historical breadth.
H4 fundamental downgrades: unavailable unless original published EPS/guidance
versions are obtained. No substitute with reported EPS or current valuation.
H5 regime shift: QQQ<MA50, QQQ RV20/RV60>=1.1, (VIX>=25 or VIX20 change>=20%),
AND |known lagged DGS10 change over20 stock sessions|>=25bp. Without usable yield
history fullH5 is DATA_UNAVAILABLE; an incomplete market proxy is descriptive,
not a tested replacement for H5. All new price/yield sources remain retrospective.

## Forecast and inference

Primary target: any future close at least10% below anchor close in next60
sessions; secondary20. This is anchor-price risk, not foreknowledge of a future
catalogue peak. Also evaluate shallow/near-high anchors (current expanding DD
>=-5%) to distinguish precursor evidence from ongoing-decline continuation.
Only full-horizon published labels can enter training at Jan1 cutoff. Freeze
probability fits for each whole next year; original annual C profile is unchanged.

Per-stock fixed L2-logistic estimators (ridge1, intercept unpenalized, training-only
standardization; no hyperparameter selection): historical smoothed frequency,
RV20, DD60, relativeQQQ20/SOX20, v3 state, joint baseline including all these,
and joint + one fixed H1/H2/H3/H5 flag. Missing inputs suppress that comparison;
paired comparisons use identical samples. Do not optimize thresholds from OOS.

Primary inference: H1/H2/H3/H5 joint additions, primary AMD/NVDA/MU, horizon60.
Synchronous date blocks120 sessions preserve common shocks and overlapping
60-session paths;1999 paired loss resamples. Holm across all testable primary
hypotheses, not only promising ones. 95% intervals, practical criterion>=1%
relative Brier improvement. Require negative interval at block60/120/180, negative
point differences for>=2/3 primary stocks, and same direction on the expanded
stock group before calling a pattern provisionally supported. This still does
not establish untouched independent confirmation or investment effectiveness.
Brier, logloss, empirical risk ratios, recall, false-warning share, event lead,
stock/year stability, effective N and block counts are exported. Ratios must
have mature positives/negatives; sparse/absent conditions explicitly insufficient.
Primary intervals on risk ratios and frequency contrasts use399 shared blocks.
Single-feature and other horizon/subgroup comparisons are exploratory. Event
coverage and event leads use only exposures strictly before onset; retrospective
offsets/peaks/troughs are labels only. Missing control matches and incomplete
future horizons cannot become fabricated non-events.
