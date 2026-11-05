# Methodology and scope clarifications

The full preregistered methodology is protocol.md, frozen before outcomes; the
additional pure-market stock comparator was separately preregistered BEFORE its
fitting/comparison. The original33-way primary family is unchanged. Its baseline
includes own RV20, so the extra comparator explicitly answers the stricter
market-only question using QQQ RV20 in place of own RV20. Separate3-way secondary
Holm is not a global exploratory multiplicity correction or independent validation.

All six instruments use one fresh/free frozen Yahoo snapshot, no vintage stitching.
Corporate actions and original response metadata retained; source overlaps match
frozen PR11 exactly. No independently certified original PIT data. Structural and
calendar qualification permits only exploratory price-only replay; unqualified
non-price/membership/fundamental families stop before inference. SOXX is an ETF
proxy with archived prices from2001-07-13, never backfilled or called breadth.
Provider firstTradeDate metadata is not an independently verified IPO/listing date.

Market closing episode catalogue and anchor-close future Low TOUCH labels are
separate concepts. Closing peak/onset/trough/recovery are target metadata only.
Pre-onset snapshots have only already-known price prefixes. Daily forecasts may
occur during ongoing declines; near-high causal filter is separately reported,
not falsely labelled guaranteed pre-onset. Matched controls are descriptive only;
probability models and population rates use all eligible dates.

Warmup252 and SOXX context restrict full feature history to2002+. Chronological
test2010–2026, calibration preceding year, training earlier still; fully matured
labels,20-session purges or60 for horizon60 at every boundary. Early barrier hits
do not mature incomplete labels. First/last source sessions never filled. Model
scaling/slope fits see training only, intercept calibration sees cal only, thresholds
.2/.5 fixed. No winner selection on tests or trading/economic simulation.

Brier/logloss/confusion/calibration intervals use calendar blocks and retain common
market dates across instruments. Primary33 contrasts use9999 draws and20/40/60
sensitivity; secondary999 (lengthmax40,h), metrics/prevalence399. HAC effectiveN
undefined with calendar gaps/zero variance; overlapping labels and episode clusters
never called independent observations. Reliability bins/ECE are descriptive;
calibration bias has block intervals. Bootstrap conditions on fitted models and
does not cover all fitting/design/vintage uncertainty. No crisis-specific advantage
claim from familiar/reused history. A core requires actual prospective evidence.

Publication: shell Git write authentication became unavailable after protocol
publication. Subsequent files are published with the connected GitHub Git-object
API; blob/tree SHA equality is checked against the locally tested content, branch
updates use expected-head leases without force. An initial oversized shell-output
read was capped; the mismatched blob was rejected before linking any tree. Chunked
base64 reads with exact-length and Git-blob SHA checks prevent silent truncation.
This affects transport only, not data/model selection or statistical results.
