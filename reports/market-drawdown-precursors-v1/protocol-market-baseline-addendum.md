# Pure-market stock comparator clarification (before its evaluation)

2026-11-05. The original33 primary contrasts and model definitions remain fixed.
The original stock MINIMAL baseline contains own RV20 as well as market/sector
prices, so it is a market-conditioned, own-volatility-controlled comparator, not
strictly market-only. Issue19 also explicitly requires comparison to a pure-market
baseline. Do not relabel MINIMAL as market-only.

Add a SECONDARY prespecified comparison for STOCK TOUCH5/10 only: PLUS_X versus
MARKET_ONLY. MARKET_ONLY uses the MINIMAL shared QQQ/SPY/SOXX inputs, replacing
own logRV20 with QQQ logRV20. Same C=.1/train-only scaling/annual train-cal-test
windows/intercept calibration. Neither stock prices nor stock volatility enters
this baseline's features; its outcome is still the separate stock target. Models
are fitted per stock, not pooled with index labels. No new threshold/model search.

Freeze this clarification before fitting/evaluating this new comparator. Report
Brier/logloss/calibration/confusion and9999-draw date-block20/40/60 intervals.
Holm across these3 additional SECONDARY contrasts, kept separate from the original
33-way family; they cannot upgrade a core/deployment decision. This supplement
corrects completeness of the market-only distinction, not a response to predictive
results (none of the new comparator's outcomes have been computed).
