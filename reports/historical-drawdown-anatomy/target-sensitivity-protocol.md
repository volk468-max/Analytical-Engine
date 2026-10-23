# Exploratory target sensitivity — frozen before this sensitivity calculation

Added after the first anchor-price primary results were observed (0/4 patterns
met the original criterion). It does NOT replace the original confirmatory
specification, change any hypothesis threshold or create an independent holdout.

Reason: a substantial rise after a presnapshot can precede a large peak-to-trough
fall while the eventual trough stays above the snapshot price. Consequently,
retrospective catalogue coverage and the original current-price loss target are
not equivalent. The requested anatomy question also warrants this distinction.

Supplemental target: during the next60 closes, start a running peak at the current
close, update with each future close, and record whether any subsequent close is
>=10% below that then-observed running peak. The future peak is only a target
label, NEVER a predictor. Full60-session publication is required before training,
even if the threshold is crossed early. Same annual cutoffs, ridge1 baselines,
H1/H2/H3/H5 definitions and universe. No tuning or winner selection.

Export all primary/expanded/stock comparisons of joint+each hypothesis versus the
same joint baseline, paired120-session blocks399 resamples. Holm across the four
PRIMARY sensitivity tests, explicitly exploratory. Compare with the anchor target
and report contrary results; a positive sensitivity result cannot upgrade a failed
primary result to confirmation. Original nested catalogue and control classes
remain unchanged. This label is a forward local path drawdown, not necessarily a
new lifetime-high-water episode. No live strategy or investment inference.
