# Data quality report

Data classification: archived research quotes; retrospective survivor-selected universe; no confirmed PIT index breadth. No external paid data downloaded.

| Universe | Sessions | Valid MA50 | Valid MA200 | Valid extrema | Eligible historical test |
|---|---:|---:|---:|---:|---:|
| FIXED_ELEVEN_CURRENT_SURVIVORS_PROXY | 1465 | 1416 | 1132 | 1026 | 0 |
| FIXED_SEVEN_SEMIS_PROXY | 1465 | 1465 | 1465 | 1465 | 0 |

There are2930 distinct universe/session rows, not2930 independently informative statistical observations. Fixed7 has full calculation warmup; fixed11 has PLTR and NBIS warmup/entry effects. A high current quote coverage does not imply valid MA200 or252prior-session extrema coverage. Unavailable metrics stayNULL, observed-subset percentages have separate names. NBIS resumption is inherited PR11 eligibility, not an invented IPO. No backfilled current index membership.

## Coverage gaps and gates

- 2010–2019: no qualified full market OHLCV or index membership acquired.2020 quotes are warmup only, not a claim of complete market history.
- 2021–2026: real archived quotes for a small chosen survivor panel, not full SP500/NDX/SOX constituents. IPO/delisting and bankrupt-company coverage not representative.
- Original publication/revision timestamps absent. nextUTCmidnight availability is assumed; historical_eligible=False even if numeric coverage100%.
- Stable provider IDs, complete corporate-action lineage and historical classifications not verified; proxy ID equals ticker. Existing provider split units are consistent for supplied arithmetic but not a certified corporate-actions archive. Dividend-adjusted reconciliation not done.
-2021–2026 sessions inherited fromPR11;2020 session dates from archived AMD observations, closes assumedNY16:00; exceptional early closes not certified. calendar_verified=False.
- No production storage row counts queried; service existence and configured names are not database content evidence. Redis is not treated as an immutable historical archive.
- StockCharts comparison NOT_PERFORMED: no authorized export, different universe and dividend adjustment. No numerical residuals invented.

## Preliminary descriptive event study

Not performed as a qualified index-breadth study: all rows fail historical eligibility. Plotting these survivor proxies around selected SOX/QQQ/SPY falls would not repair the universe bias or establish early-warning value. Prototype daily fields and benchmark20return permit later descriptive inspection, explicitly labelled proxy, but no correction thresholds, factor ranking, accuracy or predictive claims are produced.

## Provider qualification required

Get licensed date-specific members including removals, security master/rename history, full constituent daily OHLCV before2010 for warmup, corporate events, publication/processing timestamps and permitted archival retention. Verify session rules and missing bars; independently check authorized benchmark export using identical membership/price basis. Do not lower coverage threshold to declare incomplete data qualified.
