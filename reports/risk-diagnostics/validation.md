# Validation

Full suite: **77 passed, 20 subtests passed**, including 21 new diagnostics tests.
No failing or skipped tests in the final run.

Checks cover prior-only support/peaks, moving averages and RSI, mutation of future
prices, future VIX/QQQ publication, missing relative-strength observations,
severe-VIX and support-plus-stress branches, stale-input short circuit, separate
forward labels/censoring, threshold crossings at exact decimal boundaries,
episode deduplication/recovery, retention of MU's nested October excursion,
restoration after three actionable HOLDs, FIFO residual-share accounting and
reconciliation with PR #2's original metrics.

Downloaded-data integration checks confirm all 111 daily actions match PR #2,
all 9 recoveries reconcile its opportunity-cost diagnostic, and recorded hashes
of the unchanged Overlay and simulator still match. Source compilation, generated
artifact hash verification and staged Git whitespace checks passed.

Limitations remain those in report.md: retrospective provider vintages and assumed
publication times; no archived broad-market breadth or full-system regime. These
checks establish calculation/replay consistency, not investment effectiveness.
