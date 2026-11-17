"""Risk Forecast technical_combined daily-fit v1: raw research probabilities, separate from frozen HIST/REGIME.
No vendor access in numerical functions. No fitted training prices enter Git/journal.
"""
import math
from pathlib import Path
from datetime import datetime, timezone, timedelta
import numpy as np
import pandas as pd
from research.daily_shadow.core import canonical, sha, utc, calendar, future_sessions
from research.daily_shadow_v3.adapter import normalized_prefix

from .portfolio import SYMBOLS,UNIVERSE_REVISION
HORIZONS=(10,30)
LABELS=('LOW_INTRADAY','EOD_CLOSE')
THRESHOLDS=(5,10,15)
NBIS_START='2024-10-21'
PROTOCOL=Path(__file__).resolve().parents[2]/'reports/risk-forecast-daily-v1/protocol.txt'
CODE_HASH=sha(Path(__file__).read_bytes())
MANIFEST=dict(name='RISK_FORECAST_DAILY_V1',symbols=SYMBOLS,horizons=HORIZONS,labels=LABELS,thresholds=THRESHOLDS,protocol_sha256=sha(PROTOCOL.read_bytes()),universe_revision_sha256=UNIVERSE_REVISION)
MANIFEST_HASH=sha(canonical(MANIFEST).encode())


def series(symbols=SYMBOLS):
    return [dict(symbol=s,label_type=l,threshold_pct=t,horizon=h) for s in symbols for l in LABELS for t in THRESHOLDS for h in HORIZONS]


def cell(row):
    from bisect import bisect_right
    return (bisect_right((5,10,15,25),max(0,-float(row.drawdown_20_pct))),bisect_right((20,40,60,80,120),float(row.rv20_pct)),bool(row.close<row.ma50),bisect_right((30,45,55,70),float(row.rsi14)))


def frame(snapshot,symbol):
    from .vol import frame as source_frame
    df=source_frame(snapshot,symbol)
    c=df.close;df['ma50']=c.rolling(50).mean();df['drawdown_20_pct']=(c/c.shift(1).rolling(20).max()-1).clip(upper=0)*100
    df['rv20_pct']=np.exp(df.log_rv20)*100
    r=np.diff(c.to_numpy());gain=float(np.maximum(r[:14],0).mean()) if len(r)>=14 else 0.;loss=float(np.maximum(-r[:14],0).mean()) if len(r)>=14 else 0.
    values=[float('nan')]*len(df)
    def value():return 50. if gain==loss==0 else (100. if loss==0 else 100-100/(1+gain/loss))
    if len(r)>=14:
        values[14]=value()
        for i in range(14,len(r)):
            gain=(gain*13+max(r[i],0))/14;loss=(loss*13+max(-r[i],0))/14;values[i+1]=value()
    df['rsi14']=values
    df['_cell']=[cell(row) if all(math.isfinite(x) for x in row) else None for row in df[['drawdown_20_pct','rv20_pct','close','ma50','rsi14']].itertuples(index=False)]
    return df


