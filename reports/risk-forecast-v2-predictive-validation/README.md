# Risk Forecast v2 — Predictive Validation

Начать с [русского отчёта](executive-summary-ru.md). [Протокол](protocol.md) опубликован до вычислений; [методика](methodology.md), [данные](data-audit.md), [ограничения](error-and-power-analysis.md), [проверки](validation.md).

Важные артефакты: metrics.csv (504ticker/target/task/model rows), baseline-comparison.csv (216paired contrasts, из них27primary), reliability.csv/calibration-curves.svg, alerts.csv, stability.csv, calibration-period.csv, fit-audit.csv, data/feature/calendar audits, separate economic-lots/economic-summary, error examples. Все targets/tickers/horizons сохраняются отдельно. forecast-daily.csv.gz.b64 — base64→gzip→CSV,66438rows включая calibration. Не считать rows независимыми.

Здесь нет новой оптимизированной торговой модели. PhaseA exact v1 воспроизведение; PhaseB refit unchanged estimator на строго определённых старых train/cal/test splits; PhaseC отдельный unit-lot economic diagnostic. Общая классификация RESEARCH ONLY, текущий estimator не подтвердил incremental advantage. Реальная независимая/PIT инвестиционная эффективность не установлена.
