# Offline synthetic-only research / Issue21

Standard-library Python3.12; no providers, brokers or production imports.
Run from repository root:

    python research/portfolio_risk_probability/demo.py
    python -m unittest discover -s research/portfolio_risk_probability -v

Read protocol.md, architecture.md, portfolio-schema.json, factor-registry.json,
policy-config.json and Russian reports in reports/portfolio-risk-probability-v1.
Actual probability/CI and all real economic metrics are NA. demo.json is a
SYNTHETIC_NOT_USER_PORTFOLIO arithmetic fixture, not a fitted model. 35/51/60 are
experimental candidate thresholds. Full accounting backtest/real calibration are
blocked; policy and Ladder only test mechanisms independently, no combinations.
No live log collection or infrastructure started. CI must not claim prediction
validity from synthetic tests. Source research stays unmerged and unchanged.
