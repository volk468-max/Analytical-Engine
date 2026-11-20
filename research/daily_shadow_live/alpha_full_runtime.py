"""Daily Alpha Full journal, point-in-time learning, separate checksummed export."""
import base64
import hashlib
import gzip
import json
import io
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from research.daily_shadow.core import canonical, calendar
from .alpha_full import FEATURE_SCHEMA, MANIFEST, NAMES, VERSION, forecast, train
from .context_factors import utc


def load_bundle():
    """Private delivery contract: inline base64 or a mounted JSON file, never both.
    No credentials are inspected. Missing input is a valid partial-model state.
    """
    encoded=os.environ.get('ALPHA_FULL_BUNDLE_B64')
    path=os.environ.get('ALPHA_FULL_BUNDLE_PATH')
    if encoded and path:raise ValueError('FULL_AMBIGUOUS_BUNDLE_SOURCE')
    if not encoded and not path:return None
    if encoded:
        if len(encoded)>2_000_000:raise ValueError('FULL_BUNDLE_TOO_LARGE')
        raw=base64.b64decode(encoded,validate=True)
        if raw.startswith(b'\x1f\x8b'):
            with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:raw=stream.read(1_500_001)
            if len(raw)>1_500_000:raise ValueError('FULL_BUNDLE_TOO_LARGE')
    else:
        p=Path(path)
        if p.suffix!='.json' or p.stat().st_size>1_500_000:raise ValueError('FULL_BUNDLE_SIZE_OR_TYPE')
        raw=p.read_bytes()
    value=json.loads(raw)
    if not isinstance(value,dict):raise ValueError('FULL_INVALID_BUNDLE')
    return value


def learning_records(store,cutoff):
    """Use exact archived baseline-reference outcomes resolved BEFORE today's issue.
    A row is the original Alpha Full features, not today's reconstruction.
    """
    query="""
    WITH archive AS (
      SELECT DISTINCT ON (session_date) * FROM alpha_full_v1.runs
      WHERE body->'manifest'->>'feature_schema_sha256'=%s AND issued_at<%s
      ORDER BY session_date,issued_at,id
    )
    SELECT a.session_date, a.body->>'issued_at', r,
           f.horizon_end_at, o.outcome, e.recorded_at
    FROM archive a
    CROSS JOIN LATERAL jsonb_array_elements(a.body->'rows') r
    JOIN alpha_research_v3.forecasts f ON f.id=(r->>'baseline_forecast_id')::uuid
      AND f.session_date=a.session_date AND f.issued_at<=a.issued_at
      AND f.symbol=r->>'symbol' AND f.horizon=(r->>'horizon')::int
      AND f.threshold_pct=(r->>'threshold_pct')::int AND f.label_type=r->>'label_type'
      AND f.run_mode='RESEARCH_FORECAST'
    JOIN alpha_shadow_v1.audit_events m ON m.id=f.model_id AND m.body->>'name'=r->>'baseline_model'
    JOIN LATERAL (
      SELECT q.* FROM alpha_research_v3.outcomes q JOIN alpha_research_v3.journal j ON j.id=q.id
      WHERE q.forecast_id=f.id AND j.recorded_at<%s
      ORDER BY j.seq DESC LIMIT 1
    ) o ON o.status='MATURED'
    JOIN alpha_research_v3.journal e ON e.id=o.id
    WHERE r->>'status'='EXPERIMENTAL_FORECAST'
    ORDER BY a.session_date,r->>'symbol',r->>'horizon',r->>'threshold_pct',r->>'label_type'
    """
    with store.connect() as c:
        c.commit();c.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        rows=c.execute(query,(FEATURE_SCHEMA,cutoff,cutoff)).fetchall()
    return [dict(session=str(day),symbol=r['symbol'],issued_at=issued,maturity_at=maturity.isoformat(),
                 outcome_available_at=available.isoformat(),target=[r['horizon'],r['threshold_pct'],r['label_type']],
                 feature_names=r['feature_names'],feature_schema_sha256=FEATURE_SCHEMA,
                 x=r['feature_vector'],offset=r['offset'],y=int(outcome),fixture=False)
            for day,issued,r,maturity,outcome,available in rows]


