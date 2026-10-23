# Historical Drawdown Anatomy v1

Install optional research dependencies from `requirements-anatomy.txt` if needed.
Run from repository root:

```sh
OPENBLAS_NUM_THREADS=1 python -m aae.research.drawdown_anatomy_study
python -m pytest tests/test_drawdown_anatomy.py -q
```

Offline regeneration verifies original and supplemental pack hashes, constructs
nested-free catalogues **before** feature associations, and then builds only
publication-gated features. The previous significant low is confirmed only after
five right-hand sessions have already become available. Peak/trough catalogue
metadata never enters probability predictors.

`drawdown_anatomy.py` separates the catalogue, causal features, fixed hypotheses
and future labels. `drawdown_anatomy_models.py` fits fixed-ridge baselines only to
fully matured outcomes at annual cutoffs, with training-only standardization.
The runner keeps deterministic retrospective controls separate from population
forecast denominators; reused controls are not independent trials.

Source refresh is an explicit separate network operation:
`python scripts/fetch_drawdown_anatomy_data.py`. It writes only the new supplement,
not prior frozen data. All conclusions remain conditional on retrospective
vintages and a survivor basket. Read protocol.md, missing-data.md and validation.md
under reports/historical-drawdown-anatomy/. The original signal engines are never
changed and nothing connects this package to production or real trades.

Supplementary daily probability audits are deterministic gzip CSVs
(forecast-daily.csv.gz and path-forecast-daily.csv.gz); required event/control
reports remain plain CSV. The path-target sensitivity was specified after the
first primary results and is exploratory, as its separate protocol records.
