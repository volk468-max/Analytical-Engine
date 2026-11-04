"""Clarified specification, separate from immutable first audit outputs; no trades."""
import collections,csv,hashlib,json,random,statistics
from pathlib import Path
from research.signal_predictive_accuracy.io import R,load,STOCKS
from research.signal_predictive_accuracy.engine import outcome,episodes
O=R/'specification-completion'
SECTOR=['^SOX','SOXX','SMH']
ASSETS=SECTOR+['QQQ']+STOCKS
def write(name,rs):
    keys=list(dict.fromkeys(k for r in rs for k in r))
    with (O/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys,lineterminator='\n');w.writeheader();w.writerows(rs)
def strict(z,h=10,t=5):
    if not z['complete_'+str(h)]:return 'UNRESOLVED'
    c=z['classification_'+str(t)+'_'+str(h)]
    return 'UNRESOLVED' if c=='UNKNOWN' else c
def group_stats(xs,**tag):
    c=collections.Counter(x['status'] for x in xs);tp=c['TRUE_POSITIVE'];fp=c['FALSE_POSITIVE']
    return dict(**tag,n=len(xs),tp=tp,fp=fp,unresolved=c['UNRESOLVED'],precision=tp/(tp+fp) if tp+fp else None)
def qtile(a,p):
    a=sorted(a);return a[round((len(a)-1)*p)] if a else None
def pre_onset(signals,ci,e,h):
    onset=ci.get(e['start_date']);peak=ci.get(e['peak_date'])
    if onset is None:return []
    # Signal close must precede onset; next-open may be onset-session open.
    return [d for d in signals if d in ci and 0<onset-ci[d]<=h and ci[d]+1<=onset]
