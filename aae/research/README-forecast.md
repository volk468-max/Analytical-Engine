# Risk Forecast v1 (research only)

Install the optional `aae/research/requirements-forecast.txt` in a research
execution environment. From repository root:

```sh
OPENBLAS_NUM_THREADS=1 python -m aae.research.risk_forecast_study
python -m pytest tests/test_risk_forecast.py -q
```

The runner reads hash-verified PR #5 data and signals inherited through PR #6.
It calls the unchanged C evaluator to replay each already-selected annual profile
on earlier archived causal indicators; held-out states/scores must match exactly.
2021–2022 rows are training/descriptive, not pseudo-held-out forecasts. Jan1
annual probability fits purge every horizon not fully published by the cutoff.
No trades, economic backtests, REDUCE changes or production imports are added.

`risk_forecast.py` separates immutable causal features from barrier labels and
freezes fitted probability banks. `risk_forecast_statistics.py` implements tied-
score ROC/AP, synchronous time-block resampling, paired losses and Holm tests.
LOW_SUPPORT values are not reliable individual live probabilities. Effective N,
block counts and uncertainty matter more than decimal precision.

The pre-results protocol and all reported assumptions are in
`reports/risk-forecast-v1/protocol.md`. The report states whether the predeclared
incremental-information criterion is met. Data are retrospective vintages, not
an independently attested point-in-time archive. A prospective holdout is needed.
