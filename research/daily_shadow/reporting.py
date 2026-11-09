"""Single-series quality report; never mix different labels/models/versions."""
import math
import numpy as np
import pandas as pd
from .core import calendar

def report(forecasts,outcomes,minimum_blocks=10):
 latest={}
 for o in outcomes:latest[o['forecast_id']]=o
 result=dict(issued=len(forecasts),blocked=sum(f['status']!='FORECAST' for f in forecasts),matured=0,backlog=sum(f['id'] not in latest or latest[f['id']]['status']=='IMMATURE' for f in forecasts),brier=None,logloss=None,calibration_bias=None,intervals=None,reliability=[],quality_status='INSUFFICIENT_SUPPORT',power_status='NOT_ESTABLISHED')
 groups={(f['symbol'],f['label_type'],f['threshold_pct'],f['horizon'],f['model_version']) for f in forecasts}
 if len(groups)>1:raise ValueError('REPORT_ONE_IMMUTABLE_SERIES_AT_A_TIME')
 pairs=[(f,latest[f['id']]) for f in forecasts if f.get('mode')=='PROSPECTIVE' and f['status']=='FORECAST' and f.get('probability_raw') is not None and f['id'] in latest and latest[f['id']]['status']=='MATURED']
 result['matured']=len(pairs)
 if not pairs:return result
 dates=sorted({f['session'] for f,o in pairs});cal=calendar();lo=cal.sessions.get_loc(pd.Timestamp(dates[0]));hi=cal.sessions.get_loc(pd.Timestamp(dates[-1]));N=hi-lo+1
 blocks=len({(cal.sessions.get_loc(pd.Timestamp(d))-lo)//120 for d in dates});result.update(observed_dates=len(dates),calendar_blocks120=blocks,independent_events='UNKNOWN')
 if blocks<minimum_blocks:return result
 y=np.array([o['outcome'] for f,o in pairs],float);p=np.array([f['probability_raw'] for f,o in pairs],float)
 if np.any(~np.isfinite(p)) or np.any((p<0)|(p>1)):raise ValueError('INVALID_PROBABILITY')
 q=np.clip(p,1e-6,1-1e-6);b=(p-y)**2;ll=-y*np.log(q)-(1-y)*np.log1p(-q);idx=np.array([cal.sessions.get_loc(pd.Timestamp(f['session']))-lo for f,o in pairs]);dn=np.bincount(idx,minlength=N);values=np.column_stack([b,ll,p-y,y]);sums=np.zeros((N,4));np.add.at(sums,idx,values);intervals={}
 for L in (60,120,180):
  rng=np.random.default_rng(270027);samples=[]
  for _ in range(999):
   ix=((rng.integers(N,size=(N+L-1)//L)[:,None]+np.arange(L))%N).ravel()[:N];den=dn[ix].sum()
   if den:samples.append(sums[ix].sum(axis=0)/den)
  intervals[str(L)]=np.quantile(samples,[.025,.975],axis=0).tolist()
 result.update(brier=float(b.mean()),logloss=float(ll.mean()),calibration_bias=float((p-y).mean()),base_rate=float(y.mean()),intervals=intervals,quality_status='EXPLORATORY_CONDITIONAL_ON_FITTED_MODEL',effective_n=None)
 # Explicit HAC support; gaps remain gaps, not concatenated independent observations.
 def neff(vals,indices,total):
  counts=np.bincount(indices,minlength=total)
  if np.any(counts==0):return None
  z=np.bincount(indices,weights=vals,minlength=total)/counts;z-=z.mean();g=z@z/total
  if g<=0:return None
  lr=g+2*sum((1-k/121)*(z[k:]@z[:-k]/total) for k in range(1,min(120,total-1)+1))
  return float(min(total,max(1,total*g/max(lr,1e-12))))
 result['effective_n']=neff(y,idx,N)
 for k in range(10):
  mask=(p>=k/10)&((p<(k+1)/10) if k<9 else (p<=1));ii=idx[mask]
  result['reliability'].append(dict(bin=k,n=int(mask.sum()),mean_probability=float(p[mask].mean()) if mask.any() else None,frequency=float(y[mask].mean()) if mask.any() else None,effective_n=neff(y[mask],ii,N) if mask.any() else None,interpretation='DEPENDENT_POINTWISE_BIN_NOT_THRESHOLD_VALIDATION'))
 return result
