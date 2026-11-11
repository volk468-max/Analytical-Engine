"""One bounded isolated Railway daily job; never imports a trading or production app."""
import os,json,uuid,time,hashlib,logging
from dataclasses import replace
from datetime import datetime,timezone,timedelta
from zoneinfo import ZoneInfo
import psycopg,pandas as pd
from research.daily_shadow.core import calendar,canonical,utc
from research.daily_shadow.store import Store
from research.daily_shadow_v3.adapter import EODHDAdapter,HTTPTransport,VendorError,issuance_gate,ratio
from research.daily_shadow_v3.engine import candidates
from research.daily_shadow_v3.store import ResearchStore
from research.daily_shadow_v3.resolver import resolve_once
from research.daily_shadow_v3.actions import REFERENCES,check_event
from .config import identity,dsn,vault_key,models,ConfigurationError
from .bootstrap import CONTRACT,permit as configured_permit
CRON='0 2 * * 2-6'

def latest_completed(now):
 c=calendar();ny=now.astimezone(ZoneInfo('America/New_York'));day=pd.Timestamp(ny.date())
 if c.is_session(day) and now>=c.session_close(day).to_pydatetime():return day.strftime('%Y-%m-%d')
 return c.date_to_session(day,direction='previous').strftime('%Y-%m-%d') if not c.is_session(day) else c.previous_session(day).strftime('%Y-%m-%d')

def paid_status(transport=None):
 # Account metadata is not archived (may contain personal information).
 secret=os.environ.get('EODHD_API_TOKEN')
 if not secret:raise VendorError('MISSING_CREDENTIALS')
 transport=transport or HTTPTransport();b=transport.get('/api/user',{'fmt':'json'},secret)
 try:
  o=json.loads(b);cadence=str(o.get('subscriptionType','')).lower();quota=o.get('dailyRateLimit')
  active=cadence in ('monthly','yearly') and not isinstance(quota,bool) and int(quota)>=100000
 except Exception:raise VendorError('INVALID_ACCOUNT_STATUS') from None
 # API exposes billing cadence/quota, not invoice or product entitlement. The
 # owner's paid EOD declaration plus successful full six-symbol fetch is required.
 if not active:raise VendorError('PAID_EOD_ENTITLEMENT_NOT_VERIFIED')
 return True

def receipt(store,**body):
 with store.connect() as c:c.execute('select alpha_operations_v4.receipt(%s,%s::jsonb)',(uuid.uuid4(),canonical(body)))
 # Only pre-defined diagnostic fields; no exception text, DSN, token or payload.
 print(canonical(body),flush=True)

def acceptance(store):
 with store.connect() as c:
  n,first=c.execute("select count(*),min(issued_at) from alpha_research_v3.forecasts where run_mode='RESEARCH_FORECAST' and status='RESEARCH_FORECAST'").fetchone()
 return dict(phase='ACCEPTANCE_SQL',status='FIRST_REAL_RECORDED' if n else 'NO_REAL_FORECAST_YET',real_forecasts=n,first_issue_at=first.isoformat() if first else None,schedule=CRON)

def effective_permit(store):
 p=store.permit(CONTRACT)
 with store.connect() as c:r=c.execute('select max(access_until) from alpha_operations_v4.renewals where contract_id=%s',(CONTRACT,)).fetchone()[0]
 if r and r>utc(p.access_until):p=replace(p,access_until=r.isoformat())
 return p

def continue_paid_access(url):
 # API check renews bounded access continuity only, never grants new legal rights.
 paid_status();expiry=datetime.now(timezone.utc)+timedelta(days=30)
 with psycopg.connect(url) as c:
  c.execute('set role alpha_shadow_legal_reviewer')
  c.execute('select alpha_operations_v4.renew(%s,%s,%s)',(CONTRACT,expiry,'EODHD_USER_API_PAID_ACTIVE:'+datetime.now(timezone.utc).isoformat()))

def verify_actions(adapter,session):
 secret=os.environ.get('EODHD_API_TOKEN')
 if not secret:raise VendorError('MISSING_CREDENTIALS')
 checks=[];raw={}
 for symbol,kind in [('NVDA','split'),('MU','dividend'),('QQQ','dividend')]:
  path='/api/'+('splits' if kind=='split' else 'div')+'/'+symbol+'.US'
  b=adapter.transport.get(path,{'from':'2021-01-01','to':session,'fmt':'json'},secret)
  try:events=json.loads(b)
  except Exception:raise VendorError('INVALID_ACTION_HISTORY') from None
  if not isinstance(events,list):raise VendorError('INVALID_ACTION_HISTORY')
  raw['https://eodhd.com'+path+'?from=2021-01-01&to='+session]=b
  for ref in [r for r in REFERENCES if r['symbol']==symbol]:
   event=next((e for e in events if e.get('date')==ref['date']),None)
   if event is None:raise VendorError('PRIMARY_ACTION_SAMPLE_MISSING')
   value=ratio(event['split']) if kind=='split' else event.get('unadjustedValue')
   if not check_event(dict(symbol=symbol,date=event['date'],kind=kind,value=value),ref):raise VendorError('PRIMARY_ACTION_SAMPLE_MISMATCH')
   checks.append((symbol,ref['date']))
 return raw,checks

