# Issue19 — market drawdown precursors (isolated research)

Read reports/market-drawdown-precursors-v1/protocol.md, its preregistration and
market-only addendum, data-qualification.md and Russian executive summary first.
Primary prediction: future Low at least5% below current Close in next10 sessions.
MARKET SPY/QQQ/SOXX and STOCK AMD/NVDA/MU labels are never pooled. No trading or
production imports. The branch is intentionally stacked on unmerged Draft PR18
for append-only knowledge continuity; no prerequisite PR is treated as deployed.

Python3.12.14; exact research dependencies in requirements.txt. Use an isolated
venv if needed. Every computation below uses the included frozen source snapshot.
No provider request is required for reproduction and no paid provider is used.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python research/market_drawdown_precursors/study.py
OPENBLAS_NUM_THREADS=1 python research/market_drawdown_precursors/market_only.py
OPENBLAS_NUM_THREADS=1 python research/market_drawdown_precursors/audit_diagnostics.py
OPENBLAS_NUM_THREADS=1 python research/market_drawdown_precursors/verify_forecasts.py
OPENBLAS_NUM_THREADS=1 python research/market_drawdown_precursors/report.py
OPENBLAS_NUM_THREADS=1 python -m unittest discover -s research/market_drawdown_precursors -v
```

All output gzip streams use mtime0, numerical rows are deterministic. No current
runtime paths/timestamps in forecast outputs. Main annual fitting/inference takes
several minutes on one CPU. Forecasts are separated into six gzipCSV files;
metrics/reliability/weights are also gzipCSV. Required predictive-evaluation.csv,
market catalogue/controls/prevalence tables remain plain CSV. The same-date
bootstrap samples an entire wide panel of contrasts; it never IID-resamples
individual stock-days.9999 primary draws allow33-way Holm resolution; secondary
contrasts999, metrics/prevalence399. No bootstrap refitting, so conditional CIs.

Optional Stage1 audit reproduction (no new provider requests): fetch source PR11
commit if your shallow checkout lacks it, then run `data_audit.py --offline`.
The audit verifies the archived PR11 overlap using Git objects; it never selects a
price snapshot by outcomes. **Do not rerun acquisition against fresh Yahoo data
and overwrite this dataset.** A new dataset requires a new version/addendum.
The original one-off acquisition was preregistered and all URLs/timestamps/raw
responses/checksums are retained in data/manifest.json.

Strict original PIT certification failed. Prices pass only structural/calendar/
causal reconstruction audit; no imputed VIX/macro/breadth/H4 revisions. Tests
use labelled synthetic fixtures solely to verify causality, not predictive power.
Existing PR8/17/18 sources/results/cards are preserved. Prospective shadow-log
specification is not running infrastructure; Windows/Norgate acquisition postponed.