def main():
    O.mkdir(exist_ok=True);p=load();bs=p['bars'];ds=[x['date'] for x in p['calendar']];ci={d:i for i,d in enumerate(ds)};sig={x['date'] for x in p['signals']};assert len(sig)==134
    write('sector-signals.csv',p['signals']);allout=[];daily={};missed=[];false=[];timing=[]
    for s in ASSETS:
        a=bs[s];idx={x['date']:i for i,x in enumerate(a)};daily[s]={}
        for d in ds:
            if d<p['eligible'][s] or d not in idx:continue
            z=outcome(a,idx[d]);daily[s][d]=z
            if d not in sig:continue
            for anchor in ['OPEN','CLOSE']:
                x=dict(z if anchor=='OPEN' else outcome(a,idx[d],'CLOSE'))
                x.update(symbol=s,cohort='SECTOR' if s in SECTOR else 'MARKET' if s=='QQQ' else 'STOCK',status=strict(x),unresolved_reason='INCOMPLETE_WINDOW' if not x['complete_10'] else 'SAME_BAR_ORDER' if x['classification']=='UNKNOWN' else '',regime=p['regimes'][d],source_kind='RECONSTRUCTED_NOT_PRODUCTION')
                f=a[idx[d]+1:idx[d]+21]
                for h in [5,10,20]:
                    for side,field in [('drop','low'),('rise','high')]:
                        hit=x['observed_'+('min' if side=='drop' else 'max')+'_'+str(h)+'_date'];x['time_to_max_'+side+'_'+str(h)]=next((j+1 for j,b in enumerate(f[:h]) if b['date']==hit),None) if x['complete_'+str(h)] else None
                allout.append(x)
                if x['status']=='FALSE_POSITIVE':
                    price=x['reference_price'];late=next((j+11 for j,b in enumerate(f[10:20]) if b['low']<=price*.95),None)
                    false.append(dict(symbol=s,signal_date=d,anchor=anchor,return10=x['return_10_pct'],return20=x['return_20_pct'],max_rise10=x['max_rise_10_pct'],max_drop10=x['max_drop_10_pct'],max_rise20=x['max_rise_20_pct'],max_drop20=x['max_drop_20_pct'],complete20=x['complete_20'],up10_or_more=x['max_rise_20_pct']>=10 if x['complete_20'] else None,time_to_max_rise20=x['time_to_max_rise_20'],late_down5_latency=late,late_window_censored=not x['complete_20'],growth_duration_definition='sessions_to_first_20session_high_not_monotonic_growth'))
        es=episodes(a,max('2021-01-01',p['eligible'][s]),'2026-11-02')
        for d in sorted(sig):
            if d<p['eligible'][s] or d not in idx:continue
            active=next((e for e in es if e['peak_date']<=d<=e['trough_date']),None)
            known=100*(1-a[idx[d]]['close']/active['peak_close']) if active else None
            share=known/active['depth_pct'] if active and active['depth_pct'] else None
            timing.append(dict(symbol=s,signal_date=d,active_decline_to_event_trough=bool(active),event_peak=active['peak_date'] if active else None,event_trough=active['trough_date'] if active else None,drawdown_at_signal_pct=known,event_final_depth_pct=active['depth_pct'] if active else None,fraction_final_decline_already_occurred=share,at_least_half_already_occurred=share>=.5 if share is not None else None,label_only='RETROSPECTIVE_EVENT_DEPTH_NEVER_USED_IN_SECTOR_FLAG'))
        eligible_i=ci[max('2021-01-04',p['eligible'][s])]
        for n,e in enumerate(es):
            for t in [5,10,15]:
                hit=e.get('hit_'+str(t))
                if not hit:continue
                for h in [5,10,20]:
                    ws=pre_onset(sig,ci,e,h);ws=sorted(d for d in ws if d>=p['eligible'][s]);late=sorted(d for d in sig if d>=p['eligible'][s] and 0<ci[hit]-ci[d]<=h)
                    full=ci[e['start_date']]-h>=eligible_i
                    missed.append(dict(symbol=s,event_id=s+'_'+str(n),threshold=t,lookback=h,**e,threshold_date=hit,onset_lookback_complete=full,pre_onset_warning=bool(ws),missed_before_onset=not bool(ws) if full else None,last_pre_onset_warning=ws[-1] if ws else None,lead_to_threshold=ci[hit]-ci[ws[-1]] if ws else None,pre_threshold_warning=bool(late),last_pre_threshold_warning=late[-1] if late else None))
    write('signal-outcomes.csv',allout);write('false-signals.csv',sorted(false,key=lambda x:-(x['max_rise20'] or -999)));write('missed-drawdowns.csv',missed);write('signal-timing.csv',timing)
    stats=[];annual=[];matrix=[];regimes=[]
    for s in ASSETS:
        for anchor in ['OPEN','CLOSE']:
            xs=[x for x in allout if x['symbol']==s and x['anchor']==anchor];stats.append(group_stats(xs,symbol=s,anchor=anchor,cohort=xs[0]['cohort']))
            for regime in ['BULL','BEAR','SIDEWAYS']:
                regimes.append(group_stats([x for x in xs if x['regime']==regime],symbol=s,anchor=anchor,regime=regime))
            for h in [5,10,20]:
                for t in [3,5,10,15]:
                    matrix.append(group_stats([dict(x,status=strict(x,h,t)) for x in xs],symbol=s,anchor=anchor,horizon=h,down_pct=t,up_pct=5))
            for y in ['2021','2022','2023','2024','2025','2026','ALL']:
                sub=[x for x in xs if y=='ALL' or x['signal_date'].startswith(y)];ms=[x for x in missed if x['symbol']==s and x['lookback']==10 and x['threshold']==5 and x['onset_lookback_complete'] and (y=='ALL' or x['threshold_date'].startswith(y))]
                annual.append(group_stats(sub,symbol=s,anchor=anchor,year=y,missed_before_onset=sum(x['missed_before_onset'] for x in ms),eligible_5pct_events=len(ms)))
    write('signal-accuracy.csv',stats);write('sector-vs-stock.csv',stats);write('annual-accuracy.csv',annual)
    write('threshold-sensitivity.csv',matrix);write('regime-accuracy.csv',regimes)
    # Date is the unit. All stocks on each date are averaged before inference.
    # Circular moving-block bootstrap shares identical date weights across groups.
    rng=random.Random(20261104);weights=[];N=len(ds)
    for _ in range(499):
        w=[0]*N
        for j in range(0,N,60):
            start=rng.randrange(N)
            for k in range(min(60,N-j)):w[(start+k)%N]+=1
        weights.append(w)
    baseline=[]
    groups={s:[s] for s in SECTOR+['QQQ']};groups['STOCK_DATE_MEAN']=STOCKS
    for group,members in groups.items():
        for h in [5,10,20]:
            for t in [3,5,10,15]:
                vals={}
                for d in ds:
                    zs=[daily[s][d] for s in members if d in daily[s] and daily[s][d]['complete_'+str(h)]]
                    if not zs:continue
                    # Plain barrier event, NOT down-before-up classification.
                    vals[d]=statistics.mean(z['down_date_'+str(t)+'_'+str(h)] is not None for z in zs)
                warned=[d for d in vals if d in sig];controls=[d for d in vals if d not in sig]
                def cell(d):return (d[:4],(int(d[5:7])-1)//3,p['regimes'][d],tuple(s for s in members if d>=p['eligible'][s]))
                cells=collections.defaultdict(list)
                for d in controls:cells[cell(d)].append(d)
                matched=[d for d in warned if cells[cell(d)]]
                for kind in ['ALL_NONWARNING','MATCHED_QUARTER_REGIME']:
                    ws=warned if kind=='ALL_NONWARNING' else matched
                    pairs=[(ci[d],vals[d]) for d in ws]
                    if kind=='ALL_NONWARNING':cw=collections.Counter({d:1 for d in controls})
                    else:
                        cw=collections.Counter()
                        for d in matched:
                            cs=cells[cell(d)]
                            for c in cs:cw[c]+=1/len(cs)
                    cp=[(ci[d],vals[d],a) for d,a in cw.items()]
                    def estimate(w=None):
                        sw=sum((w[i] if w else 1) for i,v in pairs);cwt=sum(a*(w[i] if w else 1) for i,v,a in cp)
                        if not sw or not cwt:return None
                        ps=sum(v*(w[i] if w else 1) for i,v in pairs)/sw;pc=sum(v*a*(w[i] if w else 1) for i,v,a in cp)/cwt
                        return ps,pc,100*(ps-pc),ps/pc if pc else None
                    point=estimate();samples=[x for w in weights if (x:=estimate(w)) is not None]
                    baseline.append(dict(group=group,horizon=h,down_pct=t,event='INTRAHORIZON_DOWN_TOUCH_REGARDLESS_UPPER_BARRIER',control=kind,warning_dates=len(ws),control_dates=len(cp),unmatched_warning_dates=len(warned)-len(ws),probability_signal=point[0],probability_control=point[1],difference_pp=point[2],lift=point[3],difference_ci_low=qtile([x[2] for x in samples],.025),difference_ci_high=qtile([x[2] for x in samples],.975),lift_ci_low=qtile([x[3] for x in samples if x[3] is not None],.025),lift_ci_high=qtile([x[3] for x in samples if x[3] is not None],.975),bootstrap_block=60,bootstrap_reps=499,ci='POINTWISE_EXPLORATORY_NOT_MULTIPLICITY_ADJUSTED'))
    write('baseline-comparison.csv',baseline)
    print(json.dumps(dict(signal_dates=len(sig),outcomes=len(allout),sector_open=[x for x in stats if x['symbol'] in SECTOR and x['anchor']=='OPEN']),indent=2))
if __name__=='__main__':main()
