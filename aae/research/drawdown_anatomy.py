"""Causal research features and separate, nested-free retrospective event labels."""
from bisect import bisect_right
from datetime import timedelta
from math import log,sqrt,isfinite
from statistics import mean,stdev
import numpy as np
from aae.backtest.simulator import utc
from .risk_v3_features import wilder_rsi

SEMIS=('AMD','NVDA','MU','AVGO','AMAT','LRCX','TSM','MRVL','INTC','QCOM','TXN')
PRIMARY=('AMD','NVDA','MU')
EXTRA=('AVGO','AMAT','LRCX','TSM','MRVL','INTC','QCOM','TXN','AMZN','META','MSFT','GOOGL','PLTR','CRM','ADBE')
OFFSETS=(60,40,20,10,5)


def catalogue(bars,start='2021-01-01',end='2026-10-22',*,minimum=.10,recovery=1.0,extrema='close'):
    """Single high-water episode until recovered; peaks/troughs are labels only."""
    bars=sorted([b for b in bars if b.close_at.date().isoformat()<=end],key=lambda b:b.close_at)
    if not bars:return []
    if extrema not in ('close','high_low') or not 0<minimum<1 or not .9<=recovery<=1:
        raise ValueError('Invalid episode definition')
    if len({b.close_at.date() for b in bars})!=len(bars):raise ValueError('Duplicate sessions')
    output=[];peak=0;onset=None;trough=0;crossings={}
    def high(i):return bars[i].close if extrema=='close' else bars[i].high
    def low(i):return bars[i].close if extrema=='close' else bars[i].low
    def emit(last,restored):
        depth=1-low(trough)/high(peak)
        if depth+1e-12<minimum or bars[last].close_at.date().isoformat()<start:return
        date=lambda i:bars[i].close_at.date().isoformat()
        output.append(dict(symbol=bars[0].symbol,episode_id=bars[0].symbol+'-'+date(peak),
            peak_date=date(peak),peak_price=high(peak),onset_date=date(onset),
            trough_date=date(trough),minimum_price=low(trough),depth_pct=depth*100,
            severity='10-15' if depth<.15-1e-12 else '15-25' if depth<=.25+1e-12 else '>25',
            decline_sessions=trough-onset+1,underwater_sessions=last-peak,
            recovery_date=date(last) if restored else None,event_end=date(last),
            status='RECOVERED' if restored else 'OPEN_AT_CUTOFF',left_censored=date(onset)<start,
            observed_history_start=date(0),lifetime_ath_verified=False,
            peak_index=peak,onset_index=onset,trough_index=trough,end_index=last,
            extrema=extrema,recovery_fraction=recovery,minimum_fraction=minimum,
            **{f'minus_{n}_date':date(crossings[n]) if n in crossings else None for n in (5,10,15,20)}))
    for i in range(1,len(bars)):
        if onset is None:
            if high(i)>=high(peak):peak=i;continue
            onset=i;trough=i;crossings={}
        elif bars[i].close>=high(peak)*recovery:
            if low(i)<low(trough):trough=i
            for n in (5,10,15,20):
                if n not in crossings and low(i)<=high(peak)*(1-n/100)+high(peak)*1e-12:crossings[n]=i
            emit(i,True);peak=i;onset=None;crossings={};continue
        if low(i)<low(trough):trough=i
        for n in (5,10,15,20):
            if n not in crossings and low(i)<=high(peak)*(1-n/100)+high(peak)*1e-12:crossings[n]=i
    if onset is not None:emit(len(bars)-1,False)
    return output


def _ret(closes,n):return (closes[-1]/closes[-n-1]-1)*100 if len(closes)>n else None

def _rv(closes,n):
    if len(closes)<=n:return None
    r=[log(b/a) for a,b in zip(closes[-n-1:],closes[-n:])]
    return stdev(r)*sqrt(252)*100


def _corr(a,b):
    if len(a)!=len(b) or len(a)<3 or np.std(a)==0 or np.std(b)==0:return None
    return float(np.corrcoef(a,b)[0,1])