def run_full(store,audit,blob,session,*,now=None):
    if os.environ.get('ALPHA_FULL_ENABLED')!='true':return
    issued=(now or datetime.now(timezone.utc)).isoformat()
    # Refuse archival bootstrap/delayed/manual replays before any model computation.
    import pandas as pd
    close=calendar().session_close(pd.Timestamp(session)).to_pydatetime()
    if not 0<=(utc(issued)-close).total_seconds()<36*3600:
        audit.emit(persist=False,phase='ALPHA_FULL',status='SKIPPED',session=session,reason='OUTSIDE_PROSPECTIVE_WINDOW')
        return
    with store.connect() as c:
        prior=c.execute('SELECT id,body FROM alpha_full_v1.runs WHERE session_date=%s AND model_version=%s',
                        (session,VERSION)).fetchone()
    if prior:
        emit_export(audit,prior[1],str(prior[0]),already=True)
        return
    warnings=[]
    try:bundle=load_bundle()
    except (ValueError,OSError,TypeError):
        bundle=None;warnings.append('INVALID_OPTIONAL_CONTEXT_BUNDLE')
    records=learning_records(store,issued)
    artifacts={}
    for h in (10,30):
        for threshold in (5,10,15):
            for label in ('LOW_INTRADAY','EOD_CLOSE'):
                target=(h,threshold,label)
                try:a=train(records,target,issued)
                except ValueError:
                    a=None;warnings.append('LEARNING_REJECTED_PRIOR_RETAINED')
                if a is not None:artifacts[target]=a
    body=forecast(blob,session,issued,bundle=bundle,artifacts=artifacts)
    # Freeze exact baseline IDs; later re-fits or outcome revisions cannot select another forecast.
    with store.connect() as c:
        references=c.execute("""SELECT f.id,f.symbol,m.body->>'name',f.horizon,f.threshold_pct,f.label_type,f.issued_at
          FROM alpha_research_v3.forecasts f JOIN alpha_shadow_v1.audit_events m ON m.id=f.model_id
          WHERE f.session_date=%s AND f.run_mode='RESEARCH_FORECAST'
            AND m.body->>'name' IN ('VOL','RISK_FORECAST','MARKET_PRECURSORS')""",(session,)).fetchall()
    bank={}
    for fid,s,name,h,t,l,stamp in references:
        bank.setdefault((s,name,h,t,l,utc(stamp.isoformat()).isoformat()),[]).append(str(fid))
    for r in body['rows']:
        r['baseline_forecast_id']=None
        if r['baseline_model'] is not None:
            ids=bank.get((r['symbol'],r['baseline_model'],r['horizon'],r['threshold_pct'],r['label_type'],
                          utc(r['baseline_issued_at']).isoformat()),[])
            if len(ids)!=1:raise ValueError('FULL_BASELINE_REFERENCE_NOT_UNIQUE')
            r['baseline_forecast_id']=ids[0]
    body['input_warnings']=sorted(set(warnings))
    body['learning_record_count']=len(records)
    # DB enforces current completed session, immutable120-target batch and idempotency.
    with store.connect() as c:
        rid=c.execute('SELECT alpha_full_v1.record(%s,%s)',(uuid.uuid4(),canonical(body))).fetchone()[0]
        saved=c.execute('SELECT body FROM alpha_full_v1.runs WHERE id=%s',(rid,)).fetchone()[0]
    emit_export(audit,saved,str(rid))


def emit_export(audit,body,rid,*,already=False):
    payload=canonical(body).encode();digest=hashlib.sha256(payload).hexdigest()
    encoded=base64.b64encode(gzip.compress(payload,mtime=0)).decode();chunks=[encoded[i:i+2000] for i in range(0,len(encoded),2000)]
    for i,chunk in enumerate(chunks):
        audit.emit(persist=False,phase='ALPHA_FULL_EXPORT',status='CHUNK',session=body['session'],
                   full_run_id=rid,json_sha256=digest,chunk_index=i,chunk_count=len(chunks),payload_b64=chunk,encoding='gzip+base64')
    rows=body['rows']
    audit.emit(persist=False,phase='ALPHA_FULL_EXPORT',status='READY',session=body['session'],
               full_run_id=rid,json_sha256=digest,chunk_count=len(chunks),row_count=120,encoding='gzip+base64',
               numeric=sum(r['probability_raw'] is not None for r in rows),
               learned=sum(r['weights_mode']=='LEARNED_POOLED_EXPERIMENTAL' for r in rows),
               partial=sum(bool(r['missing_features']) for r in rows),already_recorded=already)
