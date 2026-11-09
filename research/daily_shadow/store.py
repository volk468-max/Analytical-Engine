"""Explicit-DSN isolated Postgres writer. No migrations, no implicit production URL."""
import uuid,json,hashlib
import psycopg
from .core import canonical
class Store:
 def __init__(self,dsn):self.dsn=dsn
 def connect(self):
  c=psycopg.connect(self.dsn)
  if c.execute('select current_database()').fetchone()[0]!='alpha_shadow_research':c.close();raise ValueError('ISOLATED_DATABASE_REQUIRED')
  c.execute("set time zone 'UTC'");c.execute('set role alpha_shadow_writer');return c
 @staticmethod
 def append(c,kind,key,payload):
  return c.execute('select alpha_shadow_v1.append_event(%s,%s,%s,%s)',(uuid.uuid4(),kind,key,canonical(payload))).fetchone()[0]
 def health(self,key,status,**kw):
  with self.connect() as c:return self.append(c,'health',key,dict(status=status,**kw))
 def job(self,key,session,models,vintage,forecasts,mode='SYNTHETIC'):
  with self.connect() as c:
   c.execute('select pg_advisory_xact_lock(270027)')
   mids={(m['name'],m['version']):self.append(c,'model',m['name']+':'+m['version'],m) for m in models}
   old=c.execute("select id from alpha_shadow_v1.audit_events where kind='run' and event_key=%s",(key,)).fetchone()
   if old:
    prior=c.execute('select distinct s.source_hash from alpha_shadow_v1.forecast_records f join alpha_shadow_v1.source_vintages s on f.vintage_id=s.id where f.run_id=%s',(old[0],)).fetchall()
    if prior and {r[0] for r in prior}!={vintage['source_hash']}:raise ValueError('SOURCE_REVISION_REQUIRES_CORRECTION')
    return [r[0] for r in c.execute('select id from alpha_shadow_v1.forecast_records where run_id=%s order by id',(old[0],)).fetchall()]
   run=self.append(c,'run',key,dict(session=session,mode=mode));vid=self.append(c,'vintage',vintage['source_hash']+':'+key,vintage);ids=[]
   for f in forecasts:
    row=dict(f);name=row.pop('model_name');version=row.get('model_version')
    if version is None:
     candidates=[v for n,v in mids if n==name]
     if len(candidates)!=1:raise ValueError('AMBIGUOUS_MODEL_VERSION')
     version=candidates[0]
    row.update(run_id=str(run),vintage_id=str(vid),model_id=str(mids[(name,version)]));fkey=':'.join(str(row[k]) for k in ('session','symbol','label_type','threshold_pct','horizon','model_id'))
    ids.append(self.append(c,'forecast',fkey,row))
   return sorted(ids,key=str)
 def read_forecast(self,forecast_id):
  with self.connect() as c:
   row=c.execute('select e.body,r.mode from alpha_shadow_v1.forecast_records f join alpha_shadow_v1.audit_events e on e.id=f.id join alpha_shadow_v1.forecast_runs r on r.id=f.run_id where f.id=%s',(forecast_id,)).fetchone()
   if row is None:raise KeyError('FORECAST_NOT_FOUND')
   return dict(row[0],id=str(forecast_id),mode=row[1])
 def outcome(self,key,payload,vintage=None):
  with self.connect() as c:
   body=dict(payload)
   if vintage is not None:body['source_vintage_id']=str(self.append(c,'vintage',vintage['source_hash']+':outcome:'+key,vintage))
   return self.append(c,'outcome',key,body)
 def correction(self,key,forecast_id,reason,replacement,vintage=None):
  with self.connect() as c:
   payload=dict(forecast_id=str(forecast_id),reason=reason,replacement=replacement)
   if vintage is not None:payload['source_vintage_id']=str(self.append(c,'vintage',vintage['source_hash']+':correction:'+key,vintage))
   return self.append(c,'correction',key,payload)
 def verify(self):
  with self.connect() as c:rows=c.execute('select kind,event_key,body_text,previous_hash,record_hash from alpha_shadow_v1.audit_events order by seq').fetchall()
  prev=None
  for kind,key,body,previous,h in rows:
   if previous!=prev or hashlib.sha256(((prev or '')+'|'+kind+'|'+key+'|'+body).encode()).hexdigest()!=h:return False
   prev=h
  return True
