"""Pure/offline contracts, session gate, qualified-model runner and label resolver."""
import base64,hashlib,json,math
from datetime import datetime,timezone,timedelta
from typing import Protocol
import numpy as np
import pandas as pd
import exchange_calendars as xc

def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)
def sha(b):return hashlib.sha256(b).hexdigest()
def utc(s):
 t=datetime.fromisoformat(s)
 if t.tzinfo is None:raise ValueError('UTC_AWARE_REQUIRED')
 return t.astimezone(timezone.utc)
def calendar(name='XNYS'):
 if name not in ('XNYS','XNAS'):raise ValueError('UNSUPPORTED_EXCHANGE')
 # XNAS alias maps to the common US equity session calendar; halt differences need provider evidence.
 return xc.get_calendar('XNYS',start='2000-01-01',end='2035-12-31')
def session_gate(session,now):
 t=utc(now);d=pd.Timestamp(session);c=calendar()
 if d.date()!=t.date():return 'BACKFILL_NOT_PROSPECTIVE'
 if not c.is_session(d):return 'WEEKEND' if d.weekday()>4 else 'HOLIDAY'
 if t<=c.session_close(d).to_pydatetime():return 'BEFORE_CLOSE'
 return 'READY'
def future_sessions(session,horizon):
 c=calendar();i=c.sessions.get_loc(pd.Timestamp(session));return [str(d.date()) for d in c.sessions[i+1:i+1+horizon]]

class Provider(Protocol):
 def collect(self,session:str)->dict: ...

def archive(raw,session,publication_at,ingestion_at,qualification='UNQUALIFIED',basis='UNKNOWN',**kw):
 return dict(raw_b64=base64.b64encode(raw).decode(),source_hash=sha(raw),session=session,publication_at=publication_at,ingestion_at=ingestion_at,qualification=qualification,basis=basis,**kw)
def quality(v,session,issued):
 if v['session']!=session:return 'STALE_SESSION'
 if v.get('historical_archive',False):return 'HISTORICAL_REPLAY_NOT_LIVE'
 if not v.get('publication_at') or not v.get('ingestion_at'):return 'MISSING_SOURCE_TIMESTAMPS'
 try:
  if utc(v['publication_at'])>utc(v['ingestion_at']) or utc(v['ingestion_at'])>utc(issued):return 'LATE_OR_FUTURE_SOURCE'
 except (ValueError,TypeError):return 'INVALID_SOURCE_TIMESTAMPS'
 if any(utc(t)>utc(issued) for t in v.get('feature_available_at',[])):return 'FUTURE_FEATURE'
 if v.get('qualification')!='QUALIFIED_PIT':return 'PIT_UNQUALIFIED'
 if not v.get('actions_qualified'):return 'CORPORATE_ACTIONS_UNQUALIFIED'
 if v.get('basis')!='SPLIT_NORMALIZED_PRICE' and v.get('basis')!='FROZEN_TOTAL_RETURN_NAV':return 'WRONG_BASIS'
 return None

def recipes(prices,returns):
 p=np.asarray(prices,float);r=np.asarray(returns,float)
 if p.shape!=(3,) or np.any(~np.isfinite(p)) or np.any(p<=0):raise ValueError('BAD_PRICES')
 if r.ndim!=2 or r.shape[1]!=3 or len(r)<200 or len(r)>252 or np.any(~np.isfinite(r)):raise ValueError('HISTORY_REQUIRED')
 vol=np.std(r,axis=0,ddof=1)
 if np.any(vol<=0):raise ValueError('ZERO_VOL')
 lo,hi=0.,float(max(vol)*10)
 for _ in range(100):
  mid=(lo+hi)/2
  if np.clip(mid/vol,.1,.5).sum()>1:hi=mid
  else:lo=mid
 weights=np.clip((lo+hi)/2/vol,.1,.5)
 return {name:dict(weights=w.tolist(),cash=100000*cash,units=(100000*w/p).tolist(),initial_nav=100000,currency='USD',hypothetical=True) for name,w,cash in [('A',np.ones(3)/3,0.),('B',np.ones(3)*.2,.4),('C',weights,0.)]}

def requested_series():
 return [(s,label,t,h,m) for s in ('SPY','QQQ','SOXX','AMD','NVDA','MU') for label in ('LOW_INTRADAY','EOD_CLOSE') for t in (5,10,15) for h in (10,20,60) for m in ('HIST','REGIME')]+[(s,'PORTFOLIO_EOD_CLOSE',10,60,m) for s in ('A','B','C') for m in ('HIST','REGIME')]

