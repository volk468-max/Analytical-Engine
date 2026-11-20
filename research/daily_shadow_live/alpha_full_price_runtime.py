"""Independent per-instrument collection, signed close forecasts and mature scoring."""
import os,json,uuid,time,base64,gzip,hashlib
from datetime import datetime,timezone,timedelta
from concurrent.futures import ThreadPoolExecutor,as_completed
from dataclasses import replace
from . import alpha_full_price as model
from .alpha_full_runtime import load_bundle
from research.daily_shadow.core import canonical,calendar
from research.daily_shadow_v3.adapter import EODHDAdapter,HTTPTransport,issuance_gate
from .context_factors import utc
import pandas as pd


def collect_frames(permit,session,*,collector=None,identities=None):
    frames={};failures={};snapshots={}
    start=(datetime.fromisoformat(session)-timedelta(days=5*366)).date().isoformat()
    def collect(symbol):
        if symbol in ('STRIP','SCZM'):
            identity=identities.get(symbol,{}) if isinstance(identities,dict) else {}
            if not isinstance(identity,dict):identity={}
            try:fresh=0<=(datetime.now(timezone.utc)-utc(identity['verified_at_utc'])).total_seconds()<=45*86400
            except (KeyError,ValueError,TypeError):fresh=False
            if (identity.get('provider_symbol')!=symbol+'.US' or identity.get('currency')!='USD'
                    or identity.get('status')!='VERIFIED' or not identity.get('source_url') or not fresh):
                return symbol,None,None,'INSTRUMENT_IDENTITY_UNVERIFIED'
        try:
            snapshot=(collector(symbol) if collector else EODHDAdapter(permit,
                transport=HTTPTransport(max_attempts=2,timeout=3,deadline=time.monotonic()+15),
                network_approved=True,history_start=max(start,model.ENTITY_START.get(symbol,start)),symbols=(symbol,)).collect(session))
            if snapshot.legal_reason:return symbol,None,None,snapshot.legal_reason
            frame=model.price_frame(snapshot,symbol)
            return symbol,frame,snapshot,None
        except Exception as exc:
            reason=str(exc) if __import__('re').fullmatch(r'[A-Z][A-Z0-9_]{0,95}',str(exc)) else 'PRICE_SOURCE_UNAVAILABLE'
            return symbol,None,None,reason
    with ThreadPoolExecutor(max_workers=6) as pool:
        for job in as_completed([pool.submit(collect,s) for s in model.SYMBOLS+model.MARKET]):
            symbol,frame,snapshot,reason=job.result()
            if reason:failures[symbol]=reason
            else:frames[symbol]=frame;snapshots[symbol]=snapshot
    model.attach_market(frames)
    return frames,failures,snapshots


def training_records(store,issued):
    query="""WITH archive AS (
      SELECT DISTINCT ON(session_date) * FROM alpha_full_price_v1.runs
      WHERE body->'manifest'->>'feature_schema_sha256'=%s AND issued_at<%s
      ORDER BY session_date,issued_at,id)
    SELECT a.session_date,a.body->>'issued_at',r,o.actual_return_pct,o.available_at
    FROM archive a CROSS JOIN LATERAL jsonb_array_elements(a.body->'rows') r
    JOIN alpha_full_price_v1.outcomes o ON o.run_id=a.id AND o.symbol=r->>'symbol' AND o.horizon=(r->>'horizon')::int
    WHERE o.available_at<%s AND r->>'status'='EXPERIMENTAL_PRICE_FORECAST'
    ORDER BY a.session_date,r->>'symbol',r->>'horizon'"""
    with store.connect() as c:rows=c.execute(query,(model.SCHEMA,issued,issued)).fetchall()
    return [dict(session=str(day),issued_at=stamp,horizon=r['horizon'],symbol=r['symbol'],
                 context_vector=r['context_vector'],technical_return=r['technical_return'],
                 horizon_volatility=r['horizon_volatility'],actual_return_pct=float(y),
                 outcome_available_at=available.isoformat(),feature_schema_sha256=model.SCHEMA)
            for day,stamp,r,y,available in rows]


def resolve_mature(store,frames,issued):
    """Record derived terminal returns only. Never store/reprint licensed price levels."""
    with store.connect() as c:
        runs=c.execute("SELECT id,body FROM alpha_full_price_v1.runs WHERE session_date<%s",(utc(issued).date(),)).fetchall()
        known=set(c.execute('SELECT run_id,symbol,horizon FROM alpha_full_price_v1.outcomes').fetchall())
    resolved=0
    for rid,body in runs:
        for r in body['rows']:
            if (rid,r['symbol'],r['horizon']) in known:continue
            df=frames.get(r['symbol'])
            if r['status']!='EXPERIMENTAL_PRICE_FORECAST' or df is None or r['target_session'] not in df.index or r['session'] not in df.index:continue
            maturity=calendar().session_close(pd.Timestamp(r['target_session'])).to_pydatetime()
            if maturity>=utc(issued):continue
            actual=(float(df.loc[r['target_session'],'close'])/float(df.loc[r['session'],'close'])-1)*100
            with store.connect() as c:
                c.execute('SELECT alpha_full_price_v1.resolve(%s,%s,%s,%s,%s)',(rid,r['symbol'],r['horizon'],actual,datetime.now(timezone.utc).isoformat()))
            resolved+=1
    return resolved


