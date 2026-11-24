"""Alpha Full price-return heads: separate from historical TOUCH probabilities."""
from collections import Counter
from pathlib import Path
import hashlib
import math
import numpy as np
import pandas as pd
from dataclasses import replace
from .portfolio import SYMBOLS as DISPLAY
from .alpha_full import context,FEATURE_SCHEMA,NAMES,EXPERT
from .context_factors import digest,utc,number
from .vol import frame as prices
from research.daily_shadow.core import future_sessions,calendar,canonical

EXTRA=tuple('ADI ALAB AMAT AMZN CRDO CSCO GE GEV KLAC LLY MRVL NET ORCL RTX TSM'.split())
SYMBOLS=DISPLAY+EXTRA
MARKET=('SPY','QQQ','SOXX')
ENTITY_START={'B':'2025-05-09','NBIS':'2024-10-21'}
PRICE_NAMES=('return5_vol','return20_vol','return60_vol','distance_ma20_vol','distance_ma50_vol','distance_ma200_vol','drawdown20_vol','volatility_change','market_return20_vol','semis_relative20_vol','market_volatility_regime')
CONTEXT_NAMES=NAMES[2:]+('fundamental_assessment','analyst_assessment')
PRIOR=np.r_[-EXPERT[2:],.05,.03]
SCHEMA=digest(dict(version='FULL_PRICE_FEATURES_V1',prices=PRICE_NAMES,context=CONTEXT_NAMES,context_schema=FEATURE_SCHEMA,price_clip=5,return_basis='SPLIT_ONLY_EX_DIVIDENDS'))
VERSION='ALPHA_FULL_PRICE_V1-'+digest(dict(code=Path(__file__).read_text(),schema=SCHEMA))[:16]
MANIFEST=dict(model_name='ALPHA_FULL_PRICE',model_version=VERSION,symbols=list(SYMBOLS),market_symbols=list(MARKET),display_symbols=list(DISPLAY),horizons=[10,30],row_count=len(SYMBOLS)*2,market_row_count=6,price_features=list(PRICE_NAMES),context_features=list(CONTEXT_NAMES),label='TERMINAL_CLOSE_PRICE_RETURN_SPLIT_ADJUSTED_EX_DIVIDENDS',feature_schema_sha256=SCHEMA,qualified=False)


def price_frame(snapshot,symbol):
    if symbol in ENTITY_START:
        snapshot=replace(snapshot,bars={**snapshot.bars,symbol:[r for r in snapshot.bars.get(symbol,[]) if r['date']>=ENTITY_START[symbol]]})
    df=prices(snapshot,symbol).copy();c=df.close
    v=np.exp(df.log_rv20)/np.sqrt(252);df['_daily_vol']=v
    for h in (5,20,60):df['return'+str(h)+'_vol']=(c/c.shift(h)-1)/(v*np.sqrt(h))
    for h in (20,50,200):df['distance_ma'+str(h)+'_vol']=(c/c.rolling(h).mean()-1)/(v*np.sqrt(h))
    df['drawdown20_vol']=(c/c.rolling(20).max()-1)/(v*np.sqrt(20))
    df['volatility_change']=v/v.rolling(60).mean()-1
    for k in PRICE_NAMES[-3:]:df[k]=np.nan
    return df


def attach_market(frames):
    q=frames.get('QQQ');s=frames.get('SOXX')
    if q is None:return
    qr=q.close/q.close.shift(20)-1
    regime=q['_daily_vol']/q['_daily_vol'].rolling(60).mean()-1
    relative=(s.close/s.close.shift(20)-1).reindex(q.index)-qr if s is not None else None
    for df in frames.values():
        scale=df['_daily_vol']*np.sqrt(20)
        df['market_return20_vol']=qr.reindex(df.index)/scale
        df['market_volatility_regime']=regime.reindex(df.index)
        if relative is not None:df['semis_relative20_vol']=relative.reindex(df.index)/scale


def technical_vector(row):
    values=[];missing=[]
    for name in PRICE_NAMES:
        v=float(row[name]);absent=not math.isfinite(v)
        values.append(0. if absent else float(np.clip(v,-5,5)));missing.append(float(absent))
    return [1.]+values+missing