def raw_estimate(model,task,session,issued,regime,symbol=None):
 if task not in model['supported_tasks']:return None,'UNSUPPORTED_TASK'
 if not model['qualified']:return None,'MODEL_UNQUALIFIED'
 if utc(model['fit_cutoff'])>utc(issued):return None,'FUTURE_MODEL_FIT'
 # Frozen counts can only contain full-horizon matured labels before fit_cutoff.
 rows=[r for r in model['training'] if r.get('task')==task and r.get('symbol')==symbol]
 if not rows or any(utc(r['maturity'])>utc(model['fit_cutoff']) for r in rows):return None,'IMMATURE_TRAINING_LABEL'
 base=(sum(r['y'] for r in rows)+1)/(len(rows)+2)
 if model['name']=='HIST':return base,None
 if model['name']!='REGIME':return None,'UNSUPPORTED_MODEL'
 matched=[r for r in rows if r['regime']==regime]
 return (sum(r['y'] for r in matched)+20*base)/(len(matched)+20),None

def forecast(session,symbol,label,threshold,horizon,model,vintage,issued,decision,snapshot=None):
 if utc(decision)>utc(issued):raise ValueError('FUTURE_DECISION')
 task=f'{label}:{threshold}:{horizon}';reason=quality(vintage,session,issued)
 if session_gate(session,issued)!='READY':reason=session_gate(session,issued)
 if vintage.get('basis')=='FROZEN_TOTAL_RETURN_NAV' and label!='PORTFOLIO_EOD_CLOSE':reason='WRONG_BASIS'
 if label=='PORTFOLIO_EOD_CLOSE' and (not snapshot or vintage.get('basis')!='FROZEN_TOTAL_RETURN_NAV'):reason='PORTFOLIO_TOTAL_RETURN_INPUT_REQUIRED'
 if reason!='INVALID_SOURCE_TIMESTAMPS' and vintage.get('publication_at') and vintage.get('ingestion_at') and (utc(decision)<utc(vintage['publication_at']) or utc(decision)<utc(vintage['ingestion_at'])):reason='DECISION_BEFORE_INGESTION'
 if symbol in ('A','B','C') and (label,threshold,horizon)!=('PORTFOLIO_EOD_CLOSE',10,60):raise ValueError('UNSUPPORTED_PORTFOLIO_TARGET')
 anchor=vintage.get('anchors',{}).get(symbol)
 if reason is None and (anchor is None or not math.isfinite(anchor) or anchor<=0):reason='FROZEN_ANCHOR_REQUIRED'
 p=None
 if reason is None:p,reason=raw_estimate(model,task,session,issued,vintage.get('regime'),symbol)
 return dict(session=session,symbol=symbol,label_type=label,threshold_pct=threshold,horizon=horizon,issued_at=issued,decision_at=decision,status='STATUS_BLOCKED' if reason else 'FORECAST',reason=reason,probability_raw=p,probability_calibrated=None,score_kind='RESEARCH_UNCALIBRATED',snapshot=snapshot,basis=vintage.get('basis'),frozen_anchor=anchor,horizon_end_at=calendar().session_close(pd.Timestamp(future_sessions(session,horizon)[-1])).isoformat())

def resolve(f,anchor,observations,now,basis,actions_qualified):
 expected=future_sessions(f['session'],f['horizon']);context=dict(forecast_id=f['id'],completed_sessions=0,last_publication_at=None,source_hashes=[r.get('source_hash') for r in observations],outcome=None,mae=None,time_to_hit=None)
 bydate={r['session']:r for r in observations}
 if len(bydate)!=len(observations):return dict(context,status='UNRESOLVED',reason='DUPLICATE_SOURCE_SESSION')
 if not observations or now is None:return dict(context,status='IMMATURE',reason='NO_MATURE_SOURCE')
 maturity_close=calendar().session_close(pd.Timestamp(expected[-1])).to_pydatetime()
 if utc(now)<maturity_close:return dict(context,status='IMMATURE',reason='FULL_HORIZON_NOT_MATURE')
 if any(d not in bydate for d in expected):return dict(context,status='UNRESOLVED',reason='MATURE_WINDOW_GAP')
 rows=[bydate[d] for d in expected]
 if any(not r.get('source_hash') for r in rows):return dict(context,status='UNRESOLVED',reason='MISSING_OUTCOME_PROVENANCE')
 if any(utc(r['publication_at'])>utc(now) for r in rows):return dict(context,status='IMMATURE',reason='SOURCE_NOT_PUBLISHED')
 if not actions_qualified or basis!=f['basis']:return dict(context,status='UNRESOLVED',reason='BASIS_OR_ACTIONS_UNQUALIFIED')
 key={'LOW_INTRADAY':'low','EOD_CLOSE':'close','PORTFOLIO_EOD_CLOSE':'nav'}[f['label_type']]
 values=[r.get(key) for r in rows]
 if not math.isfinite(anchor) or anchor<=0 or any(x is None or not math.isfinite(x) or x<0 for x in values):return dict(context,status='UNRESOLVED',reason='INVALID_MARK')
 hit=next((i+1 for i,x in enumerate(values) if x<=anchor*(1-f['threshold_pct']/100)+anchor*1e-12),None)
 return dict(context,status='MATURED',reason=None,completed_sessions=len(rows),last_publication_at=max(r['publication_at'] for r in rows),outcome=hit is not None,mae=1-min(values)/anchor,time_to_hit=hit)
