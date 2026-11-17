# VOL daily v1 — owner universe / Issue33

Ten stocks in UI order: ANET NVDA AMD CRWD NBIS GOOG GS META MU LRCX.
Enable only in the existing authorised isolated worker with ALPHA_VOL_ENABLED=true.
ALPHA_VOL_PREFLIGHT_ONCE=true also checks real10-symbol access/history/fits on
pre-close deployment runs; it issues no historical forecasts. Set false after the
first reviewed preflight. Existing EODHD token/DB references stay in Railway.

Same cron0 2 * * 2-6 (05:00 Moscow Tue–Sat). Official exchange-session and New York
20:30 gates are unchanged. No forced forecast can be published during Moscow day.
Original HIST/REGIME six-symbol222-row manifest remains separate. New VOL120-row
manifest is10*2labels*3thresholds*2horizons10/30. On missing data/support a row is
BLOCKED with a reason; no artificial probability. Existing VOL records for a
session prevent reissuance under new versions. Partial batches are not refilled.
Atomic publication is one transaction; fit/model-registration precede SQL issued_at.

Estimator: raw logRV20 annualised daily-log-return volatility, ddof1; independent
L2 logistic C.1 with train-only standardisation. This is **daily-refit v1**, not
an assertion of equivalence to historical annual train/cal/test or calibrated VOL.
Warmup252 observations, >=252 fully mature training labels, >=10 of each class;
extra horizon anchor purge, no latest-day label. Current revised vendor archive is
TRAINING_REPLAY_NOT_PIT, model not validated, calibrated probability NULL. No
performance advantage or protection guarantee. No threshold/class support tuning.

NBIS starts2024-10-21. Official Nasdaq announcement:
https://ir.nasdaq.com/news-releases/news-release-details/nasdaq-resumes-trading-nebius-group-nv
No historical YNDX splice, zero-filling or bridging exchange-session gaps. Initial
NBIS tasks can be BLOCKED because warmup plus training support is insufficient.

Migration006 widens research horizon allowlist to30 and permits VOL on only this
manifest; all original SQL001–005 hashes, as-of/privacy/append-only guards remain.
Do not run migrations on production. New SQL audit reports numeric/blocked totals,
first/last actual issueUTC and duplicate logical rows; genuine forecast acceptance
requires120 rows (numeric or explicit blocked) for a new valid session. Synthetic
fixtures never count. Preflight/CI/deploy SUCCESS alone is not real issuance.

Matured outcomes use original licensed anchor and exact next10/30 session window,
with as-of split adjustment. A current adapter covers requested forecast symbols,
not only the original6. Weekly report preserves HIST/REGIME pairing if VOL exists;
VOL scores are separately shown by target. Same-date30-session HIST/REGIME
comparison is not available until separate baseline artifacts are prepared.

Rollback: set ALPHA_VOL_ENABLED=false (or re-pin old research SHA). Keep history and
additive006, do not downgrade/delete forecast journal. No broker/trading consumers.
