# Risk Signal Engine v3 (research only)

This package imports offline backtest data types/features. Nothing in the running
Decision Engine or Tactical Risk Overlay imports this package. It emits explanatory
risk states, never allocation sizes or orders.

From the repository root:

```sh
python -m aae.research.risk_v3_study
python -m pytest tests/test_risk_signal_v3.py -q
```

The first command uses the checked-in, hash-verified source pack without network
access. Refreshing sources is a separate explicit operation:
`python scripts/fetch_risk_v3_data.py`. A refresh changes the dataset vintage and
requires regenerating all results. The study cutoff remains 22 October 2026.

`risk_signal_v3.evaluate` accepts only the documented causal indicator whitelist,
publication/observation metadata and an optional previous signal. Missing or stale
required observations yield no risk level; optional VIX/SOX gaps are disclosed.
See `reports/risk-signal-v3/report.md` for rules, selection objective, event labels,
walk-forward boundaries and limitations. Full signal payloads accompany the daily
CSV in compressed JSONL. Forward outcomes live only in evaluation outputs.

These retrospective provider responses are not an independently verified
point-in-time archive. The catalogue was specified for this research after the
historical period became observable; chronological evaluation is not a substitute
for prospective validation. No claim of investment effectiveness is supported.
