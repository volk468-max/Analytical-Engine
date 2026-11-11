"""Research probability is not model validation. No mutation of frozen artifacts."""
import math
from datetime import datetime,timezone
import numpy as np
from research.daily_shadow.core import utc,calendar,future_sessions,requested_series,sha,canonical
from .adapter import issuance_gate,normalized_prefix

def complete_models(models):
    """Missing models get an explicit nonnumeric audit identity, never guessed counts."""
    result=list(models)
    keys={(m['name'],tuple(m['series'][k] for k in ('symbol','label_type','threshold_pct','horizon'))) for m in result}
    for symbol,label,threshold,horizon,name in requested_series():
        if (name,(symbol,label,threshold,horizon)) not in keys:
            series=dict(symbol=symbol,label_type=label,threshold_pct=threshold,horizon=horizon)
            result.append(dict(name=name,series=series,version='UNAVAILABLE-'+sha(canonical([name,series]).encode()),unavailable=True,qualified=False,calibrated=False,fixture=True,created_at=None,fit_cutoff=None))
    return result

def probability(model,series,issued,regime):
    symbol,label,threshold,horizon,name=series
    expected=dict(symbol=symbol,label_type=label,threshold_pct=threshold,horizon=horizon)
    if model.get('name')!=name or model.get('series')!=expected:return None,'MODEL_SERIES_MISMATCH'
    if not model.get('created_at') or utc(model['created_at'])>utc(issued) or utc(model['fit_cutoff'])>utc(issued):return None,'MODEL_NOT_AVAILABLE_ASOF'
    b=model.get('count_bank',{})
    if not b or utc(b['last_maturity'])>=utc(model['fit_cutoff']):return None,'UNMATURED_TRAINING_LABEL'
    n,hits=b['n'],b['hits']
    if not isinstance(n,int) or not isinstance(hits,int) or n<=0 or not 0<=hits<=n:return None,'INVALID_COUNTS'
    base=(hits+1)/(n+2)
    if name=='HIST':return base,None
    if name!='REGIME' or regime not in b.get('groups',{}):return None,'MISSING_REGIME'
    g=b['groups'][regime]
    if g['n']<0 or not 0<=g['hits']<=g['n']:return None,'INVALID_REGIME_COUNTS'
    return (g['hits']+20*base)/(g['n']+20),None

def regime(snapshot):
    rows=normalized_prefix(snapshot.bars.get('QQQ',[]),snapshot.splits.get('QQQ',[]),snapshot.session)
    if len(rows)<200:return None
    c=np.array([r['close'] for r in rows]);return 'UP' if c[-1]>=c[-200:].mean() and c[-1]>c[-21] else ('DOWN' if c[-1]<c[-200:].mean() and c[-1]<=c[-21] else 'MIXED')

def candidates(session,issued,decision,snapshot,models,permit,*,data_reviewed=False):
    if utc(decision)>utc(issued):raise ValueError('FUTURE_DECISION')
    models=complete_models(models)
    gate=issuance_gate(session,issued,permit);bykey={(m['name'],tuple(m['series'][k] for k in ('symbol','label_type','threshold_pct','horizon'))):m for m in models}
    if len(bykey)!=len(models):raise ValueError('AMBIGUOUS_MODEL_SERIES')
    reg=regime(snapshot) if snapshot.bars else None;rows=[]
    for series in requested_series():
        symbol,label,threshold,horizon,name=series;m=bykey.get((name,(symbol,label,threshold,horizon)));dates=future_sessions(session,horizon)
        # Conservative availability of the last outcome close; this is a planned deadline, not publication.
        import pandas as pd
        horizon_end=calendar().session_close(pd.Timestamp(dates[-1])).isoformat()
        reason=gate or snapshot.legal_reason or permit.reason(issued,fixture=snapshot.fixture,horizon_end=(utc(horizon_end)+__import__('datetime').timedelta(days=1)).isoformat())
        if reason is None and snapshot.basis!='RAW_AS_TRADED_OHLC; VOLUME_SPLIT_ADJUSTED; ADJUSTED_CLOSE_TOTAL_RETURN':reason='UNSUPPORTED_SOURCE_BASIS'
        if reason is None and not data_reviewed:reason='DATA_ACTION_BASIS_NOT_REVIEWED'
        if reason is None and (snapshot.retrieved_at is None or utc(snapshot.retrieved_at)>utc(decision)):reason='SOURCE_NOT_AVAILABLE_AT_DECISION'
        if reason is None and snapshot.publication_at and (utc(snapshot.publication_at)>utc(snapshot.retrieved_at) or utc(snapshot.publication_at)>utc(decision)):reason='FUTURE_PUBLICATION'
        if reason is None and snapshot.session!=session:reason='STALE_SOURCE_SESSION'
        if symbol in ('A','B','C'):reason=reason or 'PORTFOLIO_SELF_FINANCING_NAV_NOT_QUALIFIED'
        elif reason is None and (symbol not in snapshot.bars or snapshot.currency.get(symbol)!='USD' or snapshot.bars[symbol][-1]['date']!=session):reason='MISSING_OR_MIXED_SESSION_INPUT'
        if reason is None and (m is None or m.get('unavailable')):reason='MODEL_UNAVAILABLE'
        p=None
        if reason is None:p,reason=probability(m,series,issued,reg)
        rows.append(dict(symbol=symbol,label_type=label,threshold_pct=threshold,horizon=horizon,model_name=name,model_version=m['version'] if m else None,model_hash=sha(canonical(m).encode()) if m else None,session=session,decision_at=decision,issued_at=issued,horizon_end_at=horizon_end,status='RESEARCH_FORECAST' if reason is None else 'STATUS_BLOCKED',reason=reason,model_status='MODEL_NOT_VALIDATED',training_status='TRAINING_REPLAY_NOT_PIT',data_status='UNQUALIFIED_FIXTURE' if snapshot.fixture else ('REVIEWED_INPUTS' if data_reviewed else 'UNQUALIFIED'),probability_raw=p,probability_calibrated=None,calendar='XNYS_exchange_calendars_4.11.2',label_definition='NEXT_N_TRADING_SESSION_TOUCH_FROM_FROZEN_ANCHOR;SPLIT_ONLY_PRICE',source_publication_at=snapshot.publication_at,source_retrieved_at=snapshot.retrieved_at))
    # Never issue an unpaired research model. A missing/gated partner blocks both.
    grouped={}
    for r in rows:grouped.setdefault(tuple(r[k] for k in ('symbol','label_type','threshold_pct','horizon')),[]).append(r)
    for pair in grouped.values():
        if len(pair)!=2 or any(r['status']!='RESEARCH_FORECAST' for r in pair):
            for r in pair:
                if r['status']=='RESEARCH_FORECAST':r.update(status='STATUS_BLOCKED',reason='PAIRED_BASELINE_UNAVAILABLE',probability_raw=None)
    return rows
