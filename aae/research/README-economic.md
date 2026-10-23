# Frozen v3 economic research

From repository root, install the optional plot dependency from
`aae/research/requirements-economic.txt` in a research environment if needed.
Run `python -m aae.research.risk_v3_economic_study` to regenerate all outputs
without network access. It verifies the existing PR #5 source/output hashes and
uses the frozen walk-forward C signals, never retraining them. Plot caches use
`/tmp/alpha-risk-economic-*` when no cache settings were supplied.

The execution-policy specification was committed before calculating results in
`reports/risk-v3-economic/protocol.md`. Main account performance, independently
reset subperiods and inherited continuous-account slices are explicitly labelled.
Buy & Hold starts with the same after-cost shares. Restored shares are cash-
limited and FIFO matched. The runner asserts that lot contributions exactly
reconcile final NAV minus Buy & Hold for all primary and sensitivity accounts.

`python -m pytest tests/test_risk_v3_economic.py -q` checks execution/state logic;
full repository tests remain applicable. The economic module is never imported
by production engines. Nothing here sends orders or recommends live position
weights. See the report and validation files for vintage/dividend limitations.
