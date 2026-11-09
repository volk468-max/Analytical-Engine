# Preliminary continuation of Issue25 / existing Draft PR26

The owner explicitly authorized a separate preliminary study when complete data
qualification remains unavailable. Frozen v1 records and source prices remain
unchanged. Results are historical research replay, NOT certified PIT probabilities
or an executable strategy. See reports/eod-calibration-ledger-v2/protocol-supplement.md
(first continuation commit before new computations).

Dependencies (Python3.12): numpy2.3.5, pandas2.2.3, exchange-calendars4.11.2.

    python -m research.eod_calibration_ledger.preliminary
    python -m research.eod_calibration_ledger.continuity_v2
    python -m research.eod_calibration_ledger.verify_v2
    python -m unittest discover -s research/eod_calibration_ledger -v

Numerical replay uses only frozen PR24 local archives, verifies raw SHA256 and all
19320 original anchor labels/features/weights (actual count in run-manifest.json).
It performs no HTTP calls; verify_v2 additionally denies socket creation. Output
files live only in the separate v2 report directory. Intercept calibration is
fitted before each evaluation year using the original conservative temporal cuts;
rolling climatology cannot see an unmatured outcome. Calendar bootstrap retains
excluded session positions, synchronously across models and the three recipes.
Model intervals condition on the fitted models; annual fits are not re-estimated
inside each bootstrap. Effective support is HAC descriptive, not independent N.

Source audit: source-retrievals.json records two official source URLs, actual UTC
retrieval/status and raw response SHA256; structured verified facts are in
action-reconciliation.json. Full third-party pages are not redistributed here.
If original downloaded HTML bytes are available locally, reproduce the text checks:

    python -m research.eod_calibration_ledger.reconcile_v2 /path/to/raw-evidence

Expected filenames MU_ISSUER.html and MU_VIENNA.html; mismatched bytes fail closed.
Fresh retrieval may change page hashes; never overwrite original evidence metadata
or call a newly downloaded response the original historical vintage. The original
Unicode dash URL from the request was inaccessible in web lookup; the same official
issuer release was found at its canonical double-hyphen URL. No paid/denied source
was bypassed. Nasdaq original API bytes were already archived in v1 and hash checked.

Cash: unknown dividend payment dates stay permanently nonspendable receivables.
Only verified MU2024 record is transferred on the announced payment date. This is a
liquidity convention, not a claim about historical actual settlement. Split events
are audit memos; prices and dividends already use the provider normalized numeraire,
so applying another share multiplier would double count. Independent full-history
continuity still unverified. No ladder calls, probability trims, orders or live jobs.
