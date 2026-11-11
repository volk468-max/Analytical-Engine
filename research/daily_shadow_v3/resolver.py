"""Outcome resolution uses the deletable, original anchor payload; full window only."""
from research.daily_shadow.core import future_sessions,calendar,utc
from .adapter import future_anchor_units
import pandas as pd
import math

def resolve(forecast,anchor,observations,splits,now,*,data_reviewed):
    base=dict(forecast_id=forecast['id'],status='UNRESOLVED',outcome=None,completed_sessions=0,last_publication_at=None,revision_ref=None,reason=None)
    days=future_sessions(forecast['session'],forecast['horizon']);closing=calendar().session_close(pd.Timestamp(days[-1])).to_pydatetime()
    if utc(now)<closing:return dict(base,status='IMMATURE',reason='FULL_HORIZON_NOT_MATURE')
    if not data_reviewed or anchor is None:return dict(base,reason='ANCHOR_OR_ACTION_EVIDENCE_UNAVAILABLE')
    if not isinstance(anchor,(int,float)) or not math.isfinite(anchor) or anchor<=0:return dict(base,reason='INVALID_ANCHOR')
    mapping={r['date']:r for r in observations}
    if len(mapping)!=len(observations) or any(d not in mapping for d in days):return dict(base,reason='DUPLICATE_OR_MISSING_FUTURE_SESSION')
    rows=[mapping[d] for d in days]
    if any(not r.get('available_at') or utc(r['available_at'])>utc(now) for r in rows):return dict(base,status='IMMATURE',reason='FUTURE_BAR_NOT_AVAILABLE')
    if any(utc(r['available_at'])<calendar().session_close(pd.Timestamp(r['date'])).to_pydatetime() for r in rows):return dict(base,reason='FUTURE_BAR_AVAILABLE_BEFORE_ITS_CLOSE')
    key='low' if forecast['label_type']=='LOW_INTRADAY' else 'close'
    values=[future_anchor_units(r[key],forecast['session'],r['date'],splits) for r in rows]
    if any(not math.isfinite(v) or v<=0 for v in values):return dict(base,reason='INVALID_FUTURE_MARK')
    y=any(v<=anchor*(1-forecast['threshold_pct']/100)+anchor*1e-12 for v in values)
    return dict(base,status='MATURED',outcome=y,completed_sessions=len(days),last_publication_at=max(r['available_at'] for r in rows),reason=None)

def resolve_once(store,forecast_id,window_snapshot,now,*,data_reviewed=False):
    """Resolve from the original licensed anchor, append outcome with revised source ref.
    Caller collects only under a currently authorized contract. No networking here.
    Retrieval time is conservative availability; it is NOT renamed publication.
    """
    from .adapter import Snapshot
    import psycopg
    with store.connect() as c:
        f=c.execute("select body from alpha_research_v3.journal where id=%s and kind='FORECAST'",(forecast_id,)).fetchone()[0]
    f=dict(f,id=str(forecast_id));anchor=None;observations=[];splits=[];ready=False
    if data_reviewed and f['status']=='RESEARCH_FORECAST' and window_snapshot and not window_snapshot.legal_reason:
        try:
            permit=store.permit(f['contract_id'])
            if permit.reason(now,fixture=window_snapshot.fixture) is None:
                original=store.private(f['anchor_ref']);symbol=f['symbol']
                ready=(window_snapshot.provider==permit.provider and window_snapshot.basis==original['basis'] and window_snapshot.currency.get(symbol)=='USD' and window_snapshot.fixture==f['source_fixture'])
                if ready:
                    anchor=original['bars'][symbol][-1]['close']
                    observations=[dict(r,available_at=window_snapshot.retrieved_at) for r in window_snapshot.bars[symbol] if r['date'] in future_sessions(f['session'],f['horizon'])]
                    splits=window_snapshot.splits[symbol]
        except (psycopg.Error,KeyError):ready=False
    outcome=resolve(f,anchor,observations,splits,now,data_reviewed=ready)
    if outcome['status']=='MATURED':
        ref=store.payload(f['contract_id'],window_snapshot,permit.raw_until)
        outcome['revision_ref']=window_snapshot.revision
    store.outcome(str(forecast_id)+':'+__import__('hashlib').sha256(__import__('json').dumps(outcome,sort_keys=True).encode()).hexdigest(),outcome)
    return outcome
