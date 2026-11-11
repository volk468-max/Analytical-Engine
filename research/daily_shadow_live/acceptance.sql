-- Run read-only inside the isolated Railway PostgreSQL, not production.
BEGIN READ ONLY;
SELECT current_database() AS database, current_setting('server_version') AS postgres_version;
SELECT count(*) AS genuine_numeric_forecasts,min(issued_at) AS first_issue_utc,max(issued_at) AS latest_issue_utc
FROM alpha_research_v3.forecasts
WHERE run_mode='RESEARCH_FORECAST' AND status='RESEARCH_FORECAST' AND probability_raw IS NOT NULL;
SELECT f.session_date,f.symbol,f.label_type,f.threshold_pct,f.horizon,m.model_name,m.version,f.issued_at,f.status,
       j.body->>'source_fixture' AS source_fixture,j.body->>'model_status' AS model_status,j.body->>'training_status' AS training_status
FROM alpha_research_v3.forecasts f JOIN alpha_research_v3.journal j ON j.id=f.id
JOIN alpha_shadow_v1.model_registry m ON m.id=f.model_id
WHERE f.run_mode='RESEARCH_FORECAST' ORDER BY f.issued_at DESC,f.symbol LIMIT 12;
SELECT count(*) AS duplicate_series FROM (
 SELECT session_date,symbol,label_type,threshold_pct,horizon,model_id,run_mode,count(*)
 FROM alpha_research_v3.forecasts GROUP BY 1,2,3,4,5,6,7 HAVING count(*)>1
) x;
COMMIT;
