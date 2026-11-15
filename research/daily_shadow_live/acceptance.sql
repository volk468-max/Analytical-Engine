-- Independent inspection. Run only in the isolated Railway research database.
-- No write, model fit, credential display or EODHD request.
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL TIME ZONE 'UTC';
SELECT current_database() AS database,current_setting('server_version') AS postgres_version,
       current_setting('transaction_read_only') AS read_only;
SELECT count(*) AS all_records,
 count(*) FILTER(WHERE run_mode='RESEARCH_FORECAST') AS research_records,
 count(*) FILTER(WHERE run_mode='RESEARCH_FORECAST' AND status='RESEARCH_FORECAST') AS numeric_research_forecasts,
 min(issued_at) FILTER(WHERE run_mode='RESEARCH_FORECAST' AND status='RESEARCH_FORECAST') AS first_issue_utc,
 max(issued_at) FILTER(WHERE run_mode='RESEARCH_FORECAST' AND status='RESEARCH_FORECAST') AS latest_issue_utc
FROM alpha_research_v3.forecasts;
SELECT issued_at::date AS issuance_date,count(*) AS records,
 count(*) FILTER(WHERE status='RESEARCH_FORECAST') AS numeric
FROM alpha_research_v3.forecasts WHERE run_mode='RESEARCH_FORECAST' GROUP BY 1 ORDER BY 1;
SELECT symbol,count(*) AS records,count(*) FILTER(WHERE status='RESEARCH_FORECAST') AS numeric
FROM alpha_research_v3.forecasts WHERE run_mode='RESEARCH_FORECAST' GROUP BY 1 ORDER BY 1;
SELECT session_date,issued_at,count(*) AS records,count(*) FILTER(WHERE status='RESEARCH_FORECAST') AS numeric
FROM alpha_research_v3.forecasts WHERE run_mode='RESEARCH_FORECAST' GROUP BY 1,2 ORDER BY 1,2;
-- Includes parallel versions as an explicit logical-duplication warning.
SELECT f.session_date,f.symbol,f.label_type,f.threshold_pct,f.horizon,m.model_name,count(*) AS copies
FROM alpha_research_v3.forecasts f JOIN alpha_shadow_v1.model_registry m ON m.id=f.model_id
WHERE f.run_mode='RESEARCH_FORECAST' GROUP BY 1,2,3,4,5,6 HAVING count(*)>1;
SELECT count(DISTINCT body->>'run_id') AS audited_successful_run_ids
FROM alpha_operations_v4.receipts WHERE body->>'phase'='RUN_COMPLETED' AND body->>'status'='SUCCESS';
-- Older deployed code had no run_id/completion marker: do not report their runs as 0.
SELECT exists(SELECT 1 FROM alpha_operations_v4.receipts WHERE body->>'phase'='ISSUE'
 AND body->>'status'='RECORDED' AND body->>'run_id' IS NULL) AS legacy_run_ids_unavailable;
-- Full expected-grid/missing-session audit: python -m research.daily_shadow_live.inspect_persistence
-- It starts at the known first cron session 2026-11-11, including entirely absent days,
-- with a 02:30UTC next-day completion grace. 216 numeric stocks/ETFs +6blocked portfolios.
COMMIT;
