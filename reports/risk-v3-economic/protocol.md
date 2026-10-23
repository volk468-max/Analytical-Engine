# Frozen economic protocol v1

Written before executing economic results. Signal engine and its frozen historical
outputs are inputs, not candidates for optimization. Research only; no live orders.

## Signals and accounts

Use only PR #5 walk_forward variant C. Each annual profile must have training_end
before that year; 2026 is C/sensitive, selected through 2025. Never retune signals
or select recovery/size by 2026 profitability. Initial independent accounts have
$100,000; initial shares are bought at the first open including 5 bps commission
and 5 bps adverse slippage. Buy & Hold has exactly the same initial shares/costs.
Fractional shares in one provider split-adjusted unit basis; no leverage/shorts.
Minimum shares 50% and maximum original shares, not constant portfolio weights.

## Risk episodes

First observed REDUCE or CRITICAL is eligible after account inception; this is
labelled initial observation if already high-risk when the window starts. Within
an episode sell one tranche (10% original shares) at first REDUCE-or-higher; sell
one extra tranche at the first CRITICAL (including direct entry). A direct entry
to CRITICAL combines both tranches in one order. Once used, these permissions
stay exhausted through REDUCE/CRITICAL oscillations. Rearm a new episode only
after three consecutive valid WATCH/HOLD observations. A new high-risk observation
then permits another reduction, bounded by the share floor. Invalid data break
confirmation streaks and never rearm or authorize trades. Critical-disabled
control permits only the first tranche. Pending sell orders stay firm; pending
recovery orders are cancelled on a subsequent high-risk or invalid observation.
Only one pending order and one fill per session; unfilled last-day signals are
logged, not backfilled. Ignored signals (pending order, spent permissions, floor)
are retained. A pending-order conflict cannot cause a late duplicate sale.

## Recovery (no tuning)

HOLD3: three consecutive valid HOLD closes.
TREND3: three consecutive valid WATCH/HOLD closes, each above MA20 with positive
five-session MA20 slope.
TIME10: ten consecutive valid WATCH/HOLD sessions since last high-risk observation.
After confirmation restore one tranche per completed session, at the next
eligible open; stop at original shares or exhausted spendable cash. Commission
and adverse slippage cap affordable quantity. No additional capital is supplied.
Cash shortage leaves an explicit share deficit; it does not count as recovery.
New risk resets confirmation and cancels pending buys before their execution.

## Execution and prices

Primary costs 5 bps commission, 5 bps adverse slippage, at next session open
(delay=1). Sensitivity delays=2,3 (one/two additional sessions). No price-level
fills or same-close executions. Firm scheduled orders use only the last known
information. Source timestamps/publication gates and OHLC consistency must pass.
Primary datasets use one provider split-adjusted OHLC basis: DO NOT multiply
shares again on split dates. Dividend amounts must be reconciled to that same
basis against raw reported events. Gross dividend entitlements accrue on ex-date
for shares held before that session's open (pre-trade holdings). Because payment
dates are unavailable, accrued dividends remain non-spendable through account
end. Report them separately and include in total cash/equity. No taxes, interest,
stock lending, market impact, dividend reinvestment or terminal liquidation.
Price-only sensitivity omits dividends explicitly. Provider history is not a
verified original point-in-time or corporate-action archive.

## Periods and sensitivity

Full continuous test 2023-01-01 through 2026-10-22; independent fresh accounts for
2023–2024, 2025, 2026, September–October 2026. Also slice continuous equity over
these dates with inherited state, clearly separated from independent accounts.
All >=10% drawdown episodes use the unchanged PR #5 trailing-20-high event labels;
add actual recovery of that peak and censor unfinished observations.
Main size=10%; show all 5%,10%,15%,25% x recovery rules x critical on/off x delays
1,2,3 without choosing a winner. Development choice of these execution policies
is retrospective research, not untouched prospective validation.

## Economic labels (evaluation only)

For each actual reduction lot, retrospectively find the first closing trough
since sale: close <= previous close and close < next close, confirmed by that next
completed session. If no trough can be confirmed, use observed minimum only with
censored=true. Never feed this label to the policy. Report actual fill-to-trough
percentage loss and maximum avoidable dollars, plus the lot's actual net
contribution at the trough accounting for repurchases made before it. Positive
potential protection is not booked trading profit.

Match repurchases FIFO to reduction lots. Net completed contribution equals
quantity*(net sale proceeds/unit - all-in buy cost/unit) minus missed dividend
entitlements while absent. Open remaining quantities are marked at last close,
separately labelled unrealized. Their sum must reconcile to ending equity minus
Buy & Hold. Completed profitable-lot share excludes unfinished lots. Retain
per-lot and per-match dates, costs, shares, cash and deficits. October cycles
that are open on October 22 remain open.

False REDUCE labels use PR #5's unchanged 20-session growth/no additional 10%
closing decline definition; incomplete horizons remain null. Also report realized
loss rates and sold-before-growth separately, without conflating definitions.
Sharpe: daily total-equity returns, risk-free=0, sample standard deviation,
annualization sqrt(252); CAGR only for periods >=365 calendar days. Subperiod
initial mark is previous close for inherited accounts. No significance or
investment-effectiveness claims from retrospective sample profitability.