def resolve_due(store,adapter,session,now):
 with store.connect() as c:
  rows=c.execute("""select f.id,f.session_date from alpha_research_v3.forecasts f where run_mode='RESEARCH_FORECAST' and status='RESEARCH_FORECAST' and horizon_end_at<=%s
   and coalesce((select o.status from alpha_research_v3.outcomes o join alpha_research_v3.journal e on e.id=o.id where o.forecast_id=f.id order by e.seq desc limit 1),'UNRESOLVED')<>'MATURED' order by horizon_end_at limit 1000""",(now,)).fetchall()
 if not rows:return 0
 earliest=min(r[1] for r in rows).isoformat()
 historical_adapter=EODHDAdapter(adapter.permit,network_approved=True,history_start=earliest) if earliest<(now-timedelta(days=400)).date().isoformat() else adapter
 window=historical_adapter.collect(session);checked=0
 for fid,_ in rows:
  r=resolve_once(store,fid,window,datetime.now(timezone.utc).isoformat(),data_reviewed=True);checked+=r['status']=='MATURED'
 return checked

def issue_once(store,adapter,bank,session,now=None,*,ready_gap=60):
 # Session-level lock spans collection, baseline cutoff and atomic forecast append.
 with store.connect() as lock:
  if not lock.execute('select pg_try_advisory_lock(280004)').fetchone()[0]:return dict(phase='ISSUE',status='ALREADY_RUNNING',session=session)
  try:
   prior,issued_count=lock.execute("select count(*),count(*) filter(where status='RESEARCH_FORECAST') from alpha_research_v3.forecasts where session_date=%s and run_mode='RESEARCH_FORECAST'",(session,)).fetchone()
   if prior:return dict(phase='ISSUE',status='IDEMPOTENT_ALREADY_RECORDED',session=session,issued=issued_count,blocked=prior-issued_count)
   stamp=(now or datetime.now(timezone.utc)).isoformat();gate=issuance_gate(session,stamp,replace(adapter.permit,finalization_verified=True))
   if gate:return dict(phase='ISSUE',status='STATUS_BLOCKED',reason=gate,session=session)
   first=adapter.collect(session)
   if first.legal_reason:raise VendorError(first.legal_reason)
   # A stable bundle after a bounded wait is operational evidence, not a provider SLA.
   time.sleep(ready_gap)
   second=adapter.collect(session)
   if first.revision!=second.revision:raise VendorError('SOURCE_STILL_REVISING')
   base_revision=second.revision
   store.payload(CONTRACT,first,adapter.permit.raw_until)
   extra,checks=verify_actions(adapter,session)
   second.raw_responses.update(extra)
   second.revision=hashlib.sha256(b''.join(k.encode()+b'\0'+second.raw_responses[k] for k in sorted(second.raw_responses))).hexdigest()
   # Retrieval is re-stamped after the last action response. Never invent publication.
   second.retrieved_at=datetime.now(timezone.utc).isoformat()
   with store.connect() as c:c.execute('select alpha_operations_v4.ready(%s,%s,%s,%s,%s,%s,%s)',(CONTRACT,session,second.revision,first.revision,base_revision,first.retrieved_at,second.retrieved_at))
   with store.connect() as c:issued=c.execute('select clock_timestamp()').fetchone()[0].isoformat()
   if utc(issued)<utc(second.retrieved_at):raise VendorError('CLOCK_SKEW_SOURCE_AHEAD_OF_DATABASE')
   rows=candidates(session,issued,issued,second,bank,replace(adapter.permit,finalization_verified=True),data_reviewed=True)
   baseline={}
   # Baseline uses only outcomes already recorded BEFORE issuance; no future labels.
   for r in rows:
    if r['status']!='RESEARCH_FORECAST':continue
    key=tuple(r[k] for k in ('symbol','label_type','threshold_pct','horizon'))
    if key in baseline:continue
    n,k=lock.execute("""select count(*),coalesce(sum(o.outcome::int),0) from alpha_research_v3.forecasts f join alpha_shadow_v1.model_registry m on m.id=f.model_id
     join lateral(select o.outcome,o.status,e.recorded_at from alpha_research_v3.outcomes o join alpha_research_v3.journal e on e.id=o.id where o.forecast_id=f.id and e.recorded_at<%s order by e.seq desc limit 1)o on true
     where o.status='MATURED' and f.run_mode='RESEARCH_FORECAST' and f.status='RESEARCH_FORECAST' and m.model_name='HIST' and f.symbol=%s and f.label_type=%s and f.threshold_pct=%s and f.horizon=%s and f.horizon_end_at<%s""",(issued,*key,issued)).fetchone()
    baseline[key]=((k+1)/(n+2),n)
   ref=store.payload(CONTRACT,second,adapter.permit.raw_until)
   ids=store.forecasts('LIVE:'+session,rows,bank,CONTRACT,ref,second,run_mode='RESEARCH_FORECAST',baselines=baseline,baseline_cutoff=issued)
   return dict(phase='ISSUE',status='RECORDED',session=session,issued=sum(r['probability_raw'] is not None for r in rows),blocked=sum(r['probability_raw'] is None for r in rows),source_quality='SIX_SYMBOL_SCHEMA_CALENDAR_AND_PRIMARY_ACTION_SAMPLES_REVIEWED',revision=second.revision)
  finally:lock.execute('select pg_advisory_unlock(280004)')

