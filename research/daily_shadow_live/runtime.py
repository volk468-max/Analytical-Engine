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
from .diagnostics import ACTIVE,RunAudit,observe
from .readiness import collect_stable
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

def _persist_record(store,record):
 with store.connect() as c:c.execute('select alpha_operations_v4.receipt(%s,%s::jsonb)',(uuid.uuid4(),canonical(record)))

def receipt(store,**body):
 audit=ACTIVE.get() or RunAudit()
 record=audit.emit(persist=False,**body)
 _persist_record(store,record)
 return record

def acceptance(store):
 with store.connect() as c:
  n,first,last=c.execute("select count(*),min(issued_at),max(issued_at) from alpha_research_v3.forecasts where run_mode='RESEARCH_FORECAST' and status='RESEARCH_FORECAST'").fetchone()
 return dict(phase='ACCEPTANCE_SQL',status='FIRST_REAL_RECORDED' if n else 'NO_REAL_FORECAST_YET',real_forecasts=n,first_issue_at=first.isoformat() if first else None,latest_issue_at=last.isoformat() if last else None,schedule=CRON)

def effective_permit(store):
 p=store.permit(CONTRACT)
 with store.connect() as c:r=c.execute('select max(access_until) from alpha_operations_v4.renewals where contract_id=%s',(CONTRACT,)).fetchone()[0]
 if r and r>utc(p.access_until):p=replace(p,access_until=r.isoformat())
 return p

def continue_paid_access(url,transport=None):
 # API check renews bounded access continuity only, never grants new legal rights.
 paid_status(transport);expiry=datetime.now(timezone.utc)+timedelta(days=30)
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
  rows=c.execute("""select f.id,f.session_date,f.symbol from alpha_research_v3.forecasts f where run_mode='RESEARCH_FORECAST' and status='RESEARCH_FORECAST' and horizon_end_at<=%s
   and coalesce((select o.status from alpha_research_v3.outcomes o join alpha_research_v3.journal e on e.id=o.id where o.forecast_id=f.id order by e.seq desc limit 1),'UNRESOLVED')<>'MATURED' order by horizon_end_at limit 1000""",(now,)).fetchall()
 if not rows:return dict(checked=0,unresolved=0)
 earliest=min(r[1] for r in rows).isoformat()
 wanted=tuple(sorted({r[2] for r in rows}))
 historical_adapter=EODHDAdapter(adapter.permit,transport=adapter.transport,network_approved=True,history_start=earliest,symbols=wanted)
 window=historical_adapter.collect(session);checked=0;unresolved=0
 for fid,_,symbol in rows:
  r=resolve_once(store,fid,window,datetime.now(timezone.utc).isoformat(),data_reviewed=True);checked+=r['status']=='MATURED'
  if r['status']!='MATURED':
   unresolved+=1;receipt(store,phase='OUTCOME',status='UNRESOLVED',reason=r['reason'])
 return dict(checked=checked,unresolved=unresolved)

def batch_result(session,total,numeric,*,retry=False):
 expected_total=222;expected_numeric=216
 complete=total==expected_total and numeric==expected_numeric
 return dict(phase='ISSUE',status=('IDEMPOTENT_ALREADY_RECORDED' if retry else 'RECORDED') if complete else 'PARTIAL_FAILURE',session=session,issued=numeric,blocked=total-numeric,reason=None if complete else 'INCOMPLETE_EXPECTED_FORECAST_BATCH')

def issue_once(store,adapter,bank,session,now=None,*,ready_gap=60,clock=None):
 clock=clock or (lambda:datetime.now(timezone.utc))
 # Transaction-scoped lock is released on commit/rollback/disconnect; no cleanup
 # SQL may mask the original exception. Existing forecast rows are never updated.
 with store.connect() as lock:
  if not lock.execute('select pg_try_advisory_xact_lock(280004)').fetchone()[0]:return dict(phase='ISSUE',status='ALREADY_RUNNING',session=session)
  prior,issued_count=lock.execute("select count(*),count(*) filter(where status='RESEARCH_FORECAST') from alpha_research_v3.forecasts where session_date=%s and run_mode='RESEARCH_FORECAST' and model_id in (select id from alpha_shadow_v1.model_registry where model_name in ('HIST','REGIME'))",(session,)).fetchone()
  if prior:return batch_result(session,prior,issued_count,retry=True)
  stamp=(now or clock()).isoformat();gate=issuance_gate(session,stamp,replace(adapter.permit,finalization_verified=True))
  if gate:return dict(phase='ISSUE',status='STATUS_BLOCKED',reason=gate,session=session)
  first,second,first_hash,second_hash=collect_stable(adapter,store,CONTRACT,session,gap=ready_gap,clock=clock)
  extra,checks=verify_actions(adapter,session)
  second.raw_responses.update(extra)
  second.revision=hashlib.sha256(b''.join(k.encode()+b'\0'+second.raw_responses[k] for k in sorted(second.raw_responses))).hexdigest()
  second.retrieved_at=clock().isoformat()
  with store.connect() as c:c.execute('select alpha_operations_v4.ready(%s,%s,%s,%s,%s,%s,%s)',(CONTRACT,session,second.revision,first_hash,second_hash,first.retrieved_at,second.retrieved_at))
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
  result=batch_result(session,len(ids),sum(r['probability_raw'] is not None for r in rows))
  result.update(issued_at=issued,source_quality='SIX_SYMBOL_SCHEMA_CALENDAR_AND_PRIMARY_ACTION_SAMPLES_REVIEWED',revision=second.revision)
  return result