def fit_prices(frames,horizon,issued):
    """Causal historical price-only training; revised vendor history is NOT PIT."""
    capacity = sum(max(0, len(df) - horizon - 20) for df in frames.values())
    width = 1 + 2 * len(PRICE_NAMES)
    x = np.empty((capacity, width))
    y = np.empty(capacity)
    training_days = []
    training_hash = hashlib.sha256(b'[')
    matured={d:calendar().session_close(pd.Timestamp(d)).to_pydatetime()<utc(issued)
             for d in sorted({d for df in frames.values() for d in df.index})}
    for symbol in sorted(frames):
        df=frames[symbol]
        for i in range(20,len(df)-horizon):
            anchor=df.iloc[i];v=float(anchor['_daily_vol'])*np.sqrt(horizon)
            if not math.isfinite(v) or v<=0:continue
            end=df.index[i+horizon]
            if not matured[end]:continue
            target=(float(df.iloc[i+horizon].close)/float(anchor.close)-1)/v
            day = str(df.index[i])
            features = technical_vector(anchor)
            clipped = float(np.clip(target, -10, 10))
            index = len(training_days)
            if index:
                training_hash.update(b',')
            training_hash.update(canonical((day, features, clipped)).encode())
            training_days.append(day)
            x[index] = features
            y[index] = clipped
    training_hash.update(b']')
    dates = Counter(training_days)
    count = len(training_days)
    if len(dates)<40 or count<60:return None
    x = x[:count]
    y = y[:count]
    w = np.fromiter((1 / dates[day] for day in training_days), dtype=float, count=count)
    penalty=np.eye(x.shape[1])*10;penalty[0,0]=1
    beta=np.linalg.solve(x.T@(w[:,None]*x)+penalty,x.T@(w*y))
    residual=y-x@beta
    # Weighted empirical residual bands, explicitly not calibrated coverage.
    order=np.argsort(residual);q=np.cumsum(w[order]);q=q/q[-1]
    band=np.interp([.1,.9],q,residual[order]).tolist()
    return dict(horizon=horizon,beta=beta.tolist(),residual_band=band,n=count,distinct_dates=len(dates),
                trained_at=issued,training_status='REVISED_PRICE_HISTORY_NOT_PIT',training_sha256=training_hash.hexdigest(),qualified=False)


def context_vector(bundle,symbol,session,h,issued,*,fixture=False):
    bundle=bundle if isinstance(bundle,dict) else {}
    market=bundle.get('market_coefficients_by_horizon',{})
    if symbol in MARKET and isinstance(market,dict) and market.get(str(h)):
        bundle=dict(bundle);bundle['coefficients_by_horizon']={str(h):market[str(h)]}
    values,missing,refs=context(bundle,symbol,session,h,issued,fixture=fixture)
    company=bundle.get('company_assessments_by_horizon',{})
    company=company.get(str(h),{}) if isinstance(company,dict) else {}
    assessment=company.get(symbol,{}) if isinstance(company,dict) else {}
    if not isinstance(assessment,dict):assessment={}
    for name,field,days in (('fundamental_assessment','fundamental_score',45),('analyst_assessment','analyst_score',7)):
        try:
            stamp=utc(assessment[field+'_asof_utc'])
            if stamp>utc(issued) or (utc(issued)-stamp).total_seconds()>days*86400:raise ValueError('STALE_ASSESSMENT')
            v=number(assessment[field],-100,100)
            if assessment.get('fixture',False)!=fixture or not assessment.get('source_record_sha256'):
                raise ValueError('ASSESSMENT_PROVENANCE_REQUIRED')
            reliability={'LOW':.25,'MEDIUM':.5,'HIGH':1.}[assessment['confidence_level']]
            values[name]=v/100*reliability;refs[name]=dict(asof_utc=stamp.isoformat(),source_record_sha256=assessment['source_record_sha256'])
        except (ValueError,KeyError,TypeError):missing[name]='ASSESSMENT_UNAVAILABLE'
    x=[float(values.get(k,0)) for k in CONTEXT_NAMES]+[float(k not in values) for k in CONTEXT_NAMES]
    return x,{k:v for k,v in missing.items() if k in CONTEXT_NAMES},refs


def fit_context(records,h,issued):
    rows=[];seen=set();excluded=0
    for r in records:
        if r.get('horizon')!=h or r.get('feature_schema_sha256')!=SCHEMA:continue
        try:
            identity=(r['session'],r['symbol'])
            if identity in seen or not utc(r['issued_at'])<utc(r['outcome_available_at'])<utc(issued):raise ValueError('BAD_TRAINING_TIME_OR_DUPLICATE')
            if len(r['context_vector'])!=2*len(CONTEXT_NAMES) or not all(math.isfinite(v) for v in r['context_vector']):raise ValueError('BAD_VECTOR')
            if not math.isfinite(r['actual_return_pct']) or not math.isfinite(r['technical_return']) or not math.isfinite(r['horizon_volatility']) or r['horizon_volatility']<=0:raise ValueError('BAD_TARGET')
            seen.add(identity);rows.append(r)
        except (KeyError,TypeError,ValueError):excluded+=1
    dates=Counter(r['session'] for r in rows)
    if len(dates)<20:return None
    x=np.array([r['context_vector'] for r in rows]);w=np.array([1/dates[r['session']] for r in rows])
    y=np.array([(r['actual_return_pct']/100-r['technical_return'])/r['horizon_volatility'] for r in rows])
    prior=np.r_[PRIOR,np.zeros(len(CONTEXT_NAMES))]
    beta=np.linalg.solve(x.T@(w[:,None]*x)+10*np.eye(len(prior)),x.T@(w*np.clip(y,-10,10))+10*prior)
    return dict(beta=beta.tolist(),trained_at=issued,n=len(rows),distinct_sessions=len(dates),excluded_records=excluded,training_sha256=digest(rows),feature_schema_sha256=SCHEMA,qualified=False)


