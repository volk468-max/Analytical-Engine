# Historical SELL / BUY −5% v1 — prespecified protocol
Base main:a14ebf9c268bea5cb01de962edfb98b8df94652a.
Read-only PR9:7135c2bdc0653986d93dfcfc66b202a6fb2f741e; PR10:ef1a3a76c1c0d455f48a9d787f1c04961c244b91.
Publish before calculations; no production, merge, deploy, real orders or parameter fitting.

## Mandatory gate BEFORE the long test
Freeze PR10 source, inputs, calendars, signals and expected outputs with SHA256.
Regenerate sector flags on full warmup for the control interval2026-09-01..2026-11-02.
For stock close Ct: R5=Ct/Ct-5−1, using five previous TRADING rows and only data known through t.
Fixed seven:AMD,NVDA,MU,TSM,AVGO,AMAT,LRCX. Require all seven and QQQ R5.
sector_flag=(negative-count>=4) AND (equal-weight mean seven R5 < QQQ R5).
Only false/not-true → true transitions produce requests; retain previous warmup state, not reset at interval start.
SOX/SOXX/SMH/SPY/indices/VIX are context data, NOT additional inputs or sales.
Dates and PR10 control numerical outputs must match. On any mismatch STOP before running long economics; publish discrepancy.
No replacement with RiskSignalv3 or actual-production signals. Original production history remains UNKNOWN.

## Dates, corporate actions, signals
Requested2021-01-01..2026-11-02; first actual stock session2021-01-04. Fetch2020 warmup.
Preserve raw OHLCV/actions, provider/source/retrievalUTC/date/publication assumptions, adjustments and file hashes.
NYSE sessions/calendar/DST; no regular/prepost mixing. Price next-UTC-midnight availability remains explicit UNVERIFIED assumption.
Signals at completed session close, execution after availability at next actual regular open, delay sensitivity+1session.
Do not fill missing quotes, suspension history or unverified corporate identity with made-up data.
Provider split-adjusted OHLC and compatible dividend units may be used as one constant share-unit ledger;
ALSO report contemporaneous nominal shares/prices via documented split factors. No adjclose/dividend-adjusted price mixing.
Split-adjusted original target quantity and outstanding lot quantity/limit transform with splits; not an extra purchase or profit.
Test invariance to price/share split units and compare returns against nominal prices adjusted ONLY for splits already effective at each decision.
Gross dividend entitlement on ex-date, pre-open shares; unpaid/unknown-paydate distributions held as nonspendable receivable, no interest or reinvestment.
Current-provider prices/actions are not independently attested original PIT vintages. No verified live recommendations.

## Universe and model portfolios
Fixed current11 survivors:AMD,NVDA,MU,TSM,AVGO,AMAT,AMZN,META,PLTR,LRCX,NBIS. Explicit survivorship/selection bias, not historical neutral universe.
Variant1:11 equal INITIAL capital slots100000/11; buy each available asset on first valid eligible open.
Unavailable asset's slot remains cash0% until eligibility; no redistribution/rebalance/external topup.
This reserved-cash design is explicit: otherwise funding a late entrant after fully allocating to initial names would require prohibited rebalancing.
NBIS eligibility:first documented Nebius regular session after2024 resumption, supported by provider/issuer evidence; do NOT silently splice earlier suspended YNDX.
If eligibility cannot be verified keep its slot unavailable and disclose it.
Variant2:fixed comparable constituents actually trading at initial session;100000/N equal slots, no later additions.
Each standalone stock study100000 at first eligible open; portfolio aggregates by the original slot weights.
Ending shares reported per ticker in both constant and contemporaneous split units.

## Frozen trade rules
Reuse PR10 actual engine:5%/10% ORIGINAL quantity per sector activation; cap by currently held free shares.
Separate lots/segregated net proceeds; no reselling absent shares or double-spending; no full-restoration gate.
Sell next regular open at adverse5bp, fee5bp; no sell at signal close.
Buy limit=ACTUAL sale fill×.95, active next session after sale; gap open<=limit fills open, otherwise low<=limit fills limit.
Buy exactly sold quantity in consistent split units; all-or-none cash guard; no borrow/topup, RSI/MA/score/trend conditions or forced terminal rebuy.
FIFO old-lot handling, open sale before old gap buys; new lot never rebought same bar.
Surplus stays cash, no extra shares. No general corporate cash mergers/spinoffs silently assumed; disclose unverified actions.
A Buy&Hold; B sale-only both sizes; C5%+buy−5%; D10%+buy−5%.
Optional E only if unchanged semantics and complete inputs permit defensible reproduction; otherwise explicitly omitted, not approximated.
Unfinished proceeds not profit: end NAV includes marked missing-share effect, held shares, cash and receivable.

## Metrics and analysis
Main result continuous2021..2026, no annual resets of positions, cash, pending lots or orders.
Annual returns use prior-year ending NAV (first year initial capital), annual maxDD from within-year peak seeded by prior year-end.
Full maxDD from full running peak; daily close NAV; sample volatility std×sqrt252, Sharpe mean/std×sqrt252, risk-free0%.
CAGR uses actual calendar elapsed time; short-period annualization labelled.
Report average cash/NAV and fraction of days cash>0; receivable separate. Initial reserved cash explicit.
Signal quality future-low hit5 and max decline over5/10/20 subsequent full sessions from ACTUAL sale price;
sale-session low separate; incomplete labels censored, overlapping stocks/windows not independent.
Runup before buy-day and possible inclusive-high upper bound for intraday fills; no invented high/low order.
Completed realized savings separate from open missing-share marked benefit/missed dividends.

## Objective analysis-only regimes
QQQ MA200 and20-session return. BULL if close>MA200 andR20>0; BEAR if close<MA200 andR20<0; else SIDEWAYS.
UNKNOWN without warmup. Attribute daily return to PREVIOUS session's known regime. No effect on trading.
Conditional statistics are descriptive, not a portfolio that could selectively earn disconnected regime returns.

## Prespecified sensitivity / no ranking
Thresholds3/5/7/10%, sizes5/10%, market-sell delay1/2sessions, PR10 strict5bp penetration/gap-limit-capped stress.
Extra cost scenario fee10bp/slip10bp versus frozen5/5, both market sells and applicable gap/initial fills.
Do not choose best ex post or describe same repeatedly studied2021–2026 as untouched holdout.
Persist each phase, all requested CSVs, Russian summary, raw inputs/manifests/code/tests and clean GitHub reproduction.
Stop after research PR. No production-readiness or causal inference from censored completed-only winners.
