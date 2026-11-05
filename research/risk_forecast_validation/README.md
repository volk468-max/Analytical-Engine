# Reproduce the research

Use a separate research environment with numpy2.3.5, matplotlib3.10.8. pytest8.4.2
is needed only for the original tests. Do not change production requirements.

1. Clone source branch research/risk-forecast-v1 into an isolated directory;
   checkout366f8cd00e8c228d4796d0abbe9997f717a3b6ad. Do not merge it into this branch.
2. From that source root run OPENBLAS_NUM_THREADS=1 python -m aae.research.risk_forecast_study.
   Preserve original output hashes first if checking exact reproduction. run.json
   uses environment-specific paths; compare CSVs/source hashes separately.
3. In this branch run:

```sh
OPENBLAS_NUM_THREADS=1 python research/risk_forecast_validation/study.py --source /path/to/frozen/source
OPENBLAS_NUM_THREADS=1 python research/risk_forecast_validation/package_and_audit.py /path/to/frozen/source
OPENBLAS_NUM_THREADS=1 python -m unittest discover -s research/risk_forecast_validation -v
```

Source Git SHA, unchanged aae files, original source/output hashes and registered
protocol SHA are checked. Do not replace source input packs with PR13–16 data.
The runner writes only this new report directory. Original calculations occur
only inside the isolated source checkout; no source commits or remote results
are rewritten. Raw binary generated .gz is local/ignored; packaged wrapper
is .csv.gz.b64. Decode base64 then gzip to get all real calculated forecast rows.
Calendar audit used separate exchange_calendars4.11.2 XNYS reference (see table).
No paid data, endpoints, production database, broker or trading API is used.

The source v1 test suite has one legacy absolute manifest path: validation.md
records the environment-only byte-identical source symlink used for our run.
That accommodation must never point at modified source. Numerical reproduction
is not certification of original historical PIT data or a prospective holdout.

Optional pinned calendar audit: install exchange_calendars==4.11.2 in the research environment and run `python research/risk_forecast_validation/calendar_audit.py --source /path/to/frozen/source`.