def evaluation(store,issued):
    query="""WITH a AS (SELECT DISTINCT ON(session_date) * FROM alpha_full_price_v1.runs
      WHERE body->'manifest'->>'feature_schema_sha256'=%s ORDER BY session_date,issued_at,id)
    SELECT r,o.actual_return_pct,o.available_at FROM a CROSS JOIN LATERAL jsonb_array_elements(a.body->'rows') r
    LEFT JOIN alpha_full_price_v1.outcomes o ON o.run_id=a.id AND o.symbol=r->>'symbol' AND o.horizon=(r->>'horizon')::int"""
    with store.connect() as c:records=c.execute(query,(model.SCHEMA,)).fetchall()
    result={};cases=[]
    for h in (10,30):
        subset=[(r,y,t) for r,y,t in records if r['horizon']==h];mature=[(r,float(y),t) for r,y,t in subset if y is not None]
        m=dict(total=len(subset),matured=len(mature),blocked=sum(r['status']=='STATUS_BLOCKED' for r,y,t in subset),pending=0,unresolved=0)
        for r,y,t in subset:
            if r['status']=='STATUS_BLOCKED' or y is not None:continue
            end=calendar().session_close(pd.Timestamp(r['target_session'])).to_pydatetime()
            m['pending' if end>=utc(issued) else 'unresolved']+=1
        if mature:
            for r,y,t in mature:
                if 0<=(utc(issued)-t).total_seconds()<=7*86400:
                    cases.append(dict(symbol=r.get('symbol'),session=r.get('session'),horizon=h,
                        target_session=r['target_session'],expected_return_pct=r['expected_return_pct'],
                        actual_return_pct=y,error_percentage_points=r['expected_return_pct']-y,
                        contributions_pct=r.get('contributions_pct'),missing_features=r.get('missing_features'),
                        technical_missing_features=r.get('technical_missing_features'),
                        context_provenance=r.get('context_provenance'),outcome_available_at=t.isoformat()))
            expected=[r['expected_return_pct'] for r,y,t in mature];actual=[y for r,y,t in mature]
            error=[a-b for a,b in zip(expected,actual)]
            direction=lambda v:1 if v>.25 else (-1 if v<-.25 else 0)
            m.update(mae_percentage_points=sum(abs(v) for v in error)/len(error),
                rmse_percentage_points=(sum(v*v for v in error)/len(error))**.5,
                directional_accuracy=sum(direction(a)==direction(b) for a,b in zip(expected,actual))/len(error),
                strict_sign_accuracy=sum(((a>0)-(a<0))==((b>0)-(b<0)) for a,b in zip(expected,actual))/len(error),
                empirical_band_coverage=sum(r['band_low_pct']<=y<=r['band_high_pct'] for r,y,t in mature)/len(mature),
                matched_technical_mae_pp=sum(abs(100*r['technical_return']-y) for r,y,t in mature)/len(mature),
                matched_zero_return_mae_pp=sum(abs(y) for r,y,t in mature)/len(mature),
                matured_last7days=sum((utc(issued)-t).total_seconds()<=7*86400 for r,y,t in mature))
        result[str(h)]=m
    cases.sort(key=lambda r:abs(r['error_percentage_points']),reverse=True)
    return dict(cutoff_utc=issued,by_horizon=result,accuracy_status='EXPERIMENTAL_NOT_VALIDATED',
                direction_deadband_pct=.25,recent_error_cases=cases[:20],recent_error_case_count=len(cases),
                error_case_selection='LARGEST_20_ABSOLUTE_ERRORS_MATURED_LAST7D_NOT_CAUSAL_ATTRIBUTION')


def export_body(audit,rid,body,*,already=False):
    raw=canonical(body).encode();checksum=hashlib.sha256(raw).hexdigest()
    encoded=base64.b64encode(gzip.compress(raw,mtime=0)).decode();chunks=[encoded[i:i+2000] for i in range(0,len(encoded),2000)]
    for i,chunk in enumerate(chunks):audit.emit(persist=False,phase='ALPHA_FULL_PRICE_EXPORT',status='CHUNK',session=body['session'],full_run_id=str(rid),json_sha256=checksum,chunk_index=i,chunk_count=len(chunks),payload_b64=chunk,encoding='gzip+base64')
    audit.emit(persist=False,phase='ALPHA_FULL_PRICE_EXPORT',status='READY',session=body['session'],full_run_id=str(rid),json_sha256=checksum,chunk_count=len(chunks),row_count=118,numeric=sum(r['expected_return_pct'] is not None for r in body['rows']),already_recorded=already,encoding='gzip+base64')


