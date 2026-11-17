"""VOL daily-fit v1: raw research probabilities, separate from frozen HIST/REGIME.
No vendor access in numerical functions. No fitted training prices enter Git/journal.
"""
import math
from pathlib import Path
from datetime import datetime, timezone, timedelta
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from research.daily_shadow.core import canonical, sha, utc, calendar, future_sessions
from research.daily_shadow_v3.adapter import normalized_prefix

from .portfolio import SYMBOLS,UNIVERSE_REVISION
HORIZONS=(10,30)
LABELS=('LOW_INTRADAY','EOD_CLOSE')
THRESHOLDS=(5,10,15)
NBIS_START='2024-10-21'
PROTOCOL=Path(__file__).resolve().parents[2]/'reports/vol-daily-v1/protocol.txt'
CODE_HASH=sha(Path(__file__).read_bytes())
MANIFEST=dict(name='VOL_DAILY_V1',symbols=SYMBOLS,horizons=HORIZONS,labels=LABELS,thresholds=THRESHOLDS,protocol_sha256=sha(PROTOCOL.read_bytes()),universe_revision_sha256=UNIVERSE_REVISION)
MANIFEST_HASH=sha(canonical(MANIFEST).encode())


def series(symbols=SYMBOLS):
    return [dict(symbol=s,label_type=l,threshold_pct=t,horizon=h) for s in symbols for l in LABELS for t in THRESHOLDS for h in HORIZONS]


def frame(snapshot,symbol):
    rows=normalized_prefix(snapshot.bars.get(symbol,[]),snapshot.splits.get(symbol,[]),snapshot.session)
    if symbol=='NBIS':rows=[r for r in rows if r['date']>=NBIS_START]
    if not rows:raise ValueError('NO_PRICE_HISTORY')
    if [r['date'] for r in rows]!=sorted({r['date'] for r in rows}):raise ValueError('DUPLICATE_OR_UNORDERED_SESSION')
    df=pd.DataFrame(rows).set_index('date')
    if df.index[-1]!=snapshot.session:raise ValueError('STALE_SOURCE_SESSION')
    expected=calendar().sessions_in_range(df.index[0],snapshot.session).strftime('%Y-%m-%d').tolist()
    if list(df.index)!=expected:raise ValueError('HISTORY_CALENDAR_GAP')
    if np.any(~np.isfinite(df[['close','low']].to_numpy())) or np.any(df[['close','low']].to_numpy()<=0):raise ValueError('INVALID_MARK')
    df['log_rv20']=np.log(np.log(df.close).diff().rolling(20).std(ddof=1)*np.sqrt(252))
    return df


