"""Market closing episodes and strictly pre-onset snapshots; no model fitting."""
from collections import Counter
import numpy as np
from common import *

def episodes(df,symbol):
    dates=list(df.index);c=df['close'].to_numpy();result=[];peak=0;i=1
    while i<len(c):
        if c[i]>=c[peak]:peak=i;i+=1;continue
        onset=i;j=i
        while j<len(c) and c[j]<c[peak]:j+=1
        end=j if j<len(c) else len(c)-1;path=c[onset:end+1];trough=onset+int(np.argmin(path));depth=1-c[trough]/c[peak]
        if depth>=.05-1e-12:
            crosses={t:next((k for k in range(onset,end+1) if c[k]<=c[peak]*(1-t/100)+c[peak]*1e-12),None) for t in (5,10,15)}
            e=dict(event_id=f'{symbol}-{dates[onset]}',symbol=symbol,peak_date=dates[peak],onset_date=dates[onset],threshold5_date=dates[crosses[5]],threshold10_date=dates[crosses[10]] if crosses[10] is not None else None,threshold15_date=dates[crosses[15]] if crosses[15] is not None else None,trough_date=dates[trough],recovery_date=dates[j] if j<len(c) else None,end_date=dates[end],depth_pct=depth*100,duration_sessions=end-onset+1,onset_to_threshold5=crosses[5]-onset,onset_to_trough=trough-onset,left_truncated=peak==0,prior_lifetime_peak='UNKNOWN',right_censored=j==len(c),post_onset60_complete=onset+59<len(c),depth_first60_pct=(1-min(c[onset:min(onset+60,len(c))])/c[peak])*100)
            result.append(e)
        if j>=len(c):break
        peak=j;i=j+1
    return result

def run(bars,dates,panel):
    catalogue=[e for s in MARKET for e in episodes(bars[s],s)];write('market-episodes.csv',catalogue)
    cluster_end='';cluster=0;clusters=[]
    for e in sorted(catalogue,key=lambda r:(r['onset_date'],r['symbol'])):
        if e['onset_date']>cluster_end:cluster+=1
        cluster_end=max(cluster_end,e['end_date']);clusters.append(dict(event_id=e['event_id'],symbol=e['symbol'],cluster_id=cluster,onset_date=e['onset_date'],end_date=e['end_date'],independence='NOT_ESTABLISHED'))
    write('market-episode-clusters.csv',clusters);cid={r['event_id']:r['cluster_id'] for r in clusters}
    snapshots=[];controls=[];coverage=[]
    for symbol in MARKET:
        lookup={r['date']:r for r in panel[symbol]};events=[e for e in catalogue if e['symbol']==symbol];ds=list(bars[symbol].index)
        controls_all=[r for r in panel[symbol] if not any(e['onset_date']<=r['date']<=e['end_date'] for e in events)]
        for e in events:
            onset=ds.index(e['onset_date'])
            for offset in (60,40,20,10,5):
                date=ds[onset-offset] if onset>=offset else None;r=lookup.get(date);ctx=dict(event_id=e['event_id'],cluster_id=cid[e['event_id']],symbol=symbol,onset_date=e['onset_date'],offset=offset,snapshot_date=date,status='AVAILABLE' if r else 'MISSING_WARMUP')
                snapshots.append(dict(ctx,decision_at=r['decision_at'] if r else None,market_regime=r['market_regime'] if r else None,**{f:r[f] if r else None for f in M_FLAGS}))
                if not r:controls.append(dict(ctx,control_date=None,control_regime=None,distance_sessions=None,match_status='NO_SNAPSHOT',reuse_count=None,inverse_reuse_weight=None,**{f:None for f in M_FLAGS}));continue
                assert date<e['onset_date'];year=int(date[:4]);block=(year-2000)//2
                candidates=[x for x in controls_all if x['market_regime']==r['market_regime'] and (int(x['date'][:4])-2000)//2==block and abs(x['calendar_index']-dates.index(e['onset_date']))>=60]
                chosen=sorted(candidates,key=lambda x:(abs(x['calendar_index']-r['calendar_index']),x['date']))[:3]
                for x in chosen or [None]:controls.append(dict(ctx,control_date=x['date'] if x else None,control_regime=x['market_regime'] if x else None,distance_sessions=abs(x['calendar_index']-r['calendar_index']) if x else None,match_status='MATCH' if x else 'NO_MATCH',reuse_count=None,inverse_reuse_weight=None,**{f:x[f] if x else None for f in M_FLAGS}))
        for flag in M_FLAGS:
            for offset in (60,40,20,10,5):
                ss=[r for r in snapshots if r['symbol']==symbol and r['offset']==offset and r['status']=='AVAILABLE'];warn=[r for r in ss if r[flag]]
                coverage.append(dict(symbol=symbol,flag=flag,offset=offset,eligible_events=len(ss),exposed_events=len(warn),P_flag_given_event_at_offset=len(warn)/len(ss) if ss else None,exposed_clusters=len({r['cluster_id'] for r in warn}),independent_events='UNKNOWN'))
    reuse=Counter((r['symbol'],r['control_date']) for r in controls if r['control_date'])
    for r in controls:
        if r['control_date']:r['reuse_count']=reuse[r['symbol'],r['control_date']];r['inverse_reuse_weight']=1/r['reuse_count']
    write('pre-onset-snapshots.csv',snapshots);write('matched-controls.csv',controls);write('pre-onset-coverage.csv',coverage)
    lead=[]
    for e in catalogue:
        onset=dates.index(e['onset_date']);trailing=[r for r in panel[e['symbol']] if onset-60<=r['calendar_index']<onset]
        for flag in M_FLAGS:
            hits=[onset-r['calendar_index'] for r in trailing if r[flag]]
            lead.append(dict(event_id=e['event_id'],symbol=e['symbol'],cluster_id=cid[e['event_id']],flag=flag,eligible_sessions=len(trailing),warning_sessions=len(hits),first_lead_sessions=max(hits) if hits else None,last_lead_sessions=min(hits) if hits else None,pre_onset_coverage=bool(hits),status='COMPLETE60' if len(trailing)==60 else 'PARTIAL_OR_UNAVAILABLE'))
    write('pre-onset-lead-times.csv',lead)
    return catalogue,cluster

if __name__=='__main__':
    bars,dates,cal=load_bars();panel=build_panel(bars,dates);c,n=run(bars,dates,panel);print('market episodes',len(c),'overlap clusters',n)
