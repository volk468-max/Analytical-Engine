-- Read-only operator reports; synthetic/backfilled rows are excluded from prospective metrics.
SELECT r.mode,f.session_date,f.status,count(*) AS records
FROM alpha_shadow_v1.forecast_records f JOIN alpha_shadow_v1.forecast_runs r ON r.id=f.run_id
GROUP BY r.mode,f.session_date,f.status ORDER BY f.session_date;
SELECT f.session_date,f.symbol,e.body->>'reason' AS diagnostic,
 extract(epoch FROM (e.recorded_at-f.issued_at)) AS recording_delay_seconds,
 extract(epoch FROM (f.issued_at-v.ingestion_at)) AS ingestion_to_issue_seconds
FROM alpha_shadow_v1.forecast_records f JOIN alpha_shadow_v1.audit_events e ON e.id=f.id
JOIN alpha_shadow_v1.source_vintages v ON v.id=f.vintage_id;
-- Latest explicit label only; original and all previous label attempts remain immutable.
SELECT DISTINCT ON (o.forecast_id) o.*,e.recorded_at
FROM alpha_shadow_v1.outcome_records o JOIN alpha_shadow_v1.audit_events e ON e.id=o.id
ORDER BY o.forecast_id,e.seq DESC;
SELECT status,count(*) FROM alpha_shadow_v1.job_health GROUP BY status;
-- Original probabilities by immutable target/model-version (NULL is retained).
SELECT f.session_date,f.symbol,f.label_type,f.threshold_pct,f.horizon,
 m.model_name,m.version,f.status,f.probability_raw,f.probability_calibrated
FROM alpha_shadow_v1.forecast_records f JOIN alpha_shadow_v1.model_registry m ON m.id=f.model_id
ORDER BY f.session_date,m.model_name,m.version,f.symbol;
-- Maturity backlog: incomplete outcomes, and overdue versus still-future horizons.
WITH latest AS (
 SELECT DISTINCT ON (o.forecast_id) o.forecast_id,o.status
 FROM alpha_shadow_v1.outcome_records o JOIN alpha_shadow_v1.audit_events e ON e.id=o.id
 ORDER BY o.forecast_id,e.seq DESC
)
SELECT r.mode,count(*) FILTER (WHERE l.status IS NULL OR l.status='IMMATURE') AS pending,
 count(*) FILTER (WHERE (l.status IS NULL OR l.status='IMMATURE') AND
 (e.body->>'horizon_end_at')::timestamptz<clock_timestamp()) AS horizon_ended_pending,
 count(*) FILTER (WHERE l.status='UNRESOLVED') AS unresolved
FROM alpha_shadow_v1.forecast_records f JOIN alpha_shadow_v1.forecast_runs r ON r.id=f.run_id
JOIN alpha_shadow_v1.audit_events e ON e.id=f.id LEFT JOIN latest l ON l.forecast_id=f.id
GROUP BY r.mode;
-- Completeness for the frozen initial HIST/REGIME manifest: expected 111 targets/model.
SELECT f.session_date,m.model_name,m.version,count(*) AS issued_targets,
 111-count(*) AS absent_targets,count(*) FILTER (WHERE f.status='FORECAST') AS scored_targets
FROM alpha_shadow_v1.forecast_records f JOIN alpha_shadow_v1.model_registry m ON m.id=f.model_id
GROUP BY f.session_date,m.model_name,m.version;
