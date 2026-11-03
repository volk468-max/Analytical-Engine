"""Frozen-signal outcome catalogue, descriptive statistics and nonnested missed falls."""
import collections,json,statistics
from datetime import datetime
from research.signal_predictive_accuracy.io import R,I,STOCKS,MARKETS,load,rows,write
from research.signal_predictive_accuracy.engine import outcome,classify,features,episodes,HORIZONS,THRESHOLDS

def summarize(data,**tag):
    full=[x for x in data if x['complete_10']];n=collections.Counter(x['classification'] for x in full);tp=n['TRUE_POSITIVE'];fp=n['FALSE_POSITIVE'];u=n['UNKNOWN'];den=tp+fp
    def avg(k,subset=full):
        xs=[x[k] for x in subset if x[k] is not None];return statistics.mean(xs) if xs else None
    def med(k,subset=full):
        xs=[x[k] for x in subset if x[k] is not None];return statistics.median(xs) if xs else None
    false=[x for x in full if x['classification']=='FALSE_POSITIVE'];true=[x for x in full if x['classification']=='TRUE_POSITIVE']
    return dict(**tag,rows=len(data),unique_warning_dates=len({x['signal_date'] for x in data}),complete10=len(full),true_positive=tp,false_positive=fp,unknown=u,unresolved=sum(x['classification']=='UNRESOLVED' for x in data),partial_known_outcomes=sum(not x['complete_10'] and x['classification']!='UNRESOLVED' for x in data),precision=tp/den if den else None,false_positive_fraction=fp/den if den else None,conservative_precision=tp/(den+u) if den+u else None,optimistic_precision=(tp+u)/(den+u) if den+u else None,mean_max_drop10=avg('max_drop_10_pct'),median_max_drop10=med('max_drop_10_pct'),mean_max_rise10=avg('max_rise_10_pct'),mean_tp_latency=avg('down_latency',true),median_tp_latency=med('down_latency',true),mean_false_terminal10=avg('return_10_pct',false),mean_false_runup10=avg('max_rise_10_pct',false),mean_known_dd20=avg('known_drawdown_20_pct'),already_down5_fraction=sum(x['known_drawdown_20_pct'] is not None and x['known_drawdown_20_pct']>=5 for x in full)/len(full) if full else None)

