# Validation

- Full pytest suite: **56 passed, 20 subtests passed** (29 new simulator tests plus 27 existing tests).
- No failing or skipped tests.
- Tests include publication-time gating, mutation of future candles, delayed opens,
  after-open publication, fees/slippage/affordability, repeated TRIM suppression,
  compound exposure floor, restoration, REVIEW interruption, pending terminal
  orders, opportunity cost, censored false signals, missing archives, full v1/v2
  archive replay on synthetic test-only inputs, nested future timestamp rejection,
  legacy source fidelity, missing-data exports and artifact checksum rejection.
- Python compilation and staged diff whitespace checks passed.
- Limited public-price run: 44 measured price replays, 44 explicitly unavailable
  full-strategy comparisons, 297 predeclared sensitivity variants.
- Strict audit on the public source pack: all 44 comparisons UNAVAILABLE as
  expected. Price-vintage and decision-archive provenance requirements are not met;
  these are missing research inputs, not failing unit tests. See strict-summary.csv.
- Report metrics are calculated only from downloaded market data. Synthetic data
  are confined to tests. No production calls, database access, deployments or merges.

Reproduce: `python -m pytest -q`, followed by the CLI commands in the documentation.
