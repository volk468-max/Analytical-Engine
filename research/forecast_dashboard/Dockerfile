FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
RUN pip install --no-cache-dir "psycopg[binary]>=3.2,<4"
COPY research/forecast_dashboard/ research/forecast_dashboard/
USER 65532:65532
EXPOSE 8080
CMD ["python","research/forecast_dashboard/server.py"]
