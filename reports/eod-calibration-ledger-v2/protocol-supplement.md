# Issue25 continuation — protocol first, 2026-11-09

Supersedes the phase1 stop condition ONLY for the explicitly owner-authorized
PRELIMINARY, NON-PIT historical study. Original v1 protocol, source bytes, negative
results and audit remain unchanged. Base PR26 head82eebbd95579c022040065f67e30c369d0999906;
base PR24 head51fb1d34ddb7a28e8bbc7b2361dcfc2107890f0b, both unmerged. New evidence:
Micron issuer September25 release + Vienna October4 notice; verify exact ex/record/
pay dates, USD amount and security; record fetch times/hashes. QQQ decimal nearest
0.001 reconciliation uses half-unit bound0.0005 USD: numerical consistency is NOT
proof of vendor rounding policy or full action/price/PIT qualification. Freeze this
criterion before new metric evaluation. No historical price refresh.

Classification remains RESEARCH_PRICE_REPLAY_NOT_PIT. Missing independent complete
price/action history, historical vintages or licenses BLOCK validated claims, but
owner now authorizes clearly separate preliminary historical numerical estimates.
Do not promote v1 gate or overwrite v1 report. Verify frozen source/label hashes.

Calibration: original nested split unchanged. TestY2013–2026; base bank labels
mature before Jan1(Y-3), anchor index<boundary-60; base frozen across calibration
and test. Calibration anchors>=trainboundary+60 and maturity<testboundary-60;
test anchors>=testboundary+60, exact60 future sessions. Require240cal rows,
10events+10nonevents and4 observed calendar120session blocks. HIST Beta1/1;
REGIME/VOL shrink20 by original regime/vol_bin. Intercept-only ridge1 bounds±10
for ALL THREE models; no tuning and no global fit. Daily trailing5calendar-year
matured climatology Beta1/1 on SAME dates, using maturity strictly before t.
All models/recipes evaluated on common supported dates; skipped years documented.
Slope diagnostic only, bin/ECE descriptive, no fitted slope/isotonic alternatives.

Primary family9 = calibrated vsraw HIST/REGIME/VOL xA/B/C; secondary family9 = each
calibrated vsrollingclimatology. Paired synchronous calendar-date circular block
bootstrap9999, seed2509, L120primary,60/180sensitivity; preserve embargo gaps rather
than concatenating anchors. One-sided centered-bootstrap improvement p, Holm9
within each explicitly named family. Brier primary, logloss,bias and reliability.
>=1% relativeBrier +CIupper<0+Holm<.05 +no logloss deterioration: preliminary evidence
only, never independent validation. Also report ranking raw/cal AUC and common
regime/subperiod results; no best-model selection. EffectiveN/HAC120, calendar
blocksupport, de-overlapped60-session loss windows distinct from independent market
episodes (UNKNOWN). 35/51/60 support counts/bins with dependent CIs, NOT VALIDATED.

Ledger: self-financing normalized-share numeraire matching frozen split-normalized
prices/dividends; do not multiply shares again on provider split dates. Preserve
split memos and explain equivalence to historical shares, not original PIT units.
Inception100k, identical execution index253 (decision252 afterwarmup) for A/B/C and
staticA/B. Monthly decision on first session close of month, execution FOLLOWING
session close. C last252 total-return observations through decision only, caps10–50.
No model overlays/trims. All dividends credited to receivables from PRE-trade units
on ex-date; transfer to cash only on independently supported payment dates (MU
2024-10-23 if verified). Otherwise nonspendable forever, separately reported; this
is a conservative liquidity convention, not realistic actual settlement/P&L.
No reinvestment of unavailable receivables. Grossreceivables0%interest, fractional
shares, sellbeforebuy, cash-constrained buys, no shorts/leverage/externalflows.
Costsnotional0/10/25bp, spread0/5bp sensitivity crossproduct; no taxes or yield data.
Include inception costs; exposures calculated on full NAV inclreceivables.

Report fullperiod and2013–2019/2020–2026 marked descriptive: NAV,CAGR,annualvol,
maxDD,HWM-duration,15%strict breaches count/days/maxduration,worst60return,turnover,
fees,meanstock/cash/receivableexposure. Economic reserve cost = B vsA and staticB
vsstaticA same start/end, both terminal dollars/CAGR gap; opportunity cost is not
modelalpha or a false-alert cost. B lowerDD is lowerexposure, no advantage claim.
Subperiod rebase includes previousclose, HWM recomputed and labelled; no optimization.

Tests: hash mismatch/duplicate/negativeprices, Decimalprecision wrongamount/date,
exactmaturity/purge endpoints, future test/cal labels cannot alter earlier fitted
probabilities, future price mutations cannot alter earlier weights/NAV, frozen
labels reconstruction sample+all-label values, splits/dividendunits/receivable
payment no NAVjump, nextclose lag, fee conservation, no spending receivable,
continuousvsanchor reset, DD episode boundary. No network in numerical runner.
No production/merge/deploy/trades/paiddata/livecollection. Prospective independent
protocol/power review remains future; 2021–2026 previously explored, no untouchedholdout.
