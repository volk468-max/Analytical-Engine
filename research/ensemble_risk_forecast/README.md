# Ensemble Risk Forecast v1 — isolated research

Frozen source: PR17@7fe91ab87dcda3607863a19074e6d7b2400503e8; underlying
PR7@366f8cd00e8c228d4796d0abbe9997f717a3b6ad. The new branch is intentionally
stacked on unmerged Draft PR17 for its forecast package and knowledge system.
No base research or production modules are modified.

Python3.12.14, numpy2.3.5, scipy1.17.0, scikit-learn1.8.0 (exact observed
runtime also recorded in source-manifest.json). Install research requirements
in an isolated environment if absent. No provider API or paid data required.

```bash
git worktree add --detach /path/to/source 366f8cd00e8c228d4796d0abbe9997f717a3b6ad
OPENBLAS_NUM_THREADS=1 python research/ensemble_risk_forecast/audit.py /path/to/source
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python research/ensemble_risk_forecast/study.py --source /path/to/source
OPENBLAS_NUM_THREADS=1 python research/ensemble_risk_forecast/supplement.py /path/to/source
OPENBLAS_NUM_THREADS=1 python research/ensemble_risk_forecast/report.py
OPENBLAS_NUM_THREADS=1 python -m unittest discover -s research/ensemble_risk_forecast -v
```

Audit checks every source input against its pinned Git object, validates66,438
labels directly from actual source OHLC and full maturity, and records hashes.
Runner checks immutable protocol hash. Outputs are ordinary CSV/gzip CSV, gzip
mtime0; no paths or runtime clock in numeric outputs. Reproduction compares bytes.
There are34,200 test task rows, not independent trials. Read Russian report,
protocol.md and validation.md before interpreting a number.

Source PR17 overwrote categorical `regime` with its numeric forecast probability.
New code preserves `regime` probability and reconstructs separate `market_regime`
from QQQ bars available at decision_at. This repairs metadata only: inherited
probabilities and labels remain unchanged. Source studies are never rewritten.

Economic account starts after first test anchor (initial matched-cost investment),
then processes subsequent eligible signals. All six policies/delay1/2 are fixed.
False-warning price-opportunity is signed descriptive closed-lot mark, not an
additive attribution of final wealth. Nonspendable dividend receivables are explicit.

Known inferential limits: reused history, proxy estimators, sparse patterns,
conditional bootstrap (no re-fitting), pointwise exploratory intervals outside
primary Holm family; de-overlap counts do not imply statistical independence.
