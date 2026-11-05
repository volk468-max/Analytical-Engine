# Risk Forecast v2 — Predictive Validation: frozen protocol

2026-11-05. Publish this file before executing reproduction or new statistical calculations. Research only. Existing PR7/8/11/12 outcomes have already been read: their years are reused history, NOT pristine independent test data. No final independent prospective holdout currently exists. No model innovation may be declared validated from this history. No PR13–16 price/membership data will be used as verified PIT evidence.

## Inputs and exact subject

Primary frozen source PR7 commit366f8cd00e8c228d4796d0abbe9997f717a3b6ad, inherited PR5 source packs. AMD/NVDA/MU; existing warmup2020, anchors2021 through2026-10-22. Actual coverage audited from files, not assumed earlier history. Forecast is available at the archived anchor bar's available_at (normally following00:00UTC; ASSUMPTION, not attested original publication). No current fundamentals/revisions/news used. Causal QQQ price-only regime is allowed only when archived available_at<=decision; it is not historical breadth or a fundamental regime.

For anchor close P_t on the single frozen provider split-adjusted OHLC basis, TOUCH_DOWN(d,h) = min(Low[t+1:t+h]) <= P_t*(1-d), d=.05/.10/.15, h=5/10/20 stock sessions. Anchor bar excluded. TERMINAL_DOWN(d,h) = Close[t+h] <= P_t*(1-d), a separate target. Inclusive comparisons with price-relative1e-12 tolerance as PR7. A label is usable only when ALL h sessions have published; early barrier hits never mature an unfinished window. Censor incomplete windows, don't replace missing rows. Forecast timestamp must precede first future open.

Reuse provider split-normalized units; do not apply splits twice or mix dividend-adjusted close with OHLC. Constant split-scale prefix checks are useful but do not prove original vintage accuracy. Record action events and adjustment limitations. No dividend total-return or economic portfolio conclusion follows from these price labels. Observations, reconstructed indicators/publication times, synthetic tests remain explicitly separated.

## Phase A: unchanged v1 reproduction first

Run the original module `aae.research.risk_forecast_study` inside an isolated checkout at PR7 SHA, without edits. Compare all original CSV outputs by hash, probabilities/labels and published metric counts; differences in figures/runtime metadata are disclosed, not silently fixed. Original180? No: use actual files; do not invent counts. Run original forecast tests. Preserve original remote research artifacts unchanged. This phase retains original annual fits and18 UP/DOWN primary tasks; it is distinct from Phase B.

## Phase B: prespecified stricter historical benchmark (exploratory)

Use unchanged ProbabilityBank parameters/bins/shrinkage20 and unmodified C evaluator. Fix the earliest original held-out C/sensitive profile for all periods (all recorded annual profiles must equal it, otherwise stop). Refit probability estimates only on permitted earlier rows. Primary forecast model=technical_plus_v3; technical_combined, v3_state and v3_score additionally reported, not selected after results.

For test year Y=2024/2025/2026:
- Training anchors start2021; cutoff January1 of Y-1. Require full label maturity <=cutoff and anchor at least20 common calendar sessions before cutoff (embargo). This purges future/overlapping labels.
- Calibration year Y-1: frozen training probabilities; first20 sessions embargoed. Calibration is an evaluation period only: no fitted mapping, threshold selection, tuning or refitting after viewing its outcomes. Require complete labels matured at least20 common sessions before test start when auditing eligible calibration; discard unfinished year-end windows.
- Test year Y: same frozen bank; first20 sessions embargoed after calibration/test boundary; labels completed by fixed source cutoff. Past test years may later become training as an ordinary walk-forward, never treated as untouched after prior research. Fit-audit records actual boundaries/maturity/max anchors. No random row splits.

Baselines fixed now, identical samples/labels per comparison: (1) original per-stock Beta(1,1) unconditional history; (2) unchanged PR7 RV20 bins/shrinkage; (3) QQQ regime probability, bins UP=QQQclose>=MA200 AND R20>0, DOWN=close<MA200 AND R20<=0, otherwise MIXED. Use known completed QQQ bars only. Regime empirical frequency shrinks20 to same unconditional probability; unavailable regime makes that forecast unavailable, never fabricated. Baseline choice is not altered after metrics.

## Metrics and inference

Each ticker x threshold x horizon x TOUCH/TERMINAL reported separately. No combined nine-task score. Metrics Brier, log loss (score clipping1e-6), ten fixed reliability bins, observed/predicted frequencies; precision/recall/FPR and false-discovery fraction at fixed p>=.5 and p>=.7. Recall of threshold hits is not recall before drawdown onset. Also export calendar-year and known QQQ regime strata, missing/censored counts and chronological examples.

Paired comparisons on exactly common observations. Synchronous circular calendar-block bootstrap keeps all stocks on same sampled date; length40 primary,20/60 sensitivity,1999 resamples, seed17031+h*100+round(d*1000), same draws for all contrasts. CIs95%; block count/effective-N diagnostics, not independent daily-window trials. Per-stock/stratum intervals exploratory and may be low power. Primary family27 comparisons =9 TOUCH tasks x3 baselines, pooled across stocks (each date kept together); Holm across these27. Terminal and other model contrasts secondary. No inference by counting overlapping hits as independent episodes.

Evidence criterion per TOUCH task: technical_plus_v3 improves Brier>=1% relative vs EACH prespecified baseline, paired interval upper<0, Holm p<.05, sign stable for block20/40/60 and all3 stocks and all3 test years, adequate positive/negative date blocks. Otherwise no supported incremental claim. Low power does not prove no effect. If criteria pass on reused history, still RESEARCH ONLY absent independently reserved data. GO requires independent data and PIT/robustness/economic evidence, not a synthetic test. NO-GO means no advantage established for this fixed estimator or material defect, not theorem of no conceivable signal.

## Phase C: separate economic diagnostics

No strategy optimization or portfolio backtest. Fixed p>=.5 for technical_plus_v3 TOUCH forecasts, each of9 tasks separate. Non-overlapping one-share-lot counterfactual per stock: sell1 original unit at next regular open (delay1; delay2 separate),5bp adverse slippage +5bp fee, restore at open h sessions after sale. Use only archived real opens, no fill if cutoff lacks required open. Buy quantity=min(1,net_sale_cash/(buy_open*(1+.0005)*(1+.0005))); no topups/debt, residual cash retained. Relative mark to retaining1 share at restoration open =cash+restored_qty*open-open. Warned lot is not resold while waiting. Price-only diagnostic; unknown dividend timing/tax/liquidity/PIT evidence disclosed. Not continuous portfolio wealth; unit scale and episode selection are not independent random trials. Export unit price opportunity cost, recovery above sale, missed/false warnings, delay/cost accounting. If no eligible executions, report unavailable, not success.

## Freeze and stop

All choices fixed before new calculations. Any code correction that changes results must be documented, not optimized. Never substitute synthetic observations for missing real data. Output conclusion has separate statistical/economic/PIT/independence qualifications. Publish a separate Draft PR plus append-only knowledge updates; no production/engine/signal changes, paid data, broker, trades, merge or deploy. Stop after Draft publication.
