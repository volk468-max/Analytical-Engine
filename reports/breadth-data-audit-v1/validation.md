# Validation and reproducibility

Run from repository root (Python3.12, standard-library research code):
```
python -m research.breadth_data_audit.run
python -m pytest tests research/breadth_data_audit -q
```
pytest must be installed. In this task pytest9.2.0 is available under /tmp/alpha-audit-test-deps; test command used PYTHONPATH=/tmp/alpha-audit-test-deps. Existing project requirements already list pytest; production dependency files unchanged.

Actual fresh tests:30 passed,0 failed (28 new+2 main). One anyio PytestRemovedIn10Warning is environment/plugin deprecation, not a failed assertion. No JavaScript research code or JS test runner is introduced. Tests cover exact MA50/200 and equality, metric denominator and quality gates, IPO warmup, removal and future/late membership, absent universe, late and premature bar availability, before-close rejection, future-prefix invariance, causal split normalization and scale invariance, strict high/low warmup/ties, A/D undefined denominators, missing gaps, duplicate IDs/bars, rename-stable ID, unverified publication, mixed price basis, deterministic output and divergence composition changes.

Source prepared.json SHA256 d6a46d2ceede3be5bc0c58a667256225d1f445d73c7087dc93679ebc27cd5857 matched frozenPR11. Selected input encoded as prices.json.gz.b64: base64decode then gzipdecompress to JSON, no numerical rounding of input. UnusedOHLCVfields stay in immutable upstream source, not recreated. Compressed-byte format is to publish a lossless UTF8 artifact through GitHubContentsAPI. input-manifest.json records all5input SHA256s and is checked at each subsequent run. Output floats are deterministically rounded8decimals, source values not altered. run.json summarizes coverage, source.json records transformation, upstream-manifest.json retains original retrieval URLs/times/adjustments.

All daily output has explicit universe, members, availability decision time, data/model versions, per-metric counts/coverage and historical eligibility. No production reads through app endpoints were performed: ADCGET repository initializer executes DDL and commits. Railway MCP inventory/config metadata only, values of variables never requested; Redis/Postgres contents remainUNKNOWN. Safe infrastructure snapshot is not a backup or proof of market data retention.

No model fitting, threshold search, trading simulation, orders or existing-engine imports. minimum_coverage=1.0 is a declared data-quality gate. No full2010–2026PIT index study or StockCharts numerical validation was possible. These unavailable checks are explicitly NOT PASSED/NOT PERFORMED, not successful tests. No paid subscriptions, provider sales messages or deployment/merge actions.

Deterministic replay completed: breadth-prototype.csv, run.json, input-manifest.json and inputs/membership-proxies.json all reproduced byte-identically. Hashes and unavailable checks in verification.json. Raw fresh test output in test-results.txt.