def build_features(stock,volumes,qqq,sox,vix=(),rates=()):
    """All inputs explicitly publication-gated; no catalogue arguments accepted."""
    stock=sorted(stock,key=lambda b:b.close_at)
    if len({b.close_at.date() for b in stock})!=len(stock) or any(a.available_at>=b.available_at for a,b in zip(stock,stock[1:])):
        raise ValueError('Nonmonotone/duplicate stock publications')
    lookup={name:{b.close_at.date():b for b in series} for name,series in (('qqq',qqq),('sox',sox))}
    market_sorted={name:sorted(series,key=lambda b:b.close_at) for name,series in (('qqq',qqq),('sox',sox))}
    vix=sorted(vix,key=lambda x:x.available_at);rates=sorted(rates,key=lambda x:x['available_at'])
    vix_times=[o.available_at for o in vix];rate_times=[utc(r['available_at']) for r in rates]
    output=[];confirmed=[];ma_history={20:[],50:[]};market_corr=[];vix_values=[];yield_values=[]
    for i,bar in enumerate(stock):
        at=bar.available_at;date=bar.close_at.date();known=stock[:i+1]
        if any(b.available_at>at for b in known):raise ValueError('Unavailable price prefix')
        closes=[b.close for b in known]
        # Five subsequent closes must already be published before confirming a low.
        center=i-5
        if center>=20:
            p=stock[center].close
            if p==min(b.close for b in stock[center-5:center+6]) and p<=.95*max(b.close for b in stock[center-20:center]):
                confirmed.append(center)
        row=dict(symbol=bar.symbol,date=date.isoformat(),decision_at=at.isoformat(),index=i,close=bar.close,
            observed_at=bar.close_at.isoformat(),price_basis='provider_split_adjusted_ohlc',verified_pit=False,
            return5=_ret(closes,5),return10=_ret(closes,10),return20=_ret(closes,20),return60=_ret(closes,60),return120=_ret(closes,120),
            prior_confirmed_low_date=stock[confirmed[-1]].close_at.date().isoformat() if confirmed else None,
            confirmed_low_known_at=stock[confirmed[-1]+5].available_at.isoformat() if confirmed else None,
            rise_from_confirmed_low=(bar.close/stock[confirmed[-1]].close-1)*100 if confirmed else None,
            growth_change20=(_ret(closes,20)-_ret(closes[:-20],20)) if len(closes)>40 else None,
            rv20=_rv(closes,20),rv60=_rv(closes,60),rsi14=wilder_rsi(closes),
            negative20=sum(b<a for a,b in zip(closes[-21:-1],closes[-20:]))/20 if len(closes)>20 else None,
            fall_acceleration5=(_ret(closes,5)-_ret(closes[:-5],5)) if len(closes)>10 else None,
            support120=min(b.low for b in known[-121:-1]) if len(known)>120 else None,
            current_drawdown20=(bar.close/max(closes[-21:-1])-1)*100 if len(closes)>20 else None,
            current_drawdown60=(bar.close/max(closes[-61:-1])-1)*100 if len(closes)>60 else None,
            expanding_drawdown=(bar.close/max(closes)-1)*100)
        for n in (20,50,200):
            ma=mean(closes[-n:]) if len(closes)>=n else None
            row['ma'+str(n)]=ma;row['distance_ma'+str(n)]=(bar.close/ma-1)*100 if ma else None
            if n in (20,50):
                ma_history[n].append(ma)
                previous=ma_history[n][-6] if len(ma_history[n])>=6 else None
                row['ma'+str(n)+'_slope5']=(ma/previous-1)*100 if ma is not None and previous else None
        for n in (20,50):
            previous=output[i-5].get('ma'+str(n)+'_slope5') if i>=5 else None
            current=row['ma'+str(n)+'_slope5']
            row['ma'+str(n)+'_slope_change5']=current-previous if current is not None and previous is not None else None
        old_rv5=output[i-5]['rv20'] if i>=5 else None
        row['rv_change5']=row['rv20']/old_rv5-1 if row['rv20'] is not None and old_rv5 else None
        earlier_rv=output[i-20]['rv20'] if i>=20 else None
        row['rv_change20']=row['rv20']/earlier_rv-1 if row['rv20'] is not None and earlier_rv else None
        clean_volume=lambda x:x if isinstance(x,(int,float)) and isfinite(x) and x>=0 else None
        volume=clean_volume(volumes.get(date.isoformat()));prior=[clean_volume(volumes.get(b.close_at.date().isoformat())) for b in stock[max(0,i-20):i]]
        row['volume']=volume
        row['volume_ratio']=volume/mean(prior) if volume is not None and len(prior)==20 and all(x is not None for x in prior) and mean(prior)>0 else None
        matched={}
        for name in ('qqq','sox'):
            current=lookup[name].get(date)
            valid=current is not None and current.available_at<=at
            row[name+'_observed_at']=current.close_at.isoformat() if valid else None
            row[name+'_available_at']=current.available_at.isoformat() if valid else None
            for n in (10,20,60):
                old=lookup[name].get(stock[i-n].close_at.date()) if i>=n else None
                good=valid and old is not None and old.available_at<=at
                ret=(current.close/old.close-1)*100 if good else None
                row[name+'_return'+str(n)]=ret
                own=_ret(closes,n)
                row['relative_'+name+str(n)]=own-ret if own is not None and ret is not None else None
                previous=output[i-n].get('relative_'+name+str(n)) if i>=n else None
                row['relative_'+name+'_change'+str(n)]=row['relative_'+name+str(n)]-previous if previous is not None and row['relative_'+name+str(n)] is not None else None
            visible=[b.close for b in market_sorted[name] if b.available_at<=at]
            row[name+'_close']=current.close if valid else None
            row[name+'_ma50']=mean(visible[-50:]) if valid and len(visible)>=50 else None
            if name=='qqq':
                row['qqq_ma200']=mean(visible[-200:]) if valid and len(visible)>=200 else None
                row['qqq_rv20']=_rv(visible,20) if valid else None;row['qqq_rv60']=_rv(visible,60) if valid else None
                matched[name]=[lookup[name].get(b.close_at.date()) for b in stock[max(0,i-40):i+1]]
        pairs=matched['qqq'];corr=None
        if len(pairs)==41 and all(b is not None and b.available_at<=at for b in pairs):
            own=np.diff(np.log(closes[-41:]));bench=np.diff(np.log([b.close for b in pairs]))
            corr=_corr(own[-20:],bench[-20:]);oldcorr=_corr(own[:20],bench[:20])
            row['correlation_change20']=corr-oldcorr if corr is not None and oldcorr is not None else None
        else:row['correlation_change20']=None
        row['correlation20']=corr
        vi=bisect_right(vix_times,at)-1
        observation=vix[vi] if vi>=0 and vix[vi].observed_at<=at and (at-vix[vi].observed_at).total_seconds()<=96*3600 else None
        value=observation.value['vix'] if observation else None;vix_values.append(value)
        row.update(vix=value,vix_observed_at=observation.observed_at.isoformat() if observation else None,vix_available_at=observation.available_at.isoformat() if observation else None)
        old=vix_values[-21] if len(vix_values)>20 else None
        row['vix_change20']=(value/old-1)*100 if value is not None and old else None
        ri=bisect_right(rate_times,at)-1
        rate=rates[ri] if ri>=0 and 0<=(at-utc(rates[ri]['observed_at'])).total_seconds()<=10*86400 else None
        value=rate['yield_pct'] if rate else None;yield_values.append(value)
        old=yield_values[-21] if len(yield_values)>20 else None
        row.update(yield10=value,yield_available_at=rate['available_at'] if rate else None,
            yield_change20_bp=(value-old)*100 if value is not None and old is not None else None)
        qc=row['qqq_close'];ma=row['qqq_ma200'];ret=row['qqq_return60']
        row['market_regime']='UP' if qc and ma and ret is not None and qc>ma and ret>0 else 'DOWN' if qc and ma and ret is not None and qc<ma and ret<0 else 'MIXED' if qc and ma and ret is not None else 'DATA_UNAVAILABLE'
        output.append(row)
    return output


