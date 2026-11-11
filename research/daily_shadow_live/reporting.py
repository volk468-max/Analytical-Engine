"""Private weekly report: genuine forward rows only; no raw prices or synthetic data."""
import math
from datetime import timedelta
from collections import defaultdict
from research.daily_shadow.core import canonical

def scores(rows):
 if not rows:return dict(n=0,brier=None,logloss=None,event_frequency=None,calibration=[],independent_events=None,confidence_interval=None)
 n=len(rows);bins=[]
 for i in range(10):
  group=[r for r in rows if min(9,int(r[0]*10))==i]
  if group:bins.append(dict(bin=i,n=len(group),predicted_mean=sum(p for p,y in group)/len(group),observed_frequency=sum(y for p,y in group)/len(group)))
 return dict(n=n,brier=sum((p-y)**2 for p,y in rows)/n,logloss=sum(-y*math.log(max(1e-6,p))-(1-y)*math.log(max(1e-6,1-p)) for p,y in rows)/n,event_frequency=sum(y for p,y in rows)/n,calibration=bins,independent_events=None,confidence_interval=None)

def weekly_report(store,now):
 week=(now-timedelta(days=now.weekday())).date()
 with store.connect() as c:
  total,pending=c.execute("""select count(*),count(*) filter(where coalesce((select o.status from alpha_research_v3.outcomes o join alpha_research_v3.journal e on e.id=o.id where o.forecast_id=f.id order by e.seq desc limit 1),'UNRESOLVED')<>'MATURED') from alpha_research_v3.forecasts f where run_mode='RESEARCH_FORECAST' and status='RESEARCH_FORECAST'""").fetchone()
  issued_week=c.execute("select count(*) from alpha_research_v3.forecasts where run_mode='RESEARCH_FORECAST' and status='RESEARCH_FORECAST' and issued_at>=%s",(week,)).fetchone()[0]
  rows=c.execute("""select f.symbol,f.label_type,f.threshold_pct,f.horizon,m.model_name,f.probability_raw,o.outcome,b.probability from alpha_research_v3.forecasts f
   join alpha_shadow_v1.model_registry m on m.id=f.model_id
   join lateral(select v.outcome,v.status from alpha_research_v3.outcomes v join alpha_research_v3.journal e on e.id=v.id where v.forecast_id=f.id order by e.seq desc limit 1)o on true
   left join alpha_operations_v4.baselines b on b.forecast_id=f.id where f.run_mode='RESEARCH_FORECAST' and f.status='RESEARCH_FORECAST' and o.status='MATURED'""").fetchall()
  groups=defaultdict(list)
  for symbol,label,threshold,horizon,name,p,y,base in rows:
   key=f'{symbol}/{label}/{threshold}/{horizon}';groups[key+'/'+name].append((p,int(y)))
   if name=='HIST' and base is not None:groups[key+'/BASE_PREQUENTIAL'].append((base,int(y)))
  report=dict(week=week.isoformat(),asof=now.isoformat(),classification='GENUINE_FORWARD_RESEARCH_NOT_VALIDATED',total_forecasts=total,issued_this_week=issued_week,checked=total-pending,pending=pending,metrics={k:scores(v) for k,v in groups.items()},paired_hist_regime=store.metrics(),independent_events=None,confidence_interval=None,baseline_cold_start='BETA_1_1_PRIOR_0.5_NO_MATURED_SUPPORT')
  # Append daily revisions under one weekly family; do not overwrite earlier evidence.
  c.execute('select alpha_operations_v4.report(%s,%s::jsonb)',(now.date(),canonical(report)))
 return report
