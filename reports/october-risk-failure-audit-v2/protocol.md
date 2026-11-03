# October Risk Failure Audit v2 — frozen protocol
New independent audit; lost v1 conclusions are unverified hypotheses, not evidence.
Base main: a14ebf9c268bea5cb01de962edfb98b8df94652a. Requested window: 2026-09-01 through 2026-11-02.
Universe: AMD NVDA MU TSM AVGO AMAT AMZN META PLTR LRCX NBIS.

## Scope and evidence
Stage 1 only. No Risk Engine v3 development, fitting, production changes, orders, merge or deploy.
Separate original production payloads, saved research artifacts and retrospective calculations.
Missing records never mean HOLD. No inferred real positions/trades.
Persist each completed checkpoint directly to this branch before further work.
Runtime is currently offline: full calculations/tests require a usable execution environment.
No claim of restored original code/data or of original 203 tests being rerun.

## Prespecified descriptive hypotheses (before v2 calculation)
H1 sector: >=4 of fixed seven semiconductors AMD NVDA MU TSM AVGO AMAT LRCX have negative 5-session returns AND equal-weight mean 5-session return < QQQ 5-session return.
H2 broad: QQQ close < trailing MA20 AND 5-session return <0. QQQ is a proxy, not Nasdaq index.
H3 VIX: close >=25 OR 5-session change >=20%. Report each limb separately.
Check first new activation in October, first activation in full audit window, and conditions already active at window start separately.
Specific dates October8/14/16 are hypotheses, not hardcoded expected outputs.
H4 timing: compare warnings with stock closing drawdowns 5/10/15%; distinguish same-day close from executable next-session open.
H5 AUTO-support: inspect actual main code and prove or refute current-candle inclusion condition with minimal synthetic fixture; do not infer production inputs.

## Prices, episodes and availability
Use documented OHLCV/actions with warmup, strictly dated histories, no current/future candle in historical support.
Never mix adjusted and unadjusted price units. Splits/dividends need verified handling; missing actions limit economics.
Primary episodes: closing high over prior60 available sessions to full close recovery; nested declines merged. Report ongoing/left-censored episodes.
October-local view may use prior20 sessions at October1; label nested diagnostic, never pool as independent events.
Publication timestamps must gate decisions. Inferred timestamps/retrospective vintages are not verified point-in-time data.
No missing dates/prices/macros fabricated; missing periods remain explicit.

## Economic illustration, not optimized trading strategy
Per-stock independent $100000 portfolios, initial full stock position inclusive initial costs.
Compare Buy & Hold with fixed5% and10% of ORIGINAL shares sold once at new sector-warning activation while fully restored.
Signal after completed close; fill earliest next available session open, adverse5bp slippage and5bp fee per trade.
No same-day fills; sensitivity one additional session delay.
Restore sold shares after three consecutive sessions without sector-warning AND stock close above MA20;
one pending order, no repeated sales in unchanged state, no debt/shorts/external topups.
Buy capped by sold shares and cash including fees; residual share deficit and incomplete cycles reported.
No interest on cash. Do not drop last days or replace unavailable forward paths with zero outcomes.
False warning = no 5% fall from signal close in next10 sessions using subsequent daily lows; require full10-session horizon.
Also report terminal10-session return and upside hit separately; overlapping warnings are dependent.
All outcomes/cycle troughs retrospective labels only, never decision inputs.
No parameter optimization or best-strategy claim in this short diagnostic sample.

## Required deliverables
Russian executive summary; daily market/stock chronology; 11-stock drawdown table; historical-warning catalogue;
5%/10% model comparisons/trades/restoration; AUTO-support finding; sources/tests/limitations/manifest.
Unknown production history, absent markets and truncated economics must be prominently disclosed.
Stop after audit. Further research requires separate authorization.
