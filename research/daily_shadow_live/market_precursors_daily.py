"""Market Drawdown Precursors raw daily v1: raw research probabilities, separate from frozen HIST/REGIME.
No vendor access in numerical functions. No fitted training prices enter Git/journal.
"""
import math
from pathlib import Path
from datetime import datetime, timezone, timedelta
import numpy as np
import pandas as pd
from scipy.special import expit
from .market_precursors_reference import feature_frame,fit_raw
from research.daily_shadow.core import canonical, sha, utc, calendar, future_sessions
from research.daily_shadow_v3.adapter import normalized_prefix

from .portfolio import SYMBOLS as STOCKS,UNIVERSE_REVISION
MARKET=('SPY','QQQ','SOXX')
SYMBOLS=STOCKS+MARKET
HORIZONS=(10,30)
LABELS=('LOW_INTRADAY','EOD_CLOSE')
THRESHOLDS=(5,10,15)
NBIS_START='2024-10-21'
PROTOCOL=Path(__file__).resolve().parents[2]/'reports/market-precursors-daily-v1/protocol.txt'
CODE_HASH=sha(Path(__file__).read_bytes())
MANIFEST=dict(name='MARKET_PRECURSORS_RAW_DAILY_V1',symbols=SYMBOLS,horizons=HORIZONS,labels=LABELS,thresholds=THRESHOLDS,protocol_sha256=sha(PROTOCOL.read_bytes()),universe_revision_sha256=UNIVERSE_REVISION)
MANIFEST_HASH=sha(canonical(MANIFEST).encode())


def series(symbols=SYMBOLS):
    return [dict(symbol=s,label_type=l,threshold_pct=t,horizon=h) for s in symbols for l in LABELS for t in THRESHOLDS for h in HORIZONS]


BASE_KEYS=('log_rv20','qqq_ma200','qqq_r20','spy_ma200','spy_r20')
M_KEYS=('qqq_spy_relative20','qqq_vol_ratio','spy_vol_ratio')
S_KEYS=('sector_relative20','sector_vol_ratio')
X_KEYS=('own_ma50','own_r60','stock_relative20','own_vol_ratio')

def keys(symbol):return BASE_KEYS+M_KEYS+S_KEYS+(X_KEYS if symbol in STOCKS else ())

def required(symbol):return tuple(dict.fromkeys((symbol,)+MARKET))

def frame(snapshot,symbol):
    from .vol import frame as prices
    if any(s not in snapshot.bars or snapshot.currency.get(s)!='USD' for s in required(symbol)):raise ValueError('REQUIRED_MARKET_INPUT_UNAVAILABLE')
    bars={s:prices(snapshot,s) for s in required(symbol)};f={s:feature_frame(df) for s,df in bars.items()};own=f[symbol];q=f['QQQ'].reindex(own.index);p=f['SPY'].reindex(own.index);sec=f['SOXX'].reindex(own.index)
    df=bars[symbol].copy()
    values=dict(log_rv20=np.log(own.rv20),qqq_ma200=q.ma200,qqq_r20=q.r20,spy_ma200=p.ma200,spy_r20=p.r20,qqq_spy_relative20=q.r20-p.r20,qqq_vol_ratio=q.vol_ratio,spy_vol_ratio=p.vol_ratio,sector_relative20=sec.r20-q.r20,sector_vol_ratio=sec.vol_ratio,own_ma50=own.ma50,own_r60=own.r60,stock_relative20=own.r20-q.r20,own_vol_ratio=own.vol_ratio)
    for k,v in values.items():df[k]=v
    eligible=(own.warm==True)&(sec.warm==True)&np.isfinite(df[list(values)].to_numpy()).all(axis=1)
    df['_eligible']=eligible
    if not bool(eligible.iloc[-1]):raise ValueError('INSUFFICIENT_REQUIRED_FEATURE_HISTORY')
    return df


def artifact(df,task,fit_cutoff,created_at,source_hash,*,fixture=False):
    """Only full-horizon matured targets; extra horizon anchor purge before cutoff.
    Current revised source history is explicitly NOT an original PIT archive.
    """
    label=task['label_type'];h=task['horizon'];t=task['threshold_pct']
    if label not in LABELS or h not in HORIZONS or t not in THRESHOLDS:raise ValueError('UNSUPPORTED_MDP_TASK')
    if task['symbol'] not in SYMBOLS:raise ValueError('UNSUPPORTED_MDP_SYMBOL')
    feature_keys=keys(task['symbol'])
    if utc(fit_cutoff)>utc(created_at):raise ValueError('FUTURE_FIT_CUTOFF')
    end=int(df.index.searchsorted(utc(fit_cutoff).date().isoformat()))
    x=[];y=[];anchors=[];maturities=[]
    vector=df[list(feature_keys)].to_numpy();eligible=df['_eligible'].to_numpy();close=df.close.to_numpy();mark=df['low' if label=='LOW_INTRADAY' else 'close'].to_numpy()
    for i in range(251,max(251,end-2*h)):
        last=i+h
        maturity=(pd.Timestamp(df.index[last],tz='UTC')+pd.Timedelta(days=1)).isoformat()
        if utc(maturity)>=utc(fit_cutoff) or not bool(eligible[i]):continue
        a=float(close[i]);value=float(mark[i+1:last+1].min())
        x.append(vector[i].tolist());y.append(int(value<=a*(1-t/100)+a*1e-12));anchors.append(df.index[i]);maturities.append(maturity)
    n=len(y);hits=sum(y);reason=None
    if n<252:reason='INSUFFICIENT_MATURE_TRAINING_SUPPORT'
    elif min(hits,n-hits)<10:reason='INSUFFICIENT_EVENT_CLASS_SUPPORT'
    params=None
    if reason is None:
        try:params=fit_raw(np.array(x),np.array(y))
        except ValueError as exc:
            if str(exc)!='MDP_FIT_DID_NOT_CONVERGE':raise
            reason=str(exc)
    result=dict(name='MARKET_PRECURSORS',series=task,fit_cutoff=fit_cutoff,created_at=created_at,qualified=False,calibrated=False,fixture=fixture,training_source_qualified=False,training_status='TRAINING_REPLAY_NOT_PIT',protocol_sha256=MANIFEST['protocol_sha256'],universe_sha256=MANIFEST_HASH,code_sha256=CODE_HASH,source_hash=source_hash,n=n,hits=hits,first_anchor=anchors[0] if n else None,last_anchor=anchors[-1] if n else None,last_maturity=maturities[-1] if n else None,training_rows_sha256=sha(canonical(list(zip(anchors,x,y,maturities))).encode()),params=params,feature_keys=feature_keys,feature_family='PLUS_X' if task['symbol'] in STOCKS else 'MINIMAL',source_sha='8e9aec99c7eee8b384e35a3bc1aa734f2d54800d',unavailable=reason is not None,reason=reason,estimator='DAILY_REFIT_RAW_ORIGINAL_MDP_FEATURE_FAMILY_L2_C0.1_NO_ANNUAL_INTERCEPT_CALIBRATION',supported_tasks=[f'{label}:{t}:{h}'])
    result['version']='mdp-daily-v1-'+sha(canonical(result).encode())
    return result