def artifact(df,task,fit_cutoff,created_at,source_hash,*,fixture=False):
    """Only full-horizon matured targets; extra horizon anchor purge before cutoff.
    Current revised source history is explicitly NOT an original PIT archive.
    """
    label=task['label_type'];h=task['horizon'];t=task['threshold_pct']
    if label not in LABELS or h not in HORIZONS or t not in THRESHOLDS:raise ValueError('UNSUPPORTED_VOL_TASK')
    if utc(fit_cutoff)>utc(created_at):raise ValueError('FUTURE_FIT_CUTOFF')
    end=int(df.index.searchsorted(utc(fit_cutoff).date().isoformat()))
    x=[];y=[];anchors=[];maturities=[]
    for i in range(251,max(251,end-2*h)):
        last=i+h
        maturity=(pd.Timestamp(df.index[last],tz='UTC')+pd.Timedelta(days=1)).isoformat()
        if utc(maturity)>=utc(fit_cutoff) or not math.isfinite(float(df.iloc[i].log_rv20)):continue
        a=float(df.iloc[i].close);key='low' if label=='LOW_INTRADAY' else 'close'
        value=float(df.iloc[i+1:last+1][key].min())
        x.append(float(df.iloc[i].log_rv20));y.append(int(value<=a*(1-t/100)+a*1e-12));anchors.append(df.index[i]);maturities.append(maturity)
    n=len(y);hits=sum(y);reason=None
    if n<252:reason='INSUFFICIENT_MATURE_TRAINING_SUPPORT'
    elif min(hits,n-hits)<10:reason='INSUFFICIENT_EVENT_CLASS_SUPPORT'
    params=None
    if reason is None:
        a=np.array(x);target=np.array(y);mu=float(a.mean());scale=float(a.std());scale=scale if scale>=1e-12 else 1.
        model=LogisticRegression(C=.1,max_iter=2000,tol=1e-9).fit(((a-mu)/scale).reshape(-1,1),target)
        if model.n_iter_[0]>=2000:reason='VOL_FIT_DID_NOT_CONVERGE'
        else:params=dict(mean=mu,scale=scale,coef=float(model.coef_[0,0]),intercept=float(model.intercept_[0]))
    result=dict(name='VOL',series=task,fit_cutoff=fit_cutoff,created_at=created_at,qualified=False,calibrated=False,fixture=fixture,training_source_qualified=False,training_status='TRAINING_REPLAY_NOT_PIT',protocol_sha256=MANIFEST['protocol_sha256'],universe_sha256=MANIFEST_HASH,code_sha256=CODE_HASH,source_hash=source_hash,n=n,hits=hits,first_anchor=anchors[0] if n else None,last_anchor=anchors[-1] if n else None,last_maturity=maturities[-1] if n else None,training_rows_sha256=sha(canonical(list(zip(anchors,x,y,maturities))).encode()),params=params,unavailable=reason is not None,reason=reason,estimator='DAILY_REFIT_RAW_LOG_RV20_L2_C0.1_NO_CALIBRATION',supported_tasks=[f'{label}:{t}:{h}'])
    result['version']='vol-v1-'+sha(canonical(result).encode())
    return result


def unavailable(task,created_at,reason):
    obj=dict(name='VOL',series=task,fit_cutoff=created_at,created_at=created_at,qualified=False,calibrated=False,fixture=False,unavailable=True,reason=reason,code_sha256=CODE_HASH,universe_sha256=MANIFEST_HASH)
    obj['version']='vol-v1-'+sha(canonical(obj).encode());return obj


def probability(model,feature,issued):
    if utc(model['created_at'])>utc(issued) or utc(model['fit_cutoff'])>utc(issued):return None,'MODEL_NOT_AVAILABLE_ASOF'
    if model.get('unavailable'):return None,model['reason']
    if not model.get('last_maturity') or utc(model['last_maturity'])>=utc(model['fit_cutoff']):return None,'UNMATURED_TRAINING_LABEL'
    if not math.isfinite(feature):return None,'NONFINITE_CURRENT_VOLATILITY'
    p=model['params'];z=(feature-p['mean'])/p['scale']*p['coef']+p['intercept']
    value=math.exp(-math.log1p(math.exp(-z))) if z>=0 else math.exp(z)/(1+math.exp(z))
    return value,None


def rows(session,issued,snapshot,models,permit,*,reviewed=False,reason=None):
    from research.daily_shadow_v3.adapter import issuance_gate
    result=[]
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
                try:feature=float(frame(snapshot,symbol).iloc[-1].log_rv20)
                except ValueError as exc:why=str(exc)
        p=None
        if why is None:p,why=probability(m,feature,issued)
        result.append(dict(**s,model_name='VOL',model_version=m['version'],model_hash=sha(canonical(m).encode()),session=session,decision_at=issued,issued_at=issued,horizon_end_at=end,status='STATUS_BLOCKED' if why else 'RESEARCH_FORECAST',reason=why,model_status='MODEL_NOT_VALIDATED',training_status='TRAINING_REPLAY_NOT_PIT',data_status='REVIEWED_INPUTS' if reviewed else 'UNQUALIFIED',probability_raw=p,probability_calibrated=None,calendar='XNYS_exchange_calendars_4.11.2',label_definition='NEXT_N_TRADING_SESSION_TOUCH_FROM_FROZEN_ANCHOR;SPLIT_ONLY_PRICE',source_publication_at=snapshot.publication_at if snapshot else None,source_retrieved_at=snapshot.retrieved_at if snapshot else None))
    return result
