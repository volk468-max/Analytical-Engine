"""Independent READ ONLY SQL audit. No EODHD call, model fit or DB write."""
import json
from datetime import datetime,timezone
import psycopg
from .config import identity,dsn
from .diagnostics import RunAudit

EXPECTED="""WITH expected AS (
 SELECT s.symbol,l.label_type,t.threshold_pct,h.horizon,m.model_name
 FROM (VALUES('SPY'),('QQQ'),('SOXX'),('AMD'),('NVDA'),('MU'))s(symbol)
 CROSS JOIN (VALUES('EOD_CLOSE'),('LOW_INTRADAY'))l(label_type)
 CROSS JOIN (VALUES(5),(10),(15))t(threshold_pct)
 CROSS JOIN (VALUES(10),(20),(60))h(horizon)
 CROSS JOIN (VALUES('HIST'),('REGIME'))m(model_name)
 UNION ALL
 SELECT p.symbol,'EOD_CLOSE',10,60,m.model_name FROM (VALUES('A'),('B'),('C'))p(symbol)
 CROSS JOIN (VALUES('HIST'),('REGIME'))m(model_name)
), sessions AS (SELECT session_date FROM alpha_research_v3.calendar_sessions WHERE session_date>=%s::date AND (((session_date+1)::timestamp+interval '2 hours 30 minutes') AT TIME ZONE 'UTC')<=CURRENT_TIMESTAMP)
SELECT s.session_date,count(*) FILTER(WHERE f.id IS NULL) AS missing_records,
 count(*) FILTER(WHERE e.symbol NOT IN('A','B','C') AND (f.id IS NULL OR f.probability_raw IS NULL OR f.status<>'RESEARCH_FORECAST')) AS missing_numeric_stock_series
FROM sessions s CROSS JOIN expected e
LEFT JOIN (alpha_research_v3.forecasts f JOIN alpha_shadow_v1.model_registry m ON m.id=f.model_id)
 ON f.session_date=s.session_date AND f.run_mode='RESEARCH_FORECAST' AND f.symbol=e.symbol AND f.label_type=e.label_type AND f.threshold_pct=e.threshold_pct AND f.horizon=e.horizon AND m.model_name=e.model_name
GROUP BY s.session_date ORDER BY s.session_date"""

def inspect(url,*,isolated_test=False,start_session='2026-11-11'):
 from research.daily_shadow_v3.adapter import date_only
 date_only(start_session)
 info=psycopg.conninfo.conninfo_to_dict(url)
 if info.get('dbname')!='alpha_shadow_research':raise ValueError('WRONG_DATABASE_NAME')
 if isolated_test:
  if info.get('host') not in ('localhost','127.0.0.1'):raise ValueError('LOCAL_TEST_ONLY')
 else:identity()
 with psycopg.connect(url,connect_timeout=10) as c:
  c.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY');c.execute("SET LOCAL TIME ZONE 'UTC'")
  def rows(sql,params=None):
   cur=c.execute(sql,params);names=[x.name for x in cur.description]
   return [dict(zip(names,row)) for row in cur.fetchall()]
  result=dict(verification='DIRECT_READ_ONLY_SQL',observed_at=datetime.now(timezone.utc).isoformat(),expected_session_start=start_session,missing_run_grace='02:30 UTC next day after expected session')
  result['database']=rows('SELECT current_database() AS database,current_setting(\'server_version\') AS postgres_version')[0]
  result['totals']=rows("""SELECT count(*) AS all_forecast_records,count(*) FILTER(WHERE run_mode='RESEARCH_FORECAST') AS research_records,
   count(*) FILTER(WHERE run_mode='RESEARCH_FORECAST' AND status='RESEARCH_FORECAST' AND probability_raw IS NOT NULL) AS numeric_research_forecasts,
   min(issued_at) FILTER(WHERE run_mode='RESEARCH_FORECAST' AND status='RESEARCH_FORECAST') AS first_issue_utc,
   max(issued_at) FILTER(WHERE run_mode='RESEARCH_FORECAST' AND status='RESEARCH_FORECAST') AS latest_issue_utc
   FROM alpha_research_v3.forecasts""")[0]
  result['by_issuance_date']=rows("SELECT issued_at::date AS issuance_date,count(*) AS records,count(*) FILTER(WHERE status='RESEARCH_FORECAST') AS numeric FROM alpha_research_v3.forecasts WHERE run_mode='RESEARCH_FORECAST' GROUP BY 1 ORDER BY 1")
  result['by_ticker']=rows("SELECT symbol,count(*) AS records,count(*) FILTER(WHERE status='RESEARCH_FORECAST') AS numeric FROM alpha_research_v3.forecasts WHERE run_mode='RESEARCH_FORECAST' GROUP BY 1 ORDER BY 1")
  result['issuances']=rows("SELECT session_date,issued_at,count(*) AS records,count(*) FILTER(WHERE status='RESEARCH_FORECAST') AS numeric FROM alpha_research_v3.forecasts WHERE run_mode='RESEARCH_FORECAST' GROUP BY 1,2 ORDER BY 1,2")
  result['duplicate_logical_series']=rows("SELECT f.session_date,f.symbol,f.label_type,f.threshold_pct,f.horizon,m.model_name,count(*) AS copies FROM alpha_research_v3.forecasts f JOIN alpha_shadow_v1.model_registry m ON m.id=f.model_id WHERE run_mode='RESEARCH_FORECAST' GROUP BY 1,2,3,4,5,6 HAVING count(*)>1")
  result['missing_expected']=rows(EXPECTED,(start_session,))
  result['suspicious_numeric_fixture_rows']=rows("SELECT count(*) AS count FROM alpha_research_v3.forecasts f JOIN alpha_research_v3.journal j ON j.id=f.id JOIN alpha_shadow_v1.audit_events m ON m.id=f.model_id WHERE f.run_mode='RESEARCH_FORECAST' AND f.status='RESEARCH_FORECAST' AND (coalesce((j.body->>'source_fixture')::boolean,true) OR coalesce((m.body->>'fixture')::boolean,false))")[0]['count']
  result['successful_audited_run_ids']=rows("SELECT count(DISTINCT body->>'run_id') AS count FROM alpha_operations_v4.receipts WHERE body->>'phase'='RUN_COMPLETED' AND body->>'status'='SUCCESS'")[0]['count']
  result['successful_forecast_run_ids']=rows("SELECT count(DISTINCT a.body->>'run_id') AS count FROM alpha_operations_v4.receipts a WHERE a.body->>'phase'='RUN_COMPLETED' AND a.body->>'status'='SUCCESS' AND EXISTS(SELECT 1 FROM alpha_operations_v4.receipts b WHERE b.body->>'run_id'=a.body->>'run_id' AND b.body->>'phase'='ISSUE' AND b.body->>'status'='RECORDED')")[0]['count']
  result['legacy_run_ids_unavailable']=rows("SELECT exists(SELECT 1 FROM alpha_operations_v4.receipts WHERE body->>'phase'='ISSUE' AND body->>'status'='RECORDED' AND body->>'run_id' IS NULL) AS exists")[0]['exists']
  result['complete_forecast_issuances']=sum(r['records']==222 and r['numeric']==216 for r in result['issuances'])
  return result

def main():
 audit=RunAudit()
 try:
  report=inspect(dsn());print(json.dumps(report,default=str,sort_keys=True),flush=True);return 0
 except Exception as exc:audit.failure('PERSISTENCE_INSPECTION',exc,persist=False);return 1
if __name__=='__main__':
 import sys
 sys.exit(main())