def unavailable(task,created_at,reason):
    obj=dict(name='MARKET_PRECURSORS',series=task,fit_cutoff=created_at,created_at=created_at,qualified=False,calibrated=False,fixture=False,unavailable=True,reason=reason,code_sha256=CODE_HASH,universe_sha256=MANIFEST_HASH)
    obj['version']='mdp-daily-v1-'+sha(canonical(obj).encode());return obj


def probability(model,feature,issued):
    if utc(model['created_at'])>utc(issued) or utc(model['fit_cutoff'])>utc(issued):return None,'MODEL_NOT_AVAILABLE_ASOF'
    if model.get('unavailable'):return None,model['reason']
    if not model.get('last_maturity') or utc(model['last_maturity'])>=utc(model['fit_cutoff']):return None,'UNMATURED_TRAINING_LABEL'
    value=np.asarray(feature,dtype=float)
    if value.shape!=(len(model['feature_keys']),) or not np.isfinite(value).all():return None,'NONFINITE_OR_MISMATCHED_CURRENT_FEATURES'
    p=model['params'];z=(value-np.asarray(p['mean']))/np.asarray(p['scale'])@np.asarray(p['coef'])+p['intercept']
    return float(expit(z)),None


def rows(session,issued,snapshot,models,permit,*,reviewed=False,reason=None):
    from research.daily_shadow_v3.adapter import issuance_gate
    result=[];cache={}
    def current(symbol):
        if symbol not in cache:
            row=frame(snapshot,symbol).iloc[-1];cache[symbol]=[float(row[k]) for k in keys(symbol)]
        return cache[symbol]
    for m in models:
        s=m['series'];symbol=s['symbol'];end=calendar().session_close(pd.Timestamp(future_sessions(session,s['horizon'])[-1])).isoformat()
        why=reason or issuance_gate(session,issued,permit) or permit.reason(issued,fixture=bool(snapshot and snapshot.fixture),horizon_end=(utc(end)+timedelta(days=1)).isoformat())
        feature=None
        if why is None:
            if snapshot is None:why='MISSING_SOURCE'
            elif snapshot.legal_reason:why=snapshot.legal_reason
            elif not reviewed:why='DATA_ACTION_BASIS_NOT_REVIEWED'
            elif snapshot.basis!='RAW_AS_TRADED_OHLC; VOLUME_SPLIT_ADJUSTED; ADJUSTED_CLOSE_TOTAL_RETURN':why='UNSUPPORTED_SOURCE_BASIS'
            elif snapshot.session!=session or snapshot.currency.get(symbol)!='USD':why='STALE_OR_MIXED_SESSION_INPUT'
            elif not snapshot.retrieved_at or utc(snapshot.retrieved_at)>utc(issued):why='FUTURE_SOURCE_RETRIEVAL'
            elif snapshot.publication_at and utc(snapshot.publication_at)>utc(snapshot.retrieved_at):why='FUTURE_SOURCE_PUBLICATION'
            else:
                try:feature=current(symbol)
                except ValueError as exc:why=str(exc)
        p=None
        if why is None:p,why=probability(m,feature,issued)
        result.append(dict(**s,model_name='MARKET_PRECURSORS',model_version=m['version'],model_hash=sha(canonical(m).encode()),session=session,decision_at=issued,issued_at=issued,horizon_end_at=end,status='STATUS_BLOCKED' if why else 'RESEARCH_FORECAST',reason=why,model_status='MODEL_NOT_VALIDATED',training_status='TRAINING_REPLAY_NOT_PIT',data_status='REVIEWED_INPUTS' if reviewed else 'UNQUALIFIED',probability_raw=p,probability_calibrated=None,calendar='XNYS_exchange_calendars_4.11.2',label_definition='NEXT_N_TRADING_SESSION_TOUCH_FROM_FROZEN_ANCHOR;SPLIT_ONLY_PRICE',source_publication_at=snapshot.publication_at if snapshot else None,source_retrieved_at=snapshot.retrieved_at if snapshot else None))
    return result
