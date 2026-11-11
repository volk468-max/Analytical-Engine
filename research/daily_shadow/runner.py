"""Callable one-shot job, no scheduler/startup hooks; live provider NOT configured."""
from datetime import datetime,timezone
from .core import *

def run_once(session,provider,models,store,issued,decision,snapshots=None,mode='SYNTHETIC',live_approved=False):
 if mode!='SYNTHETIC' and not live_approved:raise PermissionError('LIVE_REQUIRES_SEPARATE_OWNER_APPROVAL')
 status=session_gate(session,issued);key=f'{mode}:{session}:'+sha(canonical(models).encode())
 if status!='READY':return dict(status=status,health_id=str(store.health(key,status)),records=0)
 vintage=None
 for attempt in range(3):
  try:vintage=provider.collect(session);break
  except (TimeoutError,ConnectionError):continue
 if vintage is None:
  vintage=archive(b'',session,None,None,qualification='UNAVAILABLE',basis='UNKNOWN',provider_error='BOUNDED_RETRIES_EXHAUSTED')
 data=[]
 for symbol,label,threshold,horizon,name in requested_series():
  series=dict(symbol=symbol,label_type=label,threshold_pct=threshold,horizon=horizon)
  matches=[m for m in models if m['name']==name and (m.get('series')==series or 'series' not in m)]
  if len(matches)!=1:raise ValueError('EXPLICIT_UNAMBIGUOUS_MODEL_REGISTRY_REQUIRED')
  model=matches[0]
  f=forecast(session,symbol,label,threshold,horizon,model,vintage,issued,decision,(snapshots or {}).get(symbol));f['model_name']=name;f['model_version']=model['version'];data.append(f)
 ids=store.job(key,session,models,vintage,data,mode)
 return dict(status='NOT_RUNNING_SYNTHETIC_DRY_RUN' if mode=='SYNTHETIC' else 'ONE_SHOT_COMMITTED',records=len(ids),ids=list(map(str,ids)))

class FixtureProvider:
 def __init__(self,vintage):self.vintage=vintage
 def collect(self,session):return self.vintage

def blocked_models():
 return [dict(name=m,version='issue27-review-'+sha(b''.join(p.name.encode()+p.read_bytes() for p in sorted(__import__('pathlib').Path(__file__).parent.glob('*.py')) if not p.name.startswith('test_'))),qualified=False,calibrated=False,fit_cutoff='2026-01-01T00:00:00+00:00',supported_tasks=[],training=[],code_sha256=sha(b''.join(p.name.encode()+p.read_bytes() for p in sorted(__import__('pathlib').Path(__file__).parent.glob('*.py')) if not p.name.startswith('test_'))),params={'status':'FROZEN_REVIEW_ONLY','series':'PARALLEL_VERSION_ON_CHANGE'}) for m in ('HIST','REGIME')]
