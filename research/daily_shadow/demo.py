"""No network/DB: explicit synthetic in-memory transactional fixture writer."""
import json,uuid,threading,copy
from pathlib import Path
from .core import *
from .runner import *
class MemoryStore:
 def __init__(self):self.jobs={};self.events=[];self.models={};self.lock=threading.Lock()
 def health(self,key,status):self.events.append(dict(key=key,status=status));return key
 def job(self,key,session,models,vintage,forecasts,mode):
  with self.lock:
   for m in models:
    k=(m['name'],m['version']);h=sha(canonical(m).encode())
    if k in self.models and self.models[k]!=h:raise ValueError('MODEL_VERSION_CONFLICT')
    self.models[k]=h
   if key in self.jobs:return self.jobs[key]
   ids=[str(uuid.uuid5(uuid.NAMESPACE_URL,key+str(i))) for i in range(len(forecasts))];self.jobs[key]=ids;self.events.extend(copy.deepcopy(forecasts));return ids

def demo():
 session='2026-11-06';issued='2026-11-06T23:30:00+00:00';v=archive(b'SYNTHETIC FIXTURE NOT LIVE FEED',session,'2026-11-06T22:00:00+00:00','2026-11-06T22:01:00+00:00',historical_archive=True,basis='SPLIT_NORMALIZED_PRICE',provider='OFFLINE_SYNTHETIC',actions_qualified=False,licensing='FIXTURE');store=MemoryStore();provider=FixtureProvider(v);models=blocked_models();first=run_once(session,provider,models,store,issued,issued);second=run_once(session,provider,models,store,issued,issued)
 output=dict(status='NOT RUNNING',mode='OFFLINE_SYNTHETIC',requested_series=len(requested_series()),records=first['records'],all_probabilities_null=all(r['probability_raw'] is None and r['probability_calibrated'] is None for r in store.events),idempotent=first['ids']==second['ids'],live_forecasts_exist=False,database_mutated=False)
 (Path(__file__).resolve().parents[2]/'reports/daily-shadow-postgres-v1/dry-run.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output))
if __name__=='__main__':demo()