def artifact(df,task,fit_cutoff,created_at,source_hash,*,fixture=False):
    label=task['label_type'];h=task['horizon'];t=task['threshold_pct']
    if label not in LABELS or h not in HORIZONS or t not in THRESHOLDS:raise ValueError('UNSUPPORTED_RISK_FORECAST_TASK')
    if utc(fit_cutoff)>utc(created_at):raise ValueError('FUTURE_FIT_CUTOFF')
    end=int(df.index.searchsorted(utc(fit_cutoff).date().isoformat()));counts={};training=[]
    mark=df['low' if label=='LOW_INTRADAY' else 'close'].to_numpy();close=df.close.to_numpy()
    for i in range(251,max(251,end-2*h)):
        maturity=(pd.Timestamp(df.index[i+h],tz='UTC')+pd.Timedelta(days=1)).isoformat()
        if utc(maturity)>=utc(fit_cutoff):continue
        key=df['_cell'].iloc[i];hit=int(mark[i+1:i+h+1].min()<=close[i]*(1-t/100)+close[i]*1e-12)
        entry=counts.setdefault(canonical(key),[0,0,set()]);entry[0]+=1;entry[1]+=hit;entry[2].add(i//40)
        training.append((str(df.index[i]),key,hit,maturity))
    n=len(training);hits=sum(r[2] for r in training);reason='INSUFFICIENT_MATURE_TRAINING_SUPPORT' if n<252 else ('INSUFFICIENT_EVENT_CLASS_SUPPORT' if min(hits,n-hits)<10 else None)
    bank={k:[v[0],v[1],len(v[2])] for k,v in counts.items()}
    result=dict(name='RISK_FORECAST',series=task,fit_cutoff=fit_cutoff,created_at=created_at,qualified=False,calibrated=False,fixture=fixture,training_source_qualified=False,training_status='TRAINING_REPLAY_NOT_PIT',protocol_sha256=MANIFEST['protocol_sha256'],universe_sha256=MANIFEST_HASH,code_sha256=CODE_HASH,source_hash=source_hash,n=n,hits=hits,first_anchor=training[0][0] if n else None,last_anchor=training[-1][0] if n else None,last_maturity=training[-1][3] if n else None,training_rows_sha256=sha(canonical(training).encode()),count_cells=bank,unavailable=reason is not None,reason=reason,estimator='RISK_FORECAST_V1_TECHNICAL_COMBINED_DAILY_REFIT',source_sha='366f8cd00e8c228d4796d0abbe9997f717a3b6ad',supported_tasks=[f'{label}:{t}:{h}'])
    result['version']='rf-daily-v1-'+sha(canonical(result).encode());return result


def unavailable(task,created_at,reason):
    obj=dict(name='RISK_FORECAST',series=task,fit_cutoff=created_at,created_at=created_at,qualified=False,calibrated=False,fixture=False,unavailable=True,reason=reason,code_sha256=CODE_HASH,universe_sha256=MANIFEST_HASH)
    obj['version']='rf-daily-v1-'+sha(canonical(obj).encode());return obj


def diagnostics(model,feature):
    n,pos,blocks=model.get('count_cells',{}).get(canonical(feature),(0,0,0))
    return dict(cell_n=n,cell_positive=pos,cell_negative=n-pos,cell_blocks=blocks,backoff=n==0,status='SUPPORTED_RESEARCH_ESTIMATE' if n>=60 and pos>=10 and n-pos>=10 and blocks>=5 else 'LOW_SUPPORT')


def probability(model,feature,issued):
    if utc(model['created_at'])>utc(issued) or utc(model['fit_cutoff'])>utc(issued):return None,'MODEL_NOT_AVAILABLE_ASOF'
    if model.get('unavailable'):return None,model['reason']
    if not model.get('last_maturity') or utc(model['last_maturity'])>=utc(model['fit_cutoff']):return None,'UNMATURED_TRAINING_LABEL'
    if not isinstance(feature,tuple) or len(feature)!=4:return None,'INVALID_CURRENT_TECHNICAL_CELL'
    d=diagnostics(model,feature);base=(model['hits']+1)/(model['n']+2)
    return (d['cell_positive']+20*base)/(d['cell_n']+20),None


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
                try:feature=cell(frame(snapshot,symbol).iloc[-1])
                except ValueError as exc:why=str(exc)
        p=None
        if why is None:p,why=probability(m,feature,issued)
        result.append(dict(**s,model_name='RISK_FORECAST',model_version=m['version'],model_hash=sha(canonical(m).encode()),session=session,decision_at=issued,issued_at=issued,horizon_end_at=end,status='STATUS_BLOCKED' if why else 'RESEARCH_FORECAST',reason=why,model_status='MODEL_NOT_VALIDATED',training_status='TRAINING_REPLAY_NOT_PIT',data_status='REVIEWED_INPUTS' if reviewed else 'UNQUALIFIED',probability_raw=p,probability_calibrated=None,calendar='XNYS_exchange_calendars_4.11.2',label_definition='NEXT_N_TRADING_SESSION_TOUCH_FROM_FROZEN_ANCHOR;SPLIT_ONLY_PRICE',source_publication_at=snapshot.publication_at if snapshot else None,source_retrieved_at=snapshot.retrieved_at if snapshot else None))
    for r,m in zip(result,models):
        if r['status']=='RESEARCH_FORECAST':
            d=diagnostics(m,cell(frame(snapshot,m['series']['symbol']).iloc[-1]))
            if d['status']=='LOW_SUPPORT':r['reason']='LOW_SUPPORT'
    return result