def run_daily():
 identity();url=dsn();store=ResearchStore(url,vault_key(url));now=datetime.now(timezone.utc)
 receipt(store,**acceptance(store))
 try:
  continue_paid_access(url);p=effective_permit(store)
  adapter=EODHDAdapter(p,network_approved=True);session=latest_completed(now)
  # Pre-close first deployment can verify paid access/schema/actions without issuing.
  ny=now.astimezone(ZoneInfo('America/New_York'));day=ny.date().isoformat()
  if not calendar().is_session(pd.Timestamp(day)):
   receipt(store,phase='ISSUE',status='NON_TRADING_DAY',session=day)
  elif issuance_gate(day,now.isoformat(),replace(p,finalization_verified=True)):
   sample=adapter.collect(session);extra,checks=verify_actions(adapter,session)
   sample.raw_responses.update(extra);sample.retrieved_at=datetime.now(timezone.utc).isoformat();sample.revision=hashlib.sha256(b''.join(k.encode()+b'\0'+sample.raw_responses[k] for k in sorted(sample.raw_responses))).hexdigest();store.payload(CONTRACT,sample,p.raw_until)
   receipt(store,phase='PREFLIGHT',status='REAL_ACCESS_AND_ACTION_SAMPLES_VERIFIED',session=session,models=len(models()),checked=len(checks),subscription_active=True)
   receipt(store,phase='ISSUE',status='WAITING_VALID_SESSION_WINDOW',session=day,reason=issuance_gate(day,now.isoformat(),replace(p,finalization_verified=True)))
  else:receipt(store,**issue_once(store,adapter,models(),day))
  checked=resolve_due(store,adapter,session,now)
  from .reporting import weekly_report
  report=weekly_report(store,now)
  receipt(store,phase='EVALUATION',status='RESEARCH_ONLY',checked=checked,pending=report['pending'],report_week=report['week'])
  if os.environ.get('ALPHA_COMPARE_HISTORY_ONCE')=='true':
   try:
    from .historical import run_once
    status=run_once(store,p);receipt(store,phase='HISTORICAL_COMPARISON',status=status)
   except Exception as exc:receipt(store,phase='HISTORICAL_COMPARISON',status='BLOCKED',error_code=type(exc).__name__.upper())
  receipt(store,**acceptance(store))
  if not store.verify():raise RuntimeError('RESEARCH_CHAIN_BROKEN')
  return 0
 except Exception as exc:
  # VendorError messages are our constant codes, never raw transport/DB messages.
  code=str(exc) if isinstance(exc,(VendorError,ConfigurationError)) else type(exc).__name__.upper()
  receipt(store,phase='DAILY',status='ERROR',error_code=code)
  return 1
 finally:
  try:store.expire()
  except Exception as exc:
   print(canonical(dict(phase='RETENTION',status='ERROR',error_code=type(exc).__name__.upper())),flush=True)
   return 1

if __name__=='__main__':
 import sys
 try:sys.exit(run_daily())
 except Exception as exc:
  print(canonical(dict(phase='STARTUP',status='ERROR',error_code=type(exc).__name__.upper())),flush=True);sys.exit(1)
