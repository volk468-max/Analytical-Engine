# EOD model portfolios
Separate adapter; never invokes PR22 intraday/ladder functions.
Dependencies: numpy2.3.5,pandas2.2.3,exchange-calendars4.11.2.
From repository root: OPENBLAS_NUM_THREADS=1 python research/model_portfolios_eod/study.py
Tests: python -m unittest discover -s research/model_portfolios_eod -v
--acquire was one-off preregistered retrieval; do not refresh frozen snapshots.
Read protocol/qualification/Russian report. Not a continuous account or actual portfolio.
