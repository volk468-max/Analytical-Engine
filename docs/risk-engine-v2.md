# Tactical Risk Overlay v1

Decision Engine previously took the minimum/maximum of the last 120 rows including
its current candle. A new low therefore moved support down with the price. It also
reported freshness without blocking ADD/TRIM/SELL. Strategy Engine could still
recommend accumulation under tactical stress. The two original tests cover only
MarketState/Risk and Hypothesis/Scenario, not these paths.

The overlay is independent of fundamental scores, revisions and the long-term
thesis. It is advisory; no order execution is added. Decision Engine returns the
separate `tactical_risk` report, and Strategy Engine propagates its REVIEW/TRIM to
short/medium horizons while keeping the long-term thesis separately assessed.
Legacy fundamental/technical rules remain; tactical HOLD does not override a
legacy TRIM/SELL. Existing thesis-review conditions also remain in force.

| Condition with verified inputs | Overlay recommendation |
| --- | --- |
| No risk condition | HOLD |
| Support break beyond buffer, or elevated VIX, or defensive fresh regime | REVIEW |
| Support break plus elevated VIX or defensive fresh regime | TRIM |
| Severe VIX | TRIM |
| Missing/invalid/stale/future observations or unavailable levels | REVIEW, actionable=false |

A blocked recommendation forces Decision Engine REVIEW with multiplier 1 and
unchanged target weight. HOLD means absence of a reduction rule, not a guarantee
of safety. REVIEW is not an order. TRIM is a suggested reduction of the current
position, not a percentage-point portfolio reduction.

## Configuration

Pass a validated `TacticalRiskConfig` to DecisionEngine/MarketRegimeEngine or set
these environment variables. No runtime infrastructure variables are changed by
this patch. Invalid configuration raises an error rather than silently defaulting.

| Environment variable | Default | Meaning |
| --- | --- | --- |
| ALPHA_RISK_SUPPORT_LOOKBACK | 120 | Required prior valid OHLC candles |
| ALPHA_RISK_SUPPORT_BREAK_BUFFER_PCT | 1 | Strict break below support minus buffer |
| ALPHA_RISK_STRESS_VIX | 25 | Elevated volatility threshold (inclusive) |
| ALPHA_RISK_SEVERE_VIX | 30 | Severe volatility threshold (inclusive) |
| ALPHA_RISK_TRIM_FRACTION | 0.25 | Fraction of current exposure suggested for reduction |
| ALPHA_RISK_MAX_QUOTE_AGE_HOURS | 96 | Maximum observed quote age |
| ALPHA_RISK_MAX_MARKET_AGE_HOURS | 36 | Maximum observed market/regime age |

These are explicit illustrative policy defaults, not fitted thresholds or an
assertion of effectiveness. Existing Market Regime classification rules and
legacy Decision Engine thresholds are otherwise unchanged.

## Time and data contract

TechnicalAnalysisEngine emits `price_as_of` from the row supplying current price
and accepts `as_of` for deterministic evaluation. Future rows are filtered before
technical indicators are computed. Decision Engine requires that timestamp; it
never infers it from the time of a separate history request. Historical levels use
only rows strictly earlier than that timestamp, with finite positive low/high,
ordered by parsed UTC time. Insufficient history or duplicate dates produce no
automatic levels, rather than substituting current price. Manual levels remain
supported; operators are responsible for recording them before evaluation, not
retrospectively choosing them.

Quote freshness is based on its observation timestamp. Market freshness requires
`trade_date` or `snapshot_time`; collection `created_at` alone is insufficient.
The Data Freshness Engine now checks observation age and rejects negative age.
Market Regime Engine returns UNKNOWN when constituent histories are stale or
insufficient; stale serialized regime reports cannot confirm a tactical break.
The policy assumes ISO timestamps/daily history, with naive timestamps interpreted
as UTC. Date-only values mean UTC midnight. The 96-hour quote allowance covers a
normal weekend; there is no exchange/holiday/session calendar. Long closures can
require manual review. Market summaries without observation dates will now block
trading until their producer supplies trustworthy metadata.

For historical evaluation, supply an as-of technical snapshot and point-in-time
market, regime, fundamentals and revisions. Filtering candle history alone does
not make today's fundamentals/revisions suitable for a historical backtest.
Daily bar completion times, splits, provider errors, missing portfolio members,
transaction costs, slippage and execution sizing are not solved here. Broad
portfolio history availability is still limited to inputs supplied by the caller.

## Validation

Offline synthetic unit tests verify policy behavior, time boundaries and causal
levels. No production endpoints or databases are used. These are regression tests,
not a historical performance test. Effectiveness remains unproven until a
point-in-time walk-forward backtest without future information is performed.
