# Validation and reproducibility

Commands from repository root:
```
python -m research.signal_predictive_accuracy.completion
python -m research.signal_predictive_accuracy.completion_report
PYTHONPATH=/tmp/alpha-audit-test-deps python -m pytest tests research/signal_predictive_accuracy -q
```

Fresh test run: 43 passed, 0 failed; one environment anyio PytestRemovedIn10Warning. pytest9.2.0 installed in temporary dependency directory; not a repository dependency change. This comprises the prior37 plus6 new tests, all rerun, not claimed from old runs. Frozen-source load validates SHA256 hashes, 1465 daily states and134activation dates; no new signal indicators. New tests enforce full-window censoring, same-bar unresolved, execution-session counting, pre-onset exclusion/boundaries, and resolved denominator.

Original first-audit files remain unchanged. Supplement uses strict UNRESOLVED for all incomplete windows, even when an early event already decided the logical outcome. In original files, UNKNOWN is distinct and partial outcomes may be known; these definitions are not mixed. Time-to-extreme fields require complete windows, first tied date chosen deterministically. Nonwarning control includes active-state days without new activation. Control matching uses only contemporaneous eligibility and recorded price regime; future labels never choose a control. Empty matching cells omitted and counted. Matching by quarter is retrospective and not a deployable online probability model.

Circular calendar-block bootstrap shares calendar resampling across all symbols; within-date equities are averaged before resampling. Confidence intervals here are exploratory pointwise,499reps; no significance claim based on multiple threshold scans. Parent audit contains longer1999rep bootstrap and20/120block sensitivity for its different primary competing-barrier targets. Do not substitute those CIs for supplement touch probabilities.

Corporate actions and publication-vintage limitations from ../inputs/provenance.json and parent validation.md remain. No new feed, production query, data backfill, prices, model weights or trading operations introduced. Price-only labels, not dividend-inclusive investor returns. No private production payload obtained; missing evidence UNKNOWN, not HOLD. Non-nested peak-to-recovery episodes may span years; annual missed-event counts assign threshold year, not imply independently discovered yearly episodes. Pre-onset recall and pre-threshold recall are separate; no F1 combining them with competing-barrier accuracy.