def run_price(store,audit,permit,session,*,now=None,collector=None):
    if os.environ.get('ALPHA_FULL_PRICE_ENABLED')!='true':return
    stamp=(now or datetime.now(timezone.utc)).isoformat()
    reason=issuance_gate(session,stamp,replace(permit,finalization_verified=True))
    if reason:
        audit.emit(persist=False,phase='ALPHA_FULL_PRICE',status='SKIPPED',session=session,reason=reason);return
    with store.connect() as c:old=c.execute('SELECT id,body FROM alpha_full_price_v1.runs WHERE session_date=%s AND model_version=%s',(session,model.VERSION)).fetchone()
    if old:export_body(audit,old[0],old[1],already=True);return
    try:bundle=load_bundle()
    except Exception:bundle=None
    frames,failures,snapshots=collect_frames(permit,session,collector=collector,identities=(bundle or {}).get('instrument_identity'))
    # Raw histories remain in the existing encrypted/expiring payload plane only.
    from .bootstrap import CONTRACT
    refs={}
    for s,snapshot in snapshots.items():
        try:refs[s]=str(store.payload(CONTRACT,snapshot,permit.raw_until))
        except Exception:
            frames.pop(s,None);failures[s]='SOURCE_ARCHIVE_UNAVAILABLE'
    cutoff=datetime.now(timezone.utc).isoformat()
    if issuance_gate(session,cutoff,replace(permit,finalization_verified=True)):
        audit.emit(persist=False,phase='ALPHA_FULL_PRICE',status='SKIPPED',session=session,reason='SOURCE_COLLECTION_OUTSIDE_ISSUE_WINDOW');return
    matured=resolve_mature(store,frames,cutoff)
    cutoff=datetime.now(timezone.utc).isoformat()
    body=model.forecast(frames,failures,session,cutoff,bundle=bundle,records=training_records(store,cutoff))
    completed=datetime.now(timezone.utc).isoformat()
    for group in ('technical_heads','context_heads'):
        for head in body[group].values():
            if head is not None:
                head['data_cutoff_utc']=head['trained_at'];head['trained_at']=completed
    # Publication timestamps are genuine post-calculation UTC, never scheduled/backdated times.
    with store.connect() as c:issued=c.execute('SELECT clock_timestamp()').fetchone()[0].isoformat()
    if utc(issued)<utc(completed):raise ValueError('PRICE_CLOCK_SKEW_DATABASE_BEHIND_CALCULATION')
    body['calculation_cutoff_utc']=cutoff;body['issued_at']=issued
    for r in body['rows']+body['market_rows']:
        r['issued_at']=issued
        if r['technical_return'] is not None:
            r['technical_weights_sha256']=model.digest(body['technical_heads'][r['horizon']])
            head=body['context_heads'][r['horizon']]
            if head is not None:r['context_weights_sha256']=model.digest(head)
    if issuance_gate(session,issued,replace(permit,finalization_verified=True)):
        audit.emit(persist=False,phase='ALPHA_FULL_PRICE',status='SKIPPED',session=session,reason='CALCULATION_OUTSIDE_ISSUE_WINDOW');return
    for r in body['rows']+body['market_rows']:
        end=calendar().session_close(pd.Timestamp(r['target_session'])).to_pydatetime()+timedelta(days=1)
        why=permit.reason(issued,fixture=False,horizon_end=end.isoformat())
        if why:
            r['license_reason']=why
            if r['status']=='EXPERIMENTAL_PRICE_FORECAST':r.update(status='STATUS_BLOCKED',reason=why,expected_return_pct=None,band_low_pct=None,band_high_pct=None,direction=None)
    body['resolved_at_this_run']=matured
    body['source_revision_sha256']={s:snapshots[s].revision for s in frames}
    body['source_payload_refs']={s:refs[s] for s in frames}
    body['source_retrieved_at_utc']={s:snapshots[s].retrieved_at for s in frames}
    body['source_quality']='SINGLE_RESEARCH_SNAPSHOT_NOT_INDEPENDENTLY_FINALIZED'
    with store.connect() as c:
        rid=c.execute('SELECT alpha_full_price_v1.record(%s,%s)',(uuid.uuid4(),canonical(body))).fetchone()[0]
        saved=c.execute('SELECT body FROM alpha_full_price_v1.runs WHERE id=%s',(rid,)).fetchone()[0]
    export_body(audit,rid,saved)
    audit.emit(persist=False,phase='ALPHA_FULL_PRICE_EVALUATION',status='READY',session=session,statistics=evaluation(store,issued))
