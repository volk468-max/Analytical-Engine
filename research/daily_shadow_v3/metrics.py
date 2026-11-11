"""Research metrics remain distinct from validation; pair on identical mature dates."""
import math

def paired_metrics(rows):
    # Fixture/backfill/blocked records cannot masquerade as genuine prospective evidence.
    eligible=[r for r in rows if r['run_mode']=='RESEARCH_FORECAST' and not r.get('fixture',False) and r['status']=='RESEARCH_FORECAST' and r.get('outcome_status')=='MATURED']
    pairs={}
    for r in eligible:
        key=tuple(r[k] for k in ('session','symbol','label_type','threshold_pct','horizon'))
        if r['model_name'] in pairs.setdefault(key,{}):raise ValueError('PARALLEL_VERSIONS_REQUIRE_SEPARATE_COMPARISON')
        pairs[key][r['model_name']]=r
    complete=[g for g in pairs.values() if set(g)=={'HIST','REGIME'}]
    out=dict(status='UNVALIDATED_RESEARCH_ONLY',paired_dates=len(complete),independent_events=None,confidence_interval=None,statistical_power='NOT_ESTABLISHED',metrics={})
    for m in ('HIST','REGIME'):
        data=[g[m] for g in complete]
        if not data:out['metrics'][m]=dict(brier=None,logloss=None);continue
        if any(g['HIST']['outcome']!=g['REGIME']['outcome'] for g in complete):raise ValueError('PAIRED_EVENT_MISMATCH')
        raw=[r['probability_raw'] for r in data]
        if any(not isinstance(p,(int,float)) or not math.isfinite(p) or not 0<=p<=1 for p in raw):raise ValueError('INVALID_PROBABILITY')
        p=[min(1-1e-6,max(1e-6,a)) for a in raw];y=[int(r['outcome']) for r in data]
        out['metrics'][m]=dict(brier=sum((a-b)**2 for a,b in zip(raw,y))/len(p),logloss=sum(-b*math.log(a)-(1-b)*math.log1p(-a) for a,b in zip(p,y))/len(p))
    # No iid CI from overlapping windows. Existing block/report machinery needs sufficient future data.
    return out
