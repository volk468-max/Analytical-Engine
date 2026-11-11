"""Manual/predeploy initialization scoped to the owner's exact isolated Railway IDs."""
import json,hashlib,os,uuid
from datetime import datetime,timezone,timedelta
from pathlib import Path
import psycopg
from research.daily_shadow.core import calendar,canonical
from research.daily_shadow.store import Store
from research.daily_shadow_v3.legal import Permit
from .config import identity,dsn,models,ROOT
CONTRACT=uuid.UUID('73fc59d1-8aaf-480d-bc33-313cbdf428e6')

def permit():
 raw=os.environ.get('ALPHA_LICENSE_MANIFEST')
 if not raw:raise ValueError('OWNER_REVIEWED_LICENSE_MANIFEST_REQUIRED')
 p=Permit(**json.loads(raw))
 if p.scope!='LIVE' or p.operator_class!='PERSONAL' or not p.existing_paid_owner_authorized:raise ValueError('PERSONAL_PAID_OWNER_REVIEW_REQUIRED')
 return p

def apply(url,*,isolated_test=False):
 if not isolated_test:identity()
 elif psycopg.conninfo.conninfo_to_dict(url).get('host') not in ('127.0.0.1','localhost'):raise ValueError('LOCAL_TEST_ONLY')
 with psycopg.connect(url,autocommit=True) as c:
  if c.execute('select current_database()').fetchone()[0]!='alpha_shadow_research':raise ValueError('WRONG_DATABASE_NAME')
  c.execute('select pg_advisory_lock(280104)')
  c.execute('create table if not exists public.alpha_shadow_migrations(name text primary key,sha256 text not null)')
  c.execute('revoke all on public.alpha_shadow_migrations from public')
  paths=[ROOT/'research/daily_shadow/sql'/n for n in ('001_isolated.sql','002_contract_hardening.sql','003_research_forecast.sql')]+[Path(__file__).with_name('004_operations.sql')]
  for path in paths:
   code=path.read_text();digest=hashlib.sha256(code.encode()).hexdigest();old=c.execute('select sha256 from public.alpha_shadow_migrations where name=%s',(path.name,)).fetchone()
   if old:
    if old[0]!=digest:raise ValueError('MIGRATION_DRIFT')
    continue
   assert code.rstrip().endswith('COMMIT;')
   marked=code.rstrip()[:-len('COMMIT;')]+"INSERT INTO public.alpha_shadow_migrations VALUES('"+path.name+"','"+digest+"'); COMMIT;"
   c.execute(marked)
  if not c.execute('select count(*) from alpha_research_v3.calendar_sessions').fetchone()[0]:
   with c.cursor() as cur:cur.executemany('insert into alpha_research_v3.calendar_sessions values(%s,%s,%s)',[(s.date(),calendar().session_close(s).to_pydatetime(),'XNYS_exchange_calendars_4.11.2') for s in calendar().sessions])
  c.execute('select pg_advisory_unlock(280104)')
 return True

def register(url,p,bank):
 with psycopg.connect(url) as c:
  c.execute('set role alpha_shadow_legal_reviewer')
  c.execute('select alpha_research_v3.register_contract(%s,%s::jsonb)',(CONTRACT,canonical(p.to_dict())))
 with Store(url).connect() as c:
  for m in bank:Store.append(c,'model',m['name']+':'+m['version'],m)

if __name__=='__main__':
 identity();url=dsn();apply(url);bank=models();register(url,permit(),bank)
 print(json.dumps(dict(phase='BOOTSTRAP',status='READY',models=len(bank),real_forecasts=0)))
