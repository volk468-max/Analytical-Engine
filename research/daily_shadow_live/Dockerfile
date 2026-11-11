FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
WORKDIR /app
COPY research/daily_shadow/requirements.txt research/daily_shadow/requirements.txt
COPY research/daily_shadow_v3/requirements.txt research/daily_shadow_v3/requirements.txt
COPY research/daily_shadow_live/requirements.txt research/daily_shadow_live/requirements.txt
RUN pip install --no-cache-dir -r research/daily_shadow_live/requirements.txt
COPY research/ research/
COPY reports/daily-shadow-postgres-v2/ reports/daily-shadow-postgres-v2/
COPY reports/market-drawdown-precursors-v1/data/ reports/market-drawdown-precursors-v1/data/
COPY reports/daily-shadow-live-v4/ reports/daily-shadow-live-v4/
CMD ["python", "-m", "research.daily_shadow_live.runtime"]
