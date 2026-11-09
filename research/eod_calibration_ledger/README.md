# Issue25 first gated milestone
Stdlib Python3.12. Reuse frozen PR24 hashes; never refresh prices.
Offline reproduction (no requests):
 python research/eod_calibration_ledger/review.py
 python research/eod_calibration_ledger/calibration.py
 python -m unittest discover -s research/eod_calibration_ledger -v
Audit.py is a one-off independent source attempt, not routine refresh. Follow-up
responses stored; original URLs/retrieval times/body hashes in source-followups.json.
Actual data qualification failed; actual metrics NA. Code demonstrates a minimal
calibrator, not a completed empirical study or continuous ledger. No ledger outputs,
no probability policy/trades, no PR22 ladder calls. Read Russian report/stop rule.
