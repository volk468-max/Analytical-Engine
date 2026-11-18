-- Run in alpha_shadow_research with the forecast reader role.
-- psql --csv -v session_date=YYYY-MM-DD -f forecast-export.sql
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL TIME ZONE 'UTC';
SELECT f.session_date, f.symbol, m.body->>'name' AS model,
       f.horizon, f.threshold_pct, f.label_type, f.probability_raw,
       f.status, j.body->>'reason' AS reason, f.issued_at
FROM alpha_research_v3.forecasts AS f
JOIN alpha_research_v3.journal AS j ON j.id = f.id
JOIN alpha_shadow_v1.audit_events AS m ON m.id = f.model_id
WHERE f.session_date = :'session_date'::date
  AND f.run_mode = 'RESEARCH_FORECAST'
  AND m.body->>'name' IN ('VOL', 'RISK_FORECAST', 'ENSEMBLE_RISK', 'MARKET_PRECURSORS')
ORDER BY f.symbol, model, f.horizon, f.threshold_pct, f.label_type;
COMMIT;
