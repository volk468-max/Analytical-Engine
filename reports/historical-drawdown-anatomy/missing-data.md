# Missing historical evidence and possible acquisition sources

No current fundamentals or latest vendor estimates were backfilled into history.
Availability below means availability to this workspace, not a claim that no
commercial or public archive exists.

| Dataset | Workspace status | Possible original-history source | Required before use |
|---|---|---|---|
| Analyst EPS/revenue revisions | No timestamped historical estimate vintages | LSEG I/B/E/S, FactSet Estimates, Bloomberg BEst, S&P Capital IQ Estimates | Licensed point-in-time snapshots, analyst/publication time, fiscal-period mapping and revision lineage |
| Expected P/E | No historical forward-estimate denominator | Same estimate vendors plus consistent historical price history | Compute using only EPS vintage published by that date; never current forward EPS |
| Guidance changes | No parsed original guidance chronology | Original issuer IR releases and SEC EDGAR 8-K/10-Q/10-K exhibits, licensed transcript archives | Original publication timestamp, guidance period/range, corrections, first availability; distinguish reported facts from expectations |
| Earnings publications | No local original release/filing event archive | SEC EDGAR submissions/filings, issuer IR release archive, timestamped vendor calendars | Actual release/acceptance time (including after close), amendments and vintage; fiscal date is not publication date |
| Material corporate news | No historical timestamped news corpus | Issuer/EDGAR releases, Reuters/Dow Jones/Bloomberg archives | First-publication time, corrections, syndication duplicates and licensing; no retrospective summaries as earlier facts |
| Whole-market breadth | No original universe-wide historical advance/decline or constituent panel | Exchange breadth feeds, CRSP/Compustat/Datastream with inactive firms | Historical membership, delistings, corporate actions and session availability; current survivors are insufficient |
| Sector membership / survivorship-free universe | Fixed user-requested survivor basket only | CRSP/Compustat/Datastream or licensed index constituent histories | Time-varying sector membership, mergers/delistings, IPO dates and selection protocol |
| Independent OHLC/action vintages | Only frozen retrospective provider responses | Exchange-licensed adjusted/unadjusted archives, licensed action histories | Reconcile every split/dividend and source revision without applying splits twice |
| Original yield publication vintages | Retrospective FRED DGS10 obtained; assumed two-session lag | ALFRED vintages / Federal Reserve H.15 original release archives | Verify original release timing and revisions; assumed lag is not attestation |

The fixed 11-name semiconductor panel is a **sector-proxy sample**, not market-wide
breadth or historical sector membership. PLTR's September2020 IPO leaves early
long-window features unavailable; rows retain missing values. Primary prices,
QQQ/SOX and VIX come from prior frozen research; supplemental source manifests
retain retrieval times, raw responses/actions and checksums.

H4 is not tested. H5 is only a conditional retrospective market/yield experiment;
its source vintage and release-time limitations preclude historical attestation.
A future study should acquire these archives before testing new fundamental or
news hypotheses, freeze its feature extraction in advance and reserve genuinely
new calendar periods. None of this study's results authorizes live trading.
