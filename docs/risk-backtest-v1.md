# Risk backtest v1: scope, contract and reproduction

This is an offline research tool, not an API endpoint, trading system or production
migration. It starts from PR #1 (`b380096`) and does not merge it. The exact original
Decision Engine from main commit `a14ebf9c268bea5cb01de962edfb98b8df94652a`
is preserved in `aae/backtest/legacy_decision_engine.py` (Git blob
`26721ae07a6ae2d60d1c771754981e714b479624`). Its original current-candle level
behavior is intentionally retained for a faithful v1 replay. A test checks the blob.

## What data were actually obtained

The repository contains no historical prices, VIX, fundamentals or revisions.
Its ADC connector exposes latest fundamentals, latest revisions, latest market
summary and a bounded price history, with no as-of/vintage query. ADC_BASE_URL is
not configured in this environment. No production endpoint, Railway setting or
PostgreSQL table was queried or changed.

Public Yahoo daily chart responses were obtained for AMD, NVDA, MU, TSM, AVGO,
AMAT, AMZN, META, PLTR, LRCX and NBIS, and CBOE's daily VIX CSV was obtained.
Source URLs, retrieval time, response hashes, row counts, corporate-action metadata
and normalized artifact hashes are in `data/backtest/manifest.json`. Normalized
prices are committed as CSV; VIX as JSON. No synthetic prices are in research
results. Synthetic inputs occur only in unit tests.

Yahoo's last 23 October 2026 candle was still incomplete at retrieval and is
excluded. The obtained complete histories end on 22 October. Ten symbols have
955 bars from 3 January 2023 (including support warm-up); NBIS has 503 from
21 October 2024, so no January–October 2024 NBIS performance is claimed. The
extended table shows each account's actual start. Ticker aliases, NBIS corporate
reorganization and survivorship/selection effects require independent review.

These are retrospective price vintages, not a historical publication archive.
Yahoo OHLC can be split-adjusted to retrieval vintage. There is no trustworthy
nominal-price corporate-action ledger or dividend cash-flow processing here.
VIX daily closes are attributed conservatively to 20:15 UTC and availability at
next UTC midnight; stock bar closes are attributed to open+6.5 hours and availability
at next UTC midnight. Early closes are therefore delayed rather than anticipated.
Actual publication/receipt times are not known. All fetched rows are explicitly
`verified=false` and cannot pass strict mode. Reported research returns are
provider-price path returns after modeled costs, not verified total returns.

## Three-way comparison and deliberately missing results

`alpha_v1` is exact legacy code; `risk_v2` is the PR #1 Decision Engine. Both need
point-in-time fundamental scores, revisions, risk/technical inputs, freshness,
market summary and optional market-regime/thesis inputs. None of these archives
were available, so every full-strategy metric is UNAVAILABLE, not zero or a
fabricated reconstruction. No present-day fundamentals are backfilled into the past.

`risk_overlay_only` is separately labeled and uses historical price support and
VIX only; no fabricated market breadth/regime or fundamental forecast is supplied.
It is compared with `buy_hold` only in explicit assumed-availability research mode.
This is an operational rule replay and does not validate Alpha OS performance.
An unchanged overlay and Buy & Hold result means that the configured reduction
rules did not fire, not that the rules are correct or efficient.

## Run

```bash
# Optional public downloads (read-only network); updates local research files only.
python scripts/fetch_backtest_prices.py
# Reproduce committed limited replay and entire predeclared sensitivity grid.
python -m aae.backtest.cli --allow-assumed-availability --extended --sensitivity
# Audit strict mode: current public data deliberately produce UNAVAILABLE rows.
python -m aae.backtest.cli --output /tmp/alpha-strict-backtest
# Strict replay when externally verified bars and archives have been supplied.
python -m aae.backtest.cli --data /path/to/verified-data --snapshots /path/to/archives.json --output /tmp/verified-results
python -m pytest -q
```

CLI uses fixed `TacticalRiskConfig()` defaults, independent of environment overrides,
and records risk/execution settings in run.json. The Python API accepts validated
`ExecutionConfig` and `TacticalRiskConfig` for cost/latency/policy experiments.

