"""Ensemble B five-component daily-fit v1: raw research probabilities, separate from frozen HIST/REGIME.
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
PROTOCOL=Path(__file__).resolve().parents[2]/'reports/ensemble-daily-v1/protocol.txt'
CODE_HASH=sha(Path(__file__).read_bytes())
MANIFEST=dict(name='ENSEMBLE_RISK_DAILY_B_V1',symbols=SYMBOLS,horizons=HORIZONS,labels=LABELS,thresholds=THRESHOLDS,protocol_sha256=sha(PROTOCOL.read_bytes()),universe_revision_sha256=UNIVERSE_REVISION)
MANIFEST_HASH=sha(canonical(MANIFEST).encode())


def series(symbols=SYMBOLS):
    return [dict(symbol=s,label_type=l,threshold_pct=t,horizon=h) for s in symbols for l in LABELS for t in THRESHOLDS for h in HORIZONS]


COMPONENTS=('technical_combined','v3_state','technical_plus_v3','volatility','regime')


def cell(row):return row['_ensemble_cells']


def frame(snapshot,symbol):
    from .risk_forecast_daily import frame as technical_frame
    from .vol import frame as price_frame
    from .frozen_v3 import evaluate,catalogue
    from bisect import bisect_right
    if 'QQQ' not in snapshot.bars:raise ValueError('REQUIRED_QQQ_UNAVAILABLE')
    df=technical_frame(snapshot,symbol);q=price_frame(snapshot,'QQQ');c=df.close
    df['ma20']=c.rolling(20).mean();df['ma200']=c.rolling(200).mean()
    df['drawdown_60_pct']=(c/c.shift(1).rolling(60).max()-1).clip(upper=0)*100
    for h in (5,10,20):df['return_'+str(h)+'_pct']=(c/c.shift(h)-1)*100
    df['fall_acceleration_5_pp']=df.return_5_pct-df.return_5_pct.shift(5)
    for h in (20,50):
        ma=df['ma'+str(h)];df['ma'+str(h)+'_slope_5_pct']=(ma/ma.shift(5)-1)*100;df['ma'+str(h)+'_slope_change_pp']=df['ma'+str(h)+'_slope_5_pct']-df['ma'+str(h)+'_slope_5_pct'].shift(5)
    df['rv60_pct']=np.log(c).diff().rolling(60).std(ddof=1)*np.sqrt(252)*100
    df['rv20_change_5_ratio']=df.rv20_pct/df.rv20_pct.shift(5)-1
    qr=(q.close/q.close.shift(20)-1)*100
    df['relative_return_qqq20_pp']=df.return_20_pct-qr.reindex(df.index)
    regimes=pd.Series(np.where((q.close>=q.close.rolling(200).mean())&(qr>0),'UP',np.where((q.close<q.close.rolling(200).mean())&(qr<=0),'DOWN','MIXED')),index=q.index).reindex(df.index)
    from .frozen_v3 import REQUIRED
    keys=list(REQUIRED)+['rv20_change_5_ratio'];out=[];config=catalogue()[0]
    for index,(date,row) in enumerate(df.iterrows()):
        if index<251 or any(not math.isfinite(float(row[k])) for k in keys):out.append(None);continue
        if pd.isna(regimes.loc[date]):raise ValueError('REQUIRED_QQQ_UNAVAILABLE')
        indicators={k:float(row[k]) for k in keys};indicators.update(vix=None,relative_return_sox20_pp=None,support=None)
        observed=calendar().session_close(pd.Timestamp(date)).isoformat();available=snapshot.retrieved_at if date==snapshot.session else (pd.Timestamp(date,tz='UTC')+pd.Timedelta(days=1)).isoformat()
        quality=dict(quote_observed_at=observed,quote_available_at=available,qqq_observed_at=observed,qqq_available_at=available,publication_vintage_verified=False)
        signal=evaluate(symbol,available,indicators,quality,variant='C',config=config)
        if signal['data_status']!='OK':out.append(None);continue
        technical=tuple(row['_cell']);state=signal['risk_level'];score=bisect_right((3,5,7,9),signal['score'])
        out.append(dict(technical_combined=technical,v3_state=(state,),technical_plus_v3=(*technical,state,score),volatility=(technical[1],),regime=(str(regimes.loc[date]),)))
    df['_ensemble_cells']=out
    if out[-1] is None:raise ValueError('REQUIRED_V3_FEATURES_UNAVAILABLE')
    return df


def artifact(df,task,fit_cutoff,created_at,source_hash,*,fixture=False):
    label=task['label_type'];h=task['horizon'];t=task['threshold_pct']
    if label not in LABELS or h not in HORIZONS or t not in THRESHOLDS:raise ValueError('UNSUPPORTED_ENSEMBLE_TASK')
    if utc(fit_cutoff)>utc(created_at):raise ValueError('FUTURE_FIT_CUTOFF')
    end=int(df.index.searchsorted(utc(fit_cutoff).date().isoformat()));counts={name:{} for name in COMPONENTS};training=[]
    mark=df['low' if label=='LOW_INTRADAY' else 'close'].to_numpy();close=df.close.to_numpy();features=df['_ensemble_cells'].tolist()
    for i in range(251,max(251,end-2*h)):
        maturity=(pd.Timestamp(df.index[i+h],tz='UTC')+pd.Timedelta(days=1)).isoformat()
        if utc(maturity)>=utc(fit_cutoff) or features[i] is None:continue
        hit=int(mark[i+1:i+h+1].min()<=close[i]*(1-t/100)+close[i]*1e-12)
        for name in COMPONENTS:
            entry=counts[name].setdefault(canonical(features[i][name]),[0,0,set()]);entry[0]+=1;entry[1]+=hit;entry[2].add(i//40)
        training.append((str(df.index[i]),features[i],hit,maturity))
    n=len(training);hits=sum(r[2] for r in training);reason='INSUFFICIENT_MATURE_TRAINING_SUPPORT' if n<252 else ('INSUFFICIENT_EVENT_CLASS_SUPPORT' if min(hits,n-hits)<10 else None)
    bank={name:{k:[v[0],v[1],len(v[2])] for k,v in cells.items()} for name,cells in counts.items()}
    result=dict(name='ENSEMBLE_RISK',series=task,fit_cutoff=fit_cutoff,created_at=created_at,qualified=False,calibrated=False,fixture=fixture,training_source_qualified=False,training_status='TRAINING_REPLAY_NOT_PIT',protocol_sha256=MANIFEST['protocol_sha256'],universe_sha256=MANIFEST_HASH,code_sha256=CODE_HASH,source_hash=source_hash,n=n,hits=hits,first_anchor=training[0][0] if n else None,last_anchor=training[-1][0] if n else None,last_maturity=training[-1][3] if n else None,training_rows_sha256=sha(canonical(training).encode()),component_banks=bank,unavailable=reason is not None,reason=reason,estimator='ENSEMBLE_B_MEAN_FIVE_ORIGINAL_COMPONENTS_DAILY_V1',source_sha='366f8cd00e8c228d4796d0abbe9997f717a3b6ad',v3_profile='C_sensitive',optional_inputs_unavailable=['VIX','SOX','SUPPORT'],supported_tasks=[f'{label}:{t}:{h}'])
    result['version']='ensemble-b-daily-v1-'+sha(canonical(result).encode());return result


def unavailable(task,created_at,reason):
    obj=dict(name='ENSEMBLE_RISK',series=task,fit_cutoff=created_at,created_at=created_at,qualified=False,calibrated=False,fixture=False,unavailable=True,reason=reason,code_sha256=CODE_HASH,universe_sha256=MANIFEST_HASH)
    obj['version']='ensemble-b-daily-v1-'+sha(canonical(obj).encode());return obj


def component_predictions(model,feature):
    if not isinstance(feature,dict) or set(feature)!=set(COMPONENTS) or set(model.get('component_banks',{}))!=set(COMPONENTS):raise ValueError('FIVE_COMPONENTS_REQUIRED')
    base=(model['hits']+1)/(model['n']+2);out={}
    for name in COMPONENTS:
        n,pos,blocks=model['component_banks'][name].get(canonical(feature[name]),(0,0,0))
        parent=out['technical_combined']['probability'] if name=='technical_plus_v3' else base
        out[name]=dict(probability=(pos+20*parent)/(n+20),cell_n=n,cell_positive=pos,cell_blocks=blocks,backoff=n==0,status='SUPPORTED_RESEARCH_ESTIMATE' if n>=60 and min(pos,n-pos)>=10 and blocks>=5 else 'LOW_SUPPORT')
    return out


def diagnostics(model,feature):
    values=component_predictions(model,feature)
    return dict(status='LOW_SUPPORT' if any(p['status']=='LOW_SUPPORT' for p in values.values()) else 'SUPPORTED_RESEARCH_ESTIMATE',components=values)


def probability(model,feature,issued):
    if utc(model['created_at'])>utc(issued) or utc(model['fit_cutoff'])>utc(issued):return None,'MODEL_NOT_AVAILABLE_ASOF'
    if model.get('unavailable'):return None,model['reason']
    if not model.get('last_maturity') or utc(model['last_maturity'])>=utc(model['fit_cutoff']):return None,'UNMATURED_TRAINING_LABEL'
    values=component_predictions(model,feature)
    return float(np.mean([values[name]['probability'] for name in COMPONENTS])),None


def rows(session,issued,snapshot,models,permit,*,reviewed=False,reason=None):
    cache={}
    def current(symbol):
        if symbol not in cache:cache[symbol]=cell(frame(snapshot,symbol).iloc[-1])
        return cache[symbol]
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
                try:feature=current(symbol)
                except ValueError as exc:why=str(exc)
        p=None
        if why is None:p,why=probability(m,feature,issued)
        result.append(dict(**s,model_name='ENSEMBLE_RISK',model_version=m['version'],model_hash=sha(canonical(m).encode()),session=session,decision_at=issued,issued_at=issued,horizon_end_at=end,status='STATUS_BLOCKED' if why else 'RESEARCH_FORECAST',reason=why,model_status='MODEL_NOT_VALIDATED',training_status='TRAINING_REPLAY_NOT_PIT',data_status='REVIEWED_INPUTS' if reviewed else 'UNQUALIFIED',probability_raw=p,probability_calibrated=None,calendar='XNYS_exchange_calendars_4.11.2',label_definition='NEXT_N_TRADING_SESSION_TOUCH_FROM_FROZEN_ANCHOR;SPLIT_ONLY_PRICE',source_publication_at=snapshot.publication_at if snapshot else None,source_retrieved_at=snapshot.retrieved_at if snapshot else None))
    for r,m in zip(result,models):
        if r['status']=='RESEARCH_FORECAST':
            d=diagnostics(m,current(m['series']['symbol']))
            if d['status']=='LOW_SUPPORT':r['reason']='LOW_SUPPORT'
    return result
