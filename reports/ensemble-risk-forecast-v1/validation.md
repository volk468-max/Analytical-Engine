# Validation

Frozen protocol published before calculations:5ddbe68 (full SHA in registration).
All source input bytes checked against pinned Git objects;66,438 source task labels
and decision/maturity timestamps independently recomputed from archived bars.

Completed local checks:

- New ensemble suite:16 passed (causal meta/cal boundaries, independent label use,
  constant-class fit, same-date bootstrap weights/gaps, confusion denominators,
  protocol hash, Holm, consensus, probability/vote audits, ledger conservation,
  split categorical regime/probability fields).
- Unchanged PR17 validation suite:14 passed.
- Unchanged original PR7 forecast suite:27 passed after documented temporary
  environment path restoration; no code/test edits in source worktree.
- Knowledge regression suite:9 passed.

66 tests total. Synthetic fixtures validate code, not predictive power. Source audit
uses real frozen observations. See corrections.md for initial/resolved failures.
Byte reproduction and online knowledge validation results are recorded in
verification.json after final checks. No future GitHub CI success is asserted.

Final results:18 numerical artifacts reproduced byte-identically after the9,999-draw
primary correction. All66 tests passed; knowledge validator passed with live GitHub
and full PR17 base SHA; git diff --check passed. Full hashes in verification.json.
No untouched/PIT claim follows from successful software checks.
