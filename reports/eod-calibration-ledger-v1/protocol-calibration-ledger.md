# Issue25 preregistration / 2026-11-08 — FIRST commit
Base DraftPR24@51fb1d34ddb7a28e8bbc7b2361dcfc2107890f0b; unchanged and unmerged.
Prior evidence read, not recomputed before this commit. EOD_CLOSE_TOUCH10_60 remains
secondary to original intraday target. A/B/C as PR24;100kUSD hypothetical, B cash0%.
15%continuous flow-adjusted HWM drawdown is a separate budget, not a guarantee.

Phase1: reuse ONLY PR24 frozen Yahoo raw bytes/hash, no price refresh. Independent
sample fixed BEFORE retrieval: NVDA2024-06-10 split10:1 (NVIDIA2024-05-22 results
release); NVDA2021-07-20 split4:1 (NVIDIA2021-05-21 release); MU2024-10-07 dividend
.115 USD (Micron2024-09-25 results release); QQQ2024-03-18 dividend .573 USD
(Nasdaq historical dividend page). AMD no split in study window: absence is NOT
independent proof of completeness. Official issuer sources for NVIDIA/Micron,
independent exchange page for QQQ. Save URL/status/retrievalUTC/bodyhash/license
unknown unless actually supplied. Human-readable dated amounts/ex dates and price
unit continuity must reconcile; HTTP200/keyword alone is NOT a pass. Missing page,
JS/no event record/403 or mismatch => BLOCKED action qualification, no fake PIT.
Source classification always RESEARCH_PRICE_REPLAY_NOT_PIT, survivor-selected names.
No speculative same-close fills. Do not route around denied sources/paywalls.

Phase2: minimal primary intercept-only logistic recalibration, fixed ridge1 on
shift, bounds[-10,10]. HIST IS calibrated alongside REGIME/VOL. For testY2013–26,
base train maturity<Jan1(Y-3), anchors at least60sessions before boundary; frozen
base forecasts for calibration yearsY-3..Y-1 and testY (no retrospective forecast
backfill from a newer base fit). Calibration anchors first60sessions excluded;
label maturity strictly before test boundary minus60sessions. Require>=240 anchors,
>=10positive/negative and >=4 effective120blocks; else BLOCKED. Test first60sessions
embargo; full60future closes required. Same-date matured trailing5year climatology
baseline, no label unknown at forecast. No global2010–26 calibration. Secondary
slope/isotonic NOT DONE due effective-support/design gate, not fitted opportunistically.
Real empirical outputs gated on independently reconciled actions; if gate fails,
minimal runnable calibration implementation+synthetic fixtures only, real metricsNA.

Future qualifying comparison family9: each calibrated HIST/REGIME/VOL vs its raw
version x3recipes; Holm9,9999synchronous date-block120,60/180sensitivity, same test
rows. Brier primary, logloss no deterioration, bias/ECE10bins diagnostic, slope
only identifiable, threshold35/51/60 support/count/effectivebinN/CI; NOT VALIDATED
without independent evidence. >=1% relative Brier preliminary and allCIupper<0;
no 90day power promise. Intercept changes marginal bias, not ranking information.
Blinded alternative/power simulation needed before prospective efficacy monitoring.

Phase3 fixed design: monthly weights from previous close; execute following close
ONLY (opens not qualified). Continuous shares/cash/dividend receivable ledger,
no external flows. Ex-date receivable segregated, no unknown-pay-date spending.
Costs0,10,25bp/notional; spread0 baseline,5bp assumed sensitivity; taxesUNKNOWN.
Monthly A/B/C, static A/B separate common start after252warmup. C past252returns
bounds10–50%; sells before cash-constrained buys, fractional units, no leverage.
Report terminalNAV/CAGR/volatility/HWM/DD15breachcounts/durations/worst60loss,
turnover/fees/exposure/cash/missedupside per common period/subperiod. NON-EXECUTABLE
unless actual corporate-action/open alignment/settlement evidence qualified.
No Tbill or probability protective overlay, no 35/51/60trim simulation. Ladder known
BLOCKING defect fromPR22 must not be called or silently repaired.

Scope stop rule (Issue25): if phase1 gate fails, deliver phase0+phase1+gated minimal
calibration milestone, ledger NEXT_MILESTONE/BLOCKED, not simulated actual economics.
No real metrics from synthetic fixtures. Explicit DONE/BLOCKED/NOT DONE in report.
Only after separate review/data qualification continue ledger. No merge/deploy,
production/broker/orders/subscriptions/purchases or live shadow jobs.

Phase4 offline append-only records: actual UTCdecision, code/model/protocol/source
hashes, recipe/snapshot, label type, raw/calibratedP/CI nullable, quality/staleness;
separate full60matured labels/corrections+hashchain. Local synthetic mock only.
Prospective minimum12months monitoring for quality/coverage, not minimum efficacy
sample. Pilot block variance/rare-event arrival uncertainty -> blinded power/precision
length plan, may require years. No past history labelled independent holdout.
