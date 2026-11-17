"""Independent atomic Market Drawdown Precursors manifest within the authorised isolated daily worker."""
import os,uuid
from dataclasses import replace
from datetime import datetime,timezone
import pandas as pd
from research.daily_shadow.core import canonical,utc,sha
from research.daily_shadow.store import Store
from research.daily_shadow_v3.adapter import EODHDAdapter,issuance_gate,VendorError
from . import market_precursors_daily as vol
from .readiness import collect_stable
from .bootstrap import CONTRACT


def enabled():return os.environ.get('ALPHA_MARKET_PRECURSORS_ENABLED','false').lower()=='true'


def prior_batch(connection,session):
    return connection.execute("""select count(*),count(*) filter(where f.status='RESEARCH_FORECAST')
      from alpha_research_v3.forecasts f join alpha_shadow_v1.model_registry m on m.id=f.model_id
      where session_date=%s and run_mode='RESEARCH_FORECAST' and m.model_name='MARKET_PRECURSORS'""",(session,)).fetchone()


def run_market_precursors(store,permit,transport,session,*,clock=None,gap=60,collector=None):
    from .runtime import receipt
    clock=clock or (lambda:datetime.now(timezone.utc));permit=replace(permit,finalization_verified=True)
    gate=issuance_gate(session,clock().isoformat(),permit)
    if gate:return dict(phase='MARKET_PRECURSORS',status='WAITING_VALID_SESSION_WINDOW',reason=gate,session=session)
    with store.connect() as lock:
        if not lock.execute('select pg_try_advisory_xact_lock(280009)').fetchone()[0]:return dict(phase='MARKET_PRECURSORS',status='ALREADY_RUNNING',session=session)
        prior,numeric=prior_batch(lock,session)
        if prior:return dict(phase='MARKET_PRECURSORS',status='ALREADY_RECORDED' if prior==156 else 'PARTIAL_FAILURE',session=session,issued=numeric,blocked=prior-numeric)
        # Fetch each name in its own validated bundle: one bad symbol cannot erase
        # all ten; raw responses never escape the encrypted deletable payload plane.
        snapshots={};banks={};errors={};refs={};readiness={}
        # A first pass over all names followed by the second pass provides >=60s
        # per-symbol stability without ten serial one-minute sleeps.
        if collector is None:
            import time
            first={};seen={}
            for symbol in vol.SYMBOLS:
                try:
                    adapter=EODHDAdapter(permit,transport=transport,clock=clock,network_approved=True,history_start=vol.NBIS_START if symbol=='NBIS' else '2000-01-01',symbols=vol.required(symbol))
                    snap=adapter.collect(session)
                    if snap.legal_reason:raise VendorError(snap.legal_reason)
                    ref=store.payload(CONTRACT,snap,permit.raw_until)
                    first[symbol]=(adapter,snap,ref);seen[symbol]=clock()
                except VendorError as exc:errors[symbol]=exc.code
            for symbol,(adapter,initial,ref) in first.items():
                try:
                    # collect_stable reuses retained first fetch; subsequent retries
                    # retain both source vintages and produce durable readiness receipts.
                    class FirstThenLive:
                        def __init__(self):self.permit=permit;self.used=False
                        def collect(self,day):
                            if not self.used:self.used=True;return initial
                            return adapter.collect(day)
                    waited=[False]
                    def sleep_remaining(seconds):
                        wait=seconds if waited[0] else max(0,seconds-(clock()-seen[symbol]).total_seconds())
                        waited[0]=True
                        if wait:time.sleep(wait)
                    a,b,h1,h2=collect_stable(FirstThenLive(),store,CONTRACT,session,gap=gap,clock=clock,symbols=vol.required(symbol),sleeper=sleep_remaining)
                    snapshots[symbol]=b;readiness[symbol]=(a.retrieved_at,b.retrieved_at,h1,h2)
                except VendorError as exc:errors[symbol]=exc.code
        else:
            for symbol in vol.SYMBOLS:
                try:snapshots[symbol]=collector(symbol)
                except VendorError as exc:errors[symbol]=exc.code
        # Explicit current day midnight cutoff: no outcome from this anchor day
        # enters training. Models are recorded before taking actual SQL issued_at.
        created=clock().isoformat();fit=session+'T00:00:00+00:00'
        for symbol in vol.SYMBOLS:
            snap=snapshots.get(symbol)
            try:
                if symbol in errors:raise ValueError(errors[symbol])
                df=vol.frame(snap,symbol)
                banks[symbol]=[vol.artifact(df,task,fit,created,snap.revision,fixture=snap.fixture) for task in vol.series((symbol,))]
            except ValueError as exc:
                reason=str(exc)
                if not __import__('re').fullmatch(r'[A-Z0-9_]{1,96}',reason):raise
                errors[symbol]=reason
                banks[symbol]=[vol.unavailable(t,created,reason) for t in vol.series((symbol,))]
            if snap:
                refs[symbol]=store.payload(CONTRACT,snap,permit.raw_until)
                # Real source stability was checked above; fixture collector only
                # exists for isolated tests and is never selected by CLI/runtime.
                if collector is None:
                    t1,t2,h1,h2=readiness[symbol]
                    with store.connect() as c:c.execute('select alpha_operations_v4.ready(%s,%s,%s,%s,%s,%s,%s)',(CONTRACT,session,snap.revision,h1,h2,t1,t2))
        allmodels=[m for bank in banks.values() for m in bank]
        mids={}
        with store.connect() as c:
            for m in allmodels:mids[m['version']]=Store.append(c,'model','Market Drawdown Precursors:'+m['version'],m)
        with store.connect() as c:issued=c.execute('select clock_timestamp()').fetchone()[0].isoformat()
        if issuance_gate(session,issued,permit):raise VendorError('MARKET_PRECURSORS_BATCH_MISSED_SESSION_WINDOW')
        rows=[]
        for symbol in vol.SYMBOLS:
            rows.extend(vol.rows(session,issued,snapshots.get(symbol),banks[symbol],permit,reviewed=symbol not in errors,reason=errors.get(symbol)))
        # All 156 rows or none. No baseline invented for a target lacking HIST.
        with store.connect() as c:
            c.execute('select pg_advisory_xact_lock(280003)')
            for row in rows:
                symbol=row['symbol'];snap=snapshots.get(symbol);b=dict(row);version=b.pop('model_version');b.pop('model_name')
                b.update(contract_id=str(CONTRACT),model_id=str(mids[version]),run_mode='SYNTHETIC' if snap and snap.fixture else 'RESEARCH_FORECAST',anchor_ref=str(refs[symbol]) if symbol in refs else None,source_fixture=bool(snap and snap.fixture),source_revision=snap.revision if snap else None)
                key='MDP_V1:'+session+':'+':'.join(str(row[k]) for k in ('symbol','label_type','threshold_pct','horizon'))
                store.append(c,'FORECAST',key,b)
        n=sum(r['status']=='RESEARCH_FORECAST' for r in rows)
        return dict(phase='MARKET_PRECURSORS',status='RECORDED' if n==156 else 'RECORDED_WITH_BLOCKED',session=session,issued=n,blocked=156-n,issued_at=issued,models=156,source_quality='PER_SYMBOL_SCHEMA_CALENDAR_SPLIT_ONLY_STABLE_CURRENT_VENDOR_REPLAY_NOT_PIT',revision=vol.MANIFEST_HASH)


