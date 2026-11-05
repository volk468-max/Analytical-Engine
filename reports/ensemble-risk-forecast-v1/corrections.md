# Corrections and execution notes

No thresholds/models/criteria were changed after seeing ensemble outcomes.

- PR17 forecast CSV uses `regime` for the numeric regime probability; its original
  category was overwritten by that probability in the source writer. Initial new
  evaluation consequently had no UP/DOWN/MIXED strata. New code reconstructs a
  distinct `market_regime` from known QQQ bars, with exactly the source rule and
  availability gate. Recomputed all outputs; base probabilities/labels and pooled
  ensemble/economic conclusions are unchanged. Original PR17 is not rewritten.
  New regression test requires all three categorical regimes and numeric probability.
- Initial report rendering failed because those strata were absent; no incomplete
  report is published. A premature knowledge test run while report generation was
  pending reported missing report links; rerun after materialization passed9/9.
- Original PR7 suite has an absolute `/workspace/Analytical-Engine/aae/research/
  risk_v3_study.py` reference in old run metadata. It initially failed1/27 because
  the pinned worktree lives elsewhere. Every referenced source digest was verified,
  then a temporary environment-only symlink restored that single path.27/27 passed;
  symlink removed afterwards. No original test/model/run.json changed.
- New economic initial allocation is after first eligible test anchor, and signal
  processing starts with subsequent anchor observations, avoiding simultaneous
  inception buy/sell. This boundary clarification does not optimize results.

- Primary bootstrap resolution corrected999→9999 before final result per separately
  committed/published protocol-numerical-addendum.md. Plus-one p=.001 with999
  repetitions could not reject any hypothesis under Holm162. No estimator, warning
  threshold, family, sample or success rule changed.