def forecast(frames,failures,session,issued,*,bundle=None,records=(),fixture=False):
    failures=dict(failures)
    for symbol,df in frames.items():
        if df.empty or str(df.index[-1])!=session:failures[symbol]='STALE_OR_FUTURE_PRICE_SERIES'
    frames={s:df for s,df in frames.items() if s not in failures}
    heads={h:fit_prices(frames,h,issued) for h in (10,30)}
    overlays={h:fit_context(records,h,issued) for h in (10,30)}
    rows=[]
    for symbol in SYMBOLS+MARKET:
        for h in (10,30):
            r=dict(symbol=symbol,horizon=h,target_session=future_sessions(session,h)[-1],session=session,issued_at=issued,
                   status='STATUS_BLOCKED',reason=failures.get(symbol),expected_return_pct=None,band_low_pct=None,band_high_pct=None,
                   direction=None,qualified=False,calibrated=False,model_name='ALPHA_FULL_PRICE',model_version=VERSION,
                   feature_schema_sha256=SCHEMA,context_vector=None,missing_features={},context_provenance={},technical_return=None,
                   technical_vector=None,technical_missing_features=[],technical_weights_sha256=None,context_weights_sha256=None,
                   contributions_pct=None,
                   horizon_volatility=None,weights_mode='EXPERT_CONTEXT_PRIOR')
            df=frames.get(symbol);head=heads[h]
            if df is None:r['reason']=r['reason'] or 'PRICE_HISTORY_UNAVAILABLE'
            elif head is None:r['reason']='SHARED_TECHNICAL_TRAINING_UNAVAILABLE'
            else:
                vol=float(df.iloc[-1]['_daily_vol'])*np.sqrt(h)
                if not math.isfinite(vol) or vol<=0:r['reason']='CURRENT_VOLATILITY_UNAVAILABLE'
                else:
                    x,missing,refs=context_vector(bundle,symbol,session,h,issued,fixture=fixture)
                    a=overlays[h];beta=np.array(a['beta']) if a else np.r_[PRIOR,np.zeros(len(CONTEXT_NAMES))]
                    raw_delta=float(np.dot(x,beta));delta=float(np.clip(raw_delta,-.6,.6))
                    scale=delta/raw_delta if abs(raw_delta)>1e-12 else 1.
                    n=len(CONTEXT_NAMES)
                    contributions=dict(language=float(np.dot(x[:6],beta[:6]))*vol*100*scale,
                        seeking_numeric=float(np.dot(x[6:11],beta[6:11]))*vol*100*scale,
                        company_assessment=float(np.dot(x[11:n],beta[11:n]))*vol*100*scale,
                        learned_missingness=float(np.dot(x[n:],beta[n:]))*vol*100*scale)
                    technical=technical_vector(df.iloc[-1])
                    technical_missing=[k for k,v in zip(PRICE_NAMES,technical[1+len(PRICE_NAMES):]) if v]
                    base=float(np.dot(technical,head['beta'])*vol)
                    value=float(np.clip(base+vol*delta,-.95,3.))
                    contributions['bound_guard']=(value-base-vol*delta)*100
                    low,high=[float(np.clip(value+q*vol,-.99,5.))*100 for q in head['residual_band']]
                    low=min(low,value*100);high=max(high,value*100)
                    r.update(status='EXPERIMENTAL_PRICE_FORECAST',reason='PARTIAL_INPUTS' if missing or technical_missing else 'UNVALIDATED',
                        expected_return_pct=value*100,band_low_pct=low,band_high_pct=high,
                        direction='UP' if value>.0025 else ('DOWN' if value<-.0025 else 'NEUTRAL'),
                        technical_return=base,technical_vector=technical,technical_missing_features=technical_missing,
                        technical_weights_sha256=digest(head),context_weights_sha256=digest(a) if a else digest(beta.tolist()),
                        contributions_pct=contributions,
                        horizon_volatility=vol,context_vector=x,missing_features=missing,context_provenance=refs,
                        weights_mode='LEARNED_CONTEXT_EXPERIMENTAL' if a else 'EXPERT_CONTEXT_PRIOR')
            rows.append(r)
    return dict(schema_version='ALPHA_FULL_PRICE_RUN_V1',manifest=MANIFEST,model_name='ALPHA_FULL_PRICE',model_version=VERSION,
                session=session,issued_at=issued,fixture=fixture,qualified=False,rows=rows[:MANIFEST['row_count']],market_rows=rows[MANIFEST['row_count']:],
                technical_heads=heads,context_heads=overlays,source_coverage=dict(available=sorted(frames),blocked=failures),
                label_definition='TERMINAL_CLOSE_T_PLUS_N_PRICE_RETURN_SPLIT_ONLY_EX_DIVIDENDS')