def run_daily():
 audit=RunAudit();token=ACTIVE.set(audit);store=None;exit_code=1;partial=[];phase='STARTUP'
 audit.emit(phase=phase,status='RUN_STARTED',persist=False)
 try:
  identity();url=dsn();store=ResearchStore(url,vault_key(url))
  audit.persister=lambda record:_persist_record(store,record)
  receipt(store,phase='CONFIGURATION',status='VALIDATED')
  receipt(store,**acceptance(store))
  transport=HTTPTransport(observer=observe,deadline=time.monotonic()+900)
  phase='SUBSCRIPTION';continue_paid_access(url,transport);p=effective_permit(store)
  receipt(store,phase=phase,status='ACCOUNT_METADATA_MATCHED',subscription_active=True)
  now=datetime.now(timezone.utc);adapter=EODHDAdapter(p,transport=transport,network_approved=True);session=latest_completed(now)
  ny=now.astimezone(ZoneInfo('America/New_York'));day=ny.date().isoformat();phase='ISSUE'
  try:
   if not calendar().is_session(pd.Timestamp(day)):
    receipt(store,phase=phase,status='NON_TRADING_DAY',session=day)
   elif issuance_gate(day,now.isoformat(),replace(p,finalization_verified=True)):
    sample=adapter.collect(session)
    if sample.legal_reason:raise VendorError(sample.legal_reason)
    extra,checks=verify_actions(adapter,session)
    sample.raw_responses.update(extra);sample.retrieved_at=datetime.now(timezone.utc).isoformat();sample.revision=hashlib.sha256(b''.join(k.encode()+b'\0'+sample.raw_responses[k] for k in sorted(sample.raw_responses))).hexdigest();store.payload(CONTRACT,sample,p.raw_until)
    receipt(store,phase='PREFLIGHT',status='REAL_ACCESS_AND_ACTION_SAMPLES_VERIFIED',session=session,models=len(models()),checked=len(checks),subscription_active=True)
    receipt(store,phase=phase,status='WAITING_VALID_SESSION_WINDOW',session=day,reason=issuance_gate(day,now.isoformat(),replace(p,finalization_verified=True)))
   else:
    result=issue_once(store,adapter,models(),day);receipt(store,**result)
    if result['status'] in ('PARTIAL_FAILURE','STATUS_BLOCKED','ALREADY_RUNNING'):partial.append('ISSUE')
  except Exception as exc:
   audit.failure('LEGACY_ISSUE',exc);partial.append('LEGACY_ISSUE')
  from .vol_runtime import enabled,run_vol,preflight,inspect_vol
  if enabled():
   phase='VOL'
   try:
    if os.environ.get('ALPHA_VOL_PREFLIGHT_ONCE')=='true' and issuance_gate(day,datetime.now(timezone.utc).isoformat(),replace(p,finalization_verified=True)):
     receipt(store,**preflight(store,p,transport,session))
    result=run_vol(store,p,transport,day);receipt(store,**result)
    receipt(store,**inspect_vol(store))
    if result['status'] in ('PARTIAL_FAILURE','ALREADY_RUNNING'):partial.append('VOL')
   except Exception as exc:audit.failure('VOL',exc);partial.append('VOL')
  from .risk_forecast_runtime import enabled as rf_enabled,run_risk_forecast,preflight as rf_preflight,inspect_risk_forecast
  if rf_enabled():
   phase='RISK_FORECAST'
   try:
    if os.environ.get('ALPHA_RISK_FORECAST_PREFLIGHT_ONCE')=='true' and issuance_gate(day,datetime.now(timezone.utc).isoformat(),replace(p,finalization_verified=True)):
     receipt(store,**rf_preflight(store,p,transport,session))
    result=run_risk_forecast(store,p,transport,day);receipt(store,**result)
    receipt(store,**inspect_risk_forecast(store))
    if result['status'] in ('PARTIAL_FAILURE','ALREADY_RUNNING'):partial.append('RISK_FORECAST')
   except Exception as exc:audit.failure('RISK_FORECAST',exc);partial.append('RISK_FORECAST')
  from .ensemble_runtime import enabled as ens_enabled,run_ensemble,preflight as ens_preflight,inspect_ensemble
  if ens_enabled():
   phase='ENSEMBLE_RISK'
   try:
    if os.environ.get('ALPHA_ENSEMBLE_RISK_PREFLIGHT_ONCE')=='true' and issuance_gate(day,datetime.now(timezone.utc).isoformat(),replace(p,finalization_verified=True)):
     receipt(store,**ens_preflight(store,p,transport,session))
    result=run_ensemble(store,p,transport,day);receipt(store,**result)
    receipt(store,**inspect_ensemble(store))
    if result['status'] in ('PARTIAL_FAILURE','ALREADY_RUNNING'):partial.append('ENSEMBLE_RISK')
   except Exception as exc:audit.failure('ENSEMBLE_RISK',exc);partial.append('ENSEMBLE_RISK')
  from .market_precursors_runtime import enabled as mdp_enabled,run_market_precursors,preflight as mdp_preflight,inspect_market_precursors
  if mdp_enabled():
   phase='MARKET_PRECURSORS'
   try:
    if os.environ.get('ALPHA_MARKET_PRECURSORS_PREFLIGHT_ONCE')=='true' and issuance_gate(day,datetime.now(timezone.utc).isoformat(),replace(p,finalization_verified=True)):
     receipt(store,**mdp_preflight(store,p,transport,session))
    result=run_market_precursors(store,p,transport,day);receipt(store,**result)
    receipt(store,**inspect_market_precursors(store))
    if result['status'] in ('PARTIAL_FAILURE','ALREADY_RUNNING'):partial.append('MARKET_PRECURSORS')
   except Exception as exc:audit.failure('MARKET_PRECURSORS',exc);partial.append('MARKET_PRECURSORS')
  phase='EVALUATION';resolution=resolve_due(store,adapter,session,now)
  if resolution['unresolved']:partial.append('OUTCOME_RESOLUTION')
  from .reporting import weekly_report
  report=weekly_report(store,now)
  receipt(store,phase=phase,status='RESEARCH_ONLY',checked=resolution['checked'],unresolved=resolution['unresolved'],pending=report['pending'],report_week=report['week'])
  if os.environ.get('ALPHA_COMPARE_HISTORY_ONCE')=='true':
   phase='HISTORICAL_COMPARISON'
   try:
    from .historical import run_once
    status=run_once(store,p,transport=transport);receipt(store,phase=phase,status=status)
   except Exception as exc:
    audit.failure(phase,exc);partial.append(phase)
  phase='VERIFICATION';receipt(store,**acceptance(store))
  if not store.verify():raise RuntimeError('RESEARCH_CHAIN_BROKEN')
  try:
   from .forecast_export import export_session
   blob=export_session(store,audit,session)
   if blob is not None and os.environ.get('ALPHA_FULL_ENABLED')=='true':
    try:
     from .alpha_full_runtime import run_full
     run_full(store,audit,blob,session)
    except Exception as exc:
     audit.failure('ALPHA_FULL',exc,persist=False);partial.append('ALPHA_FULL')
  except Exception as exc:
   audit.failure('FORECAST_EXPORT',exc,persist=False)
  if os.environ.get('ALPHA_FULL_PRICE_ENABLED')=='true':
   try:
    audit.emit(persist=False,phase='ALPHA_FULL_PRICE',status='STARTING',session=session)
    from .alpha_full_price_runtime import run_price
    run_price(store,audit,p,session)
   except Exception as exc:
    audit.failure('ALPHA_FULL_PRICE',exc,persist=False);partial.append('ALPHA_FULL_PRICE')
  exit_code=2 if partial else 0
 except Exception as exc:
  exit_code=1
  try:audit.failure(phase,exc,persist=store is not None)
  except Exception as audit_error:audit.failure('AUDIT_PERSISTENCE',audit_error,persist=False)
 finally:
  if store is not None:
   try:store.expire()
   except Exception as exc:
    exit_code=1
    try:audit.failure('RETENTION',exc)
    except Exception as audit_error:audit.failure('AUDIT_PERSISTENCE',audit_error,persist=False)
  status='SUCCESS' if exit_code==0 else ('PARTIAL_FAILURE' if exit_code==2 else 'FAILED')
  try:audit.emit(phase='RUN_COMPLETED',status=status,exit_code=exit_code,partial_phases=partial,persist=store is not None,persist_first=True,**audit.http_summary())
  except Exception as exc:
   exit_code=1;audit.failure('AUDIT_PERSISTENCE',exc,persist=False)
   audit.emit(phase='RUN_COMPLETED',status='FAILED',exit_code=1,partial_phases=partial,persist=False,**audit.http_summary())
  ACTIVE.reset(token)
 return exit_code

if __name__=='__main__':
 import sys
 sys.exit(run_daily())