Outputs: report.md, summary.csv (return/drawdown/false signals/recovery cost),
signals.csv (every HOLD/REVIEW/TRIM and decision timestamp), trades.csv (execution
and before/after weights), equity.csv (cash, shares and daily weights), coverage.csv,
sensitivity.csv (all 297 variants), run.json. Missing comparisons retain blank
numeric cells. Prices/observations without enough history produce REVIEW; no
support is invented. Signals before study start are not traded; history warms up
levels only. All strategies start fully invested on their first study open.

## Strict input schema and clock semantics

`bars.csv` columns: symbol, open_at, close_at, available_at, open, high, low, close,
source, verified, price_basis. ISO timestamps must carry timezones. Strict CSV
inputs must declare `verified=true` and `price_basis=nominal_unadjusted`. Declaring
these values is a producer attestation, not independent verification by this tool.
Bars must have unique opens, valid OHLC, ordered publication times and no overlap.
A verified input pack must additionally attest absence of unhandled splits and
other position-changing corporate actions within the replay window; until the
simulator supports a nominal-price corporate-action ledger, use action-free windows.

`markets.json` is a list of observations with observed_at, available_at, value
(e.g. {"vix": 20}), source and verified. The simulator selects the latest observed
vintage that has actually been published by the decision time. Revised values
published later cannot overwrite earlier signals. Bar history is similarly gated
by both close_at and available_at. Market freshness uses observation time, not
receipt time. No same-close trade execution is permitted.

`snapshots.json` is a list of the same observation envelopes; each value has:

- `snapshot`: the historical Decision Engine snapshot, including symbol,
  fundamental, technical, risk, revisions, market and data_freshness. Technical
  current_price and price_as_of must match the decision candle exactly.
- `market_regime` and `long_term_thesis`: optional historical inputs, never today's.
- `point_in_time_attested: true`: producer attests every component and score uses
  only information published by this envelope's available_at. This includes EPS
  revision vintages, restatements, lagged filings, regime constituent histories and
  human-authored theses. Unknown vintages must not be marked verified.

Missing or mismatched archives abort that symbol/strategy result rather than
silently approximating it. An exact Decision Engine replay alone does not reproduce
all original live services, portfolio management decisions or discretionary trades.
The same explicit execution/restoration policy is applied to both code versions.

## Execution and measurement policy

Defaults: each symbol has independent $10,000 capital, fractional shares,
commission 5 bps per side, adverse slippage 5 bps per side, no leverage, no interest,
no tax, no terminal liquidation. Initial buy uses first study open. A target formed
after publication fills at the first later observed session open (or Nth later open
when delay_sessions > 1), with gap-aware execution prices and affordability caps.
Costs can slightly shift realized weight from requested weight. No short exposure
or borrowing is permitted. There is no simulated volume/market impact constraint.

TRIM defaults to once per episode, so repeated daily stress signals do not sell
geometrically to zero. Explicit compound mode enforces a minimum weight. Three
consecutive actionable HOLDs queue full restoration; REVIEW or other risk actions
break this sequence, and new non-HOLD signals cancel queued restoration. Unverified
inputs cancel queued discretionary orders. Last-day orders remain pending, and
portfolio value marks remaining shares at the final completed close.

Max drawdown includes initial capital and daily closes; it is not intraday risk.
A false signal is an executed sell with a higher close five sessions after execution;
sells without a full horizon are censored. This descriptive forward outcome is used
ONLY in reporting, never in a trading decision. Missed recovery dollars sum positive
appreciation on sold FIFO units until their actual repurchase or terminal mark,
gross of costs, with unrepurchased units marked at terminal close. It is an
opportunity-cost diagnostic, not a claimed causal loss or the full difference from
Buy & Hold. Dates, actions, holdings and executions can be joined through the CSVs.

The sensitivity grid is fixed in advance: stress VIX 20/25/30, severe=stress+5,
support 60/120/200, trim 10/25/50%. Every variant is retained, with no parameter
winner chosen. The short September–October window is not used to tune a selected
configuration. Exploring 2024–2026 is not an independent holdout; future calibration
must reserve an untouched, prospectively specified validation window.

## Required before a full historical study

Verified point-in-time price/VIX vintages with actual receipt/publication times;
a corporate-action/split/dividend ledger and exchange session calendar; archived
fundamentals/revisions/derived scores and their publication times; archived regime
constituents and long-term thesis inputs; a historical investable universe; and a
separate validation design. Refresh complete 23 October bars only after publication.
Broker/execution validation, turnover constraints and portfolio-level cash/rebalancing
are outside this independent-stock v1 simulator.