def main():
    p=load();bs=p['bars'];index={s:{x['date']:i for i,x in enumerate(a)} for s,a in bs.items()};cal=p['calendar'];calmap={x['date']:x for x in cal};ds=[x['date'] for x in cal];ci={d:i for i,d in enumerate(ds)};signals=p['signals'];out=[]
    for w in signals:
        for s in STOCKS+MARKETS:
            d=w['date']
            if d<p['eligible'][s]:continue
            i=index[s][d];nextbar=bs[s][i+1] if i+1<len(bs[s]) else None
            if nextbar and datetime.fromisoformat(calmap[nextbar['date']]['open_at'])<=datetime.fromisoformat(w['available_at']):raise ValueError('next open predates assumed publication')
            for anchor in ['OPEN','CLOSE']:
                z=outcome(bs[s],i,anchor);z.update(symbol=s,cohort='STOCK' if s in STOCKS else 'MARKET',year=d[:4],regime=p['regimes'][d],signal_available_at=w['available_at'],execution_at=calmap[nextbar['date']]['open_at'] if nextbar else None,source_kind='SAVED_RECONSTRUCTED_SECTOR_FLAG',production_confirmed=False);out.append(z)
    write('signals.csv',out)
    write('classification.csv',[{k:x[k] for k in ['symbol','cohort','signal_date','anchor','reference_date','reference_price','classification','order','complete','observed_sessions','down_date','up_date','down_latency','up_latency','production_confirmed']} for x in out])
    stats=[]
    for cohort in ['STOCK','MARKET']:
        for anchor in ['OPEN','CLOSE']:
            sample=[x for x in out if x['cohort']==cohort and x['anchor']==anchor];stats.append(summarize(sample,cohort=cohort,anchor=anchor,group='ALL',value='ALL'))
            for key in ['symbol','year','regime']:
                for v in sorted({x[key] for x in sample}):stats.append(summarize([x for x in sample if x[key]==v],cohort=cohort,anchor=anchor,group=key,value=v))
    write('statistics.csv',stats);write('stock-statistics.csv',[x for x in stats if x['group']=='symbol']);write('year-statistics.csv',[x for x in stats if x['group']=='year']);write('regime-statistics.csv',[x for x in stats if x['group']=='regime'])
    matrix=[]
    for cohort in ['STOCK','MARKET']:
        for anchor in ['OPEN','CLOSE']:
            sample=[x for x in out if x['cohort']==cohort and x['anchor']==anchor]
            for h in HORIZONS:
                for threshold in THRESHOLDS:
                    suffix=str(int(threshold*100))+'_'+str(h);xs=[x for x in sample if x['complete_'+str(h)]];n=collections.Counter(x['classification_'+suffix] for x in xs);tp=n['TRUE_POSITIVE'];fp=n['FALSE_POSITIVE'];u=n['UNKNOWN']
                    matrix.append(dict(cohort=cohort,anchor=anchor,horizon=h,down_pct=int(threshold*100),up_pct=5,complete=len(xs),tp=tp,fp=fp,unknown=u,precision=tp/(tp+fp) if tp+fp else None,conservative_precision=tp/(tp+fp+u) if tp+fp+u else None,incomplete=len(sample)-len(xs)))
    write('threshold-matrix.csv',matrix)
    # All-date control cache, produced without altering the supplied warning sequence.
    cache=[];q=bs['QQQ'];prev=False;mechanical={}
    for i,x in enumerate(q):
        flag=x['close']/q[i-5]['close']-1<0 if i>=5 else None;mechanical[x['date']]=flag is True and prev is not True;prev=flag
    for d in ds:
        members=[s for s in STOCKS if d>=p['eligible'][s]];eligible=tuple(members);vals=[];draw=[];classes=collections.Counter();stock_values={}
        for s in members:
            i=index[s][d];future=bs[s][i+1:i+11];price=future[0]['open'] if future else None;c=classify(future,price);classes[c['classification']]+=1
            value=1 if c['classification']=='TRUE_POSITIVE' else 0 if c['classification']=='FALSE_POSITIVE' else None
            if value is not None and c['complete']:vals.append(value)
            stock_values[s]=value if c['complete'] else None
            f=features(bs[s],i);dd=f['known_drawdown_20_pct']
            if dd is not None:draw.append(dd)
        ddmean=statistics.mean(draw) if draw else None;ddbin='UNKNOWN' if ddmean is None else 'LT3' if ddmean<3 else '3TO5' if ddmean<5 else '5TO10' if ddmean<10 else 'GE10'
        cache.append(dict(date=d,calendar_index=ci[d],quarter=d[:4]+'Q'+str((int(d[5:7])-1)//3+1),regime=p['regimes'][d],eligible_signature=';'.join(eligible),score=statistics.mean(vals) if vals else None,resolved=len(vals),tp=classes['TRUE_POSITIVE'],fp=classes['FALSE_POSITIVE'],unknown=classes['UNKNOWN'],complete10=ci[d]+10<len(ds)+1,mechanical=mechanical[d],sector_warning=any(w['date']==d for w in signals),mean_known_dd20=ddmean,dd_bin=ddbin,stock_scores=stock_values))
    # Correct maturity refers to ten next-session bars after signal index.
    for x in cache:x['complete10']=x['calendar_index']+10<len(ds)
    write('control-date-scores.csv',[dict(x,stock_scores=json.dumps(x['stock_scores'],sort_keys=True)) for x in cache]);(R/'control-cache.json').write_text(json.dumps(cache,separators=(',',':'))+'\n')
    catalogue=[];missed=[];sensitivity=[]
    for seed,recovery in [(20,1.),(60,1.),(20,.98)]:
        for s in STOCKS:
            start=max('2021-01-01',p['eligible'][s]);es=episodes(bs[s],start,'2026-11-02',seed,recovery)
            for n,e in enumerate(es):
                event=dict(symbol=s,event_id=s+'_'+str(seed)+'_'+str(recovery)+'_'+str(n),seed=seed,recovery_fraction=recovery,**e)
                if seed==20 and recovery==1:catalogue.append(event)
                for threshold in [5,10,15]:
                    hit=e.get('hit_'+str(threshold))
                    if not hit:continue
                    hi=ci[hit];eligible_index=next(i for i,d in enumerate(ds) if d>=p['eligible'][s]);base=dict(**event,threshold_pct=threshold,threshold_date=hit,active_sector_state_at_threshold=p['sector_daily'][hit]['sector_flag'])
                    for h in [5,10,20]:
                        ws=[w for w in signals if w['date']>=p['eligible'][s] and 0<hi-ci[w['date']]<=h and ci[w['date']]+1<len(ds) and datetime.fromisoformat(cal[ci[w['date']]+1]['open_at'])<datetime.fromisoformat(cal[hi]['close_at'])]
                        last=ws[-1] if ws else None;full=hi-h>=eligible_index
                        z=dict(**base,lookback=h,lookback_complete=full,warning_present=bool(last),warning_date=last['date'] if last else None,signal_lead_sessions=hi-ci[last['date']] if last else None,execution_lead_sessions=hi-ci[last['date']]-1 if last else None,false_negative=not bool(last) if full else None,interpretation='NO_NEW_ACTIVATION_IS_NOT_HOLD')
                        sensitivity.append(z)
                        if seed==20 and recovery==1:missed.append(z)
    write('drawdown-events.csv',catalogue);write('missed-falls.csv',missed);write('episode-sensitivity.csv',sensitivity)
    dates=[ci[w['date']] for w in signals if ci[w['date']]+10<len(ds)];selected=[];end=-1
    for i in dates:
        if i+1>end:selected.append(i);end=i+10
    run=dict(original_production_payloads=0,unique_warning_dates=len(signals),complete10_warning_dates=len(dates),nonoverlapping10_window_subset=len(selected),nonoverlap_is_not_proof_of_independence=True,calendar60_blocks=(len(ds)+59)//60,signal_rows=len(out),stock_rows=sum(x['cohort']=='STOCK' for x in out),market_rows=sum(x['cohort']=='MARKET' for x in out),primary_event_definition='DOWN5_BEFORE_UP5_IN10_SESSIONS_FROM_NEXT_OPEN_INCLUDING_EXECUTION_SESSION',full_windows_only_for_precision=True,formula_unchanged=True)
    (R/'run.json').write_text(json.dumps(run,indent=2)+'\n');print(json.dumps(run));print(json.dumps([x for x in stats if x['group']=='ALL']))
if __name__=='__main__':main()
