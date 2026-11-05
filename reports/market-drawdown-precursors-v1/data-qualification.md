# Historical data qualification (Stage1, before outcome comparisons)

Selected panel: **FRESH_YAHOO_ALL_SIX**. See data-inventory.csv for actual
coverage by input; acquisition-attempts.json records free2000 requests/errors.
Raw responses/actions, source URLs/retrieval times, normalized bars and XNYS4.11.2
calendar are frozen with SHA256 in data/manifest.json. No source stitching/filling.

All six price series passed structural OHLC/duplicate/calendar/end-coverage and
raw-normalization checks. Calendar timestamps include early closes and DST.
Source OHLC is provider split-normalized, adjclose excluded, splits not applied
twice. Corporate actions are provider reports, not independent reconciliation.
Historical original vintages/publication times and adjustment history are NOT
PIT-certified. Assumed next-midnight availability permits only conditional causal
reconstruction; it is not original release evidence. Fresh chart response alone
cannot qualify2000–2026 as a genuine PIT archive. Strict PIT-certified gate:FAIL.

Qualified scope is EXPLORATORY price-only retrospective analysis. Deployment or
validated predictive-core claim:NO-GO. Unqualified VIX/macroeconomic/breadth/
concentration/H4 inputs are STOP_NO_GO, not imputed. missing-factors.csv records all.
Data before the selected panel's actual earliest date is UNAVAILABLE, not zero.
A failed2000 request does not establish that the underlying history does not exist.

Known economic caveat: these are price-only ETF/stock labels; ex-dividend changes
are included, not dividend-adjusted total returns. Ratio invariance under a constant
split unit does not attest time-varying original provider corrections. Human source/
licensing review remains necessary; no paid provider/account/trial was activated.
