# Validation
13 new deterministic calibration/window/gate/hash-chain tests and9 knowledge
regression tests pass (22total). Frozen PR24 raw hashes verified, saved issuer
HTML and Nasdaq API evidence hashes checked by offline review script. Three
synthetic/status artifacts reproduce byte-identically; hashes in verification.json.
Initial whitespace check found CSV CRLF, writer corrected to LF and rerun; no
outcome/threshold changes. Initial online freshness check before the new commit
was not final validation; final check must use committed documentation.
No empirical calibration or ledger/economic validation performed. CI workflow
added; actual status queried on final published head, not assumed passing.