def preflight(store,permit,transport,session,*,clock=None):
    """Actual data/model readiness only. Never issues or backdates a forecast."""
    from .runtime import receipt
    clock=clock or (lambda:datetime.now(timezone.utc));ready=blocked=0
    for symbol in vol.SYMBOLS:
        try:
            adapter=EODHDAdapter(permit,transport=transport,clock=clock,network_approved=True,history_start=vol.NBIS_START if symbol=='NBIS' else '2000-01-01',symbols=vol.required(symbol))
            snap=adapter.collect(session)
            if snap.legal_reason:raise VendorError(snap.legal_reason)
            store.payload(CONTRACT,snap,permit.raw_until);df=vol.frame(snap,symbol)
            bank=[vol.artifact(df,t,session+'T00:00:00+00:00',clock().isoformat(),snap.revision) for t in vol.series((symbol,))]
            n=sum(not m['unavailable'] for m in bank);ready+=n;blocked+=12-n
            reasons=sorted({m['reason'] for m in bank if m['unavailable']})
            receipt(store,phase='MARKET_PRECURSORS_PREFLIGHT',status='READY' if n==12 else 'PARTIAL_SUPPORT',session=session,models=12,checked=n,blocked=12-n,reason=symbol+':'+(','.join(reasons) if reasons else 'SCHEMA_CALENDAR_SPLIT_BASIS_AND_FIT_CHECKED_NOT_PIT_NOT_ISSUED'))
        except (VendorError,ValueError) as exc:
            code=getattr(exc,'code',str(exc))
            if not __import__('re').fullmatch(r'[A-Z0-9_]{1,96}',code):raise
            blocked+=12;receipt(store,phase='MARKET_PRECURSORS_PREFLIGHT',status='BLOCKED',session=session,models=12,checked=0,blocked=12,reason=symbol+':'+code)
    return dict(phase='MARKET_PRECURSORS_PREFLIGHT',status='COMPLETED_NO_FORECAST_ISSUED',session=session,models=156,checked=ready,blocked=blocked)


def inspect_market_precursors(store):
    """Direct read-only SQL, emitted in worker context without credentials/raw data."""
    with store.connect() as c:
        # Store.connect checks identity and installs the restricted session role.
        # Finish that setup transaction before selecting snapshot isolation.
        c.commit()
        c.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        n,numeric,first,last=c.execute("""select count(*),count(*) filter(where f.status='RESEARCH_FORECAST'),min(issued_at),max(issued_at)
          from alpha_research_v3.forecasts f join alpha_shadow_v1.model_registry m on m.id=f.model_id
          where run_mode='RESEARCH_FORECAST' and m.model_name='MARKET_PRECURSORS'""").fetchone()
        duplicate=c.execute("""select count(*) from(select f.session_date,f.symbol,f.label_type,f.threshold_pct,f.horizon,count(*) from alpha_research_v3.forecasts f join alpha_shadow_v1.model_registry m on m.id=f.model_id where run_mode='RESEARCH_FORECAST' and m.model_name='MARKET_PRECURSORS' group by1,2,3,4,5 having count(*)>1) q""".replace('group by1','group by 1')).fetchone()[0]
    return dict(phase='MARKET_PRECURSORS_SQL_AUDIT',status='DIRECT_READ_ONLY_SQL',checked=n,issued=numeric,blocked=n-numeric,first_issue_at=first.isoformat() if first else None,latest_issue_at=last.isoformat() if last else None,reason='DUPLICATES='+str(duplicate))