def sector_features(features):
    lookup={symbol:{r['date']:r for r in rows} for symbol,rows in features.items() if symbol in SEMIS}
    for symbol,rows in features.items():
        for row in rows:
            peers=[series.get(row['date']) for s,series in lookup.items() if s!=symbol]
            peers=[p for p in peers if p and p['decision_at']<=row['decision_at'] and p['return20'] is not None and p['relative_qqq20'] is not None and p.get('qqq_return10') is not None]
            valid=[p for p in peers if p['index']>=10]
            weak=sum(p['return10']<0 and p['relative_qqq20']<=-3 for p in valid)
            row['sector_peers']=len(valid);row['sector_weak_fraction']=weak/len(valid) if len(valid)>=5 else None


def hypotheses(r):
    def all_known(keys):return all(r.get(k) is not None for k in keys)
    h={}
    h['H1']=r['return60']>=20 and r['distance_ma50']>=10 and r['rv20']>=r['rv60']*1.1 if all_known(('return60','distance_ma50','rv20','rv60')) and r['rv60']>0 else None
    pairs=[(r.get('relative_'+b+'20'),r.get(b+'_return20')) for b in ('qqq','sox')]
    known=[relative<=-5 and market>0 for relative,market in pairs if relative is not None and market is not None]
    h['H2']=True if any(known) else False if len(known)==2 else None
    h['H3']=r['sector_weak_fraction']>=.5 if r.get('sector_weak_fraction') is not None else None
    h['H4']=None
    needed=('qqq_close','qqq_ma50','qqq_rv20','qqq_rv60','vix','vix_change20','yield_change20_bp')
    h['H5']=r['qqq_close']<r['qqq_ma50'] and r['qqq_rv20']>=r['qqq_rv60']*1.1 and (r['vix']>=25 or r['vix_change20']>=20) and abs(r['yield_change20_bp'])>=25 if all_known(needed) and r['qqq_rv60']>0 else None
    return h


