# Fixed 5% Buyback Experiment v1 — protocol frozen before calculations
Base main a14ebf9c268bea5cb01de962edfb98b8df94652a.
Read-only audit source commit7135c2bdc0653986d93dfcfc66b202a6fb2f741e (Draft PR9).
This is a new research branch, not production or a reconstruction of real Alpha OS actions.

## Primary input / period
September1–November2 2026; 11 audit stocks,100000USD model portfolio, equal initial monetary sleeves1/11, no rebalancing.
Use exactly the published sector_flag activation rows from completion/warning-timeline.csv, which also drove PR9 economics.
Other QQQ/VIX warnings remain evidence, not additional sales; do not silently union different signals.
Signal close dates/thresholds unchanged; publication timestamps remain audit assumptions, not certified original PIT.
No interpretation of missing production records as HOLD. Full long-history experiment unavailable unless a complete corresponding historical signal sequence is documented.

## Sale / shares
One sale request per original sector activation per stock,5% or10% ORIGINAL initialized quantity.
Market sell at next verified regular-session open, adverse5bp slippage and5bp fee.
Delay sensitivity: one additional session. Do not substitute close; no fill without actual quote.
Cap request by currently held free shares minus already pending sale reservations; no short/debt.
Each filled sale creates a separate lot; its sold shares are absent from holdings and unavailable for another sale until bought back.
Other held shares may be sold on a new activation even while older lots remain open. No full-restoration gate.
One pending market sale, no repeated sale merely because a state remains unchanged.
Unfilled end-of-window requests remain unfilled, not fictional trades.

## Fixed-price buyback
Limit = actual executed sale price * (1-threshold); primary threshold exactly5%.
Buy exactly filled sale quantity, active from NEXT session after sale fill, GTC until fill or study end.
If open<=limit: buy at open; else if low<=limit: buy at limit; otherwise no buy.
Daily OHLC assumes complete fill on a touched limit, with no queue/volume evidence; explicitly hypothetical.
Each lot gets segregated net sale proceeds, no double spending; buy quantity capped by its cash including5bp buy commission, never external funds.
No RSI/MA/trend/risk improvement conditions. No terminal forced rebuy or profit reinvestment into extra shares.
Base limit buys have no price worse than limit: maker touch at limit, gap at open; sale retains5bp adverse slippage.
Stress variant requires5bp penetration for intraday touch, and worsens gap fill by5bp capped at the limit.
No same-bar sale+buy of new lot. At a bar open, execute previously scheduled sale first, then old gap-fill lots FIFO.
For old non-gap lots, touched limit fill later in that session. Actions determined only from data available by then.
Concurrent limit orders retain independent limits/cash/quantity and deterministic FIFO processing.
Dividend entitlement uses pre-open shares, accrued as nonspendable receivable since pay dates unavailable.
No splits in audit window; do not silently claim general split support.

## Comparisons
A Buy & Hold. B sale-only (both5% and10%). C fixed5% sale/5% price buyback. D fixed10% sale/5% price buyback.
E unchanged prior PR9 restoration results for both sizes and delays, with source/hash verification.
Report continuous September start only. No October reset for conclusions.
Initial purchase: same5bp fee/adverse5bp slippage for every strategy; net original quantity identical.
Each stock independent100000USD calculation is scaled1/11 into model portfolio; total initial100000USD.

## Labels / economics
For each sale: future-low fall from ACTUAL sale fill price over5/10/20 subsequent sessions (exclude sale bar for comparable prospective labels), full-window status, observed hit5 and latency.
Buyback eligibility starts sale+1; realized cycles, fees, slippage, cash surplus, dividends missed and residual mark-to-end reported separately.
Post-sale maximum rise until buy: for intraday limit-fill day, high-versus-low order unknown; report known-before-day maximum and inclusive possible upper bound, not an invented path.
Unfinished sale benefit = net proceeds minus market value of missing shares (and missed dividend entitlement reported separately), never gross proceeds as profit.
Primary false-sale diagnostic: no future-low hit5 within10 subsequent sessions; incomplete horizon censored, not false.
Also report positive terminal return and maximum runup separately; overlapping windows/stock dependence explicitly limited.
Do not use future label minima/maxima in signal/limit creation.
Exact original-share buyback cannot grow stock quantity above Buy & Hold; profits stay cash. No claim of more shares through unrequested reinvestment.

## Sensitivity / stop
Thresholds3%,7%,10% alongside frozen5%, both sale sizes,1/2session execution, base/stress fills. No best-parameter selection on October.
No production calls/changes, real orders, engine edits, deploy/merge or new Risk Engine development.
Publish raw inputs/provenance, code/tests, summaries, sales/orders/cycles/daily NAV/opportunity costs and Russian report. Stop after reviewable PR.
