# Numerical-resolution correction, 2026-11-05

Original protocol.md remains byte-identical. Before final publication/recalculation:
999 bootstrap repetitions with plus-one p-values have minimum p=.001; Holm across
162 comparisons cannot reject even the smallest possible p (.162). This is an
insufficient Monte Carlo resolution, not evidence against an ensemble.

Correct PRIMARY paired Brier contrasts only to9,999 synchronous bootstrap draws
for each length20/40/60, preserving seed, models, samples, thresholds, hypotheses,
loss functions, Holm family and every other criterion. Minimum attainable Holm p
is now.0162. Secondary contrasts keep999 draws; strata metrics399; agreement999.
Recompute all primary p-values/intervals and the same decision rule. Do not select
an ensemble or change any trading parameter. Record original min raw p=.006 and
initial0/162 only as diagnostic, not as final evidence. Publish this correction
before corrected computation. No positive effect claim can be made from reused data.