def flags(r):
    definitions={'ret20':('return20',lambda x:x>=10),'ret60':('return60',lambda x:x>=20),
        'ret120':('return120',lambda x:x>=40),'low_rise':('rise_from_confirmed_low',lambda x:x>=30),
        'growth_deceleration':('growth_change20',lambda x:x<=-5),'ma50_extension':('distance_ma50',lambda x:x>=10),
        'ma200_extension':('distance_ma200',lambda x:x>=20),'relative_weakness':('relative_qqq20',lambda x:x<=-5),
        'sector_weakness':('sector_weak_fraction',lambda x:x>=.5),'rsi_overbought':('rsi14',lambda x:x>=70),
        'ma20_falling':('ma20_slope5',lambda x:x<=0),'volume_surge':('volume_ratio',lambda x:x>=1.5),
        'negative_sessions':('negative20',lambda x:x>=.6),'fall_acceleration':('fall_acceleration5',lambda x:x<=-3),
        'correlation_rise':('correlation_change20',lambda x:x>=.15),'vix_stress':('vix',lambda x:x>=25),
        'yield_change':('yield_change20_bp',lambda x:abs(x)>=25)}
    output={k:rule(r[field]) if r.get(field) is not None else None for k,(field,rule) in definitions.items()}
    output['rv_ratio']=r['rv20']>=r['rv60']*1.1 if r.get('rv20') is not None and r.get('rv60') else None
    return output


def future_label(bars,index,horizon):
    future=bars[index+1:index+horizon+1]
    if len(future)<horizon:return dict(target=None,path_target=None,path_drawdown_pct=None,minimum_return=None,terminal_return=None,label_available_at=None,control_class='CENSORED')
    anchor=bars[index].close;minimum=min(b.close/anchor-1 for b in future);terminal=future[-1].close/anchor-1
    span=max(b.close for b in future)/min(b.close for b in future)-1
    group='LARGE_CORRECTION' if minimum<=-.10+1e-12 else 'SMALL_CORRECTION' if minimum<=-.03 else 'GROWTH' if terminal>=.05 else 'SIDEWAYS' if abs(terminal)<.05 and span<=.15 else 'MIXED'
    peak=anchor;maxdd=0
    for b in future:
        peak=max(peak,b.close);maxdd=max(maxdd,1-b.close/peak)
    return dict(target=minimum<=-.10+1e-12,path_target=maxdd>=.10-1e-12,path_drawdown_pct=maxdd*100,minimum_return=minimum*100,terminal_return=terminal*100,
        label_available_at=future[-1].available_at.isoformat(),control_class=group)
