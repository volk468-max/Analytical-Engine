# Risk Forecast daily v1 — technical_combined

Owner requests daily Risk Forecast for the same10stocks and10/30sessions as VOL.
Chosen existing estimator is technical_combined from frozen Risk Forecast v1,
source366f8cd00e8c228d4796d0abbe9997f717a3b6ad. Exact source is archived in reports/
risk-forecast-daily-v1/reference_risk_forecast.py.txt for formula/parity checks.

Not technical_plus_v3: no invented VIX/SOX/v3 score/state. Price-only binning of
prior20close-peak drawdown/RV20%/belowSMA50/WilderRSI14, exact Beta1/1 base and
shrinkage20 conditional frequency. Unit checks compare original ProbabilityBank.
Daily refit and30sessions/new EOD_CLOSE TOUCH target are explicitly new adapters,
not an assertion of identical original annual validation. Prespecified protocol.

Same universe order ANET NVDA AMD CRWD NBIS GOOG GS META MU LRCX.120series/day,
DOWN5/10/15%, Low/Close TOUCH, horizon10/30. NBIS onlysince2024-10-21. Training
support <252mature labels or <10globalclass examples blocks; rare conditional
cells retain numerical empirical backoff with explicit LOW_SUPPORT row reason.
No calibration/superiority claim, no trades. Calibrated probability remains NULL.

ALPHA_RISK_FORECAST_ENABLED=true enables an independent daily manifest; optional
ALPHA_RISK_FORECAST_PREFLIGHT_ONCE=true checks actual inputs on preclose manual
runs without publishing. Separate lock280007/idempotency RF_V1 avoids all legacy/
VOL records suppressing Risk Forecast. Additive migration007 only expands guarded
model allowlist; existing001–006/historical forecasts untouched.

Same research worker/source gates/paid EODHD/private TTLvault/actualissueUTC. All120
rows atomic, retries never append new model versions to an already recorded day.
First real issue only validNY20:30+ session window, never historical backfill.
Low support/blocked must not be shown as reliable direction or exact final return.
Read-only RF SQL audit uses committed role/identity setup before repeatable-read.
Original anchor/exact window resolver and weekly metrics handle the new model.
Rollback by disabling ALPHA_RISK_FORECAST_ENABLED, keeping immutable history/007.
