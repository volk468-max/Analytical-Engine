"""Retrospective labels/metrics are isolated from the causal signal engine."""
from statistics import mean,median
from .risk_signal_v3 import LEVELS,finite


def significant_events(rows,start,end):
    """All >=10% excursions since a known trailing-20 closing high.

    Reset on the next trailing-20 high even if it is below an older all-time peak.
    Threshold/trough labels describe outcomes, never engine inputs.
    """
    rows=[r for r in rows if r['date']<=end]
    output=[];peak=None;crossings={};trough=None
    def close(last,completed):
        if 10 in crossings and start<=rows[crossings[10]]['date']<=end:
            output.append(dict(symbol=rows[peak]['symbol'],peak=peak,end=last,trough=trough,
                crossings=dict(crossings),completed=completed,left_censored=rows[peak]['date']<start))
    for i,row in enumerate(rows):
        if i<20:continue
        new_peak=row['close']>=max(r['close'] for r in rows[i-20:i])
        if peak is None or new_peak or row['close']>=rows[peak]['close']:
            if peak is not None:close(i-1,True)
            peak=i;trough=i;crossings={}
        else:
            if row['close']<rows[trough]['close']:trough=i
            for threshold in (10,15,20):
                if threshold not in crossings and row['close']<=rows[peak]['close']*(1-threshold/100):crossings[threshold]=i
    if peak is not None:close(len(rows)-1,False)
    return output


def event_table(features,signals,start,end):
    known=[r for r in features if r['date']<=end]
    lookup={r['date']:r for r in signals if start<=r['date']<=end}
    output=[]
    for event in significant_events(features,start,end):
        p,last=event['peak'],event['end'];peak=known[p]
        available=[(j,lookup[known[j]['date']]) for j in range(p,last+1) if known[j]['date'] in lookup]
        valid=[(j,s) for j,s in available if s.get('risk_level') is not None]
        watch=next(((j,s) for j,s in valid if s['risk_level']=='WATCH'),None)
        warning=next(((j,s) for j,s in valid if LEVELS[s['risk_level']]>=1),None)
        reduce=next(((j,s) for j,s in valid if LEVELS[s['risk_level']]>=2),None)
        trough=known[event['trough']]
        loss=1-trough['close']/peak['close']
        dd_at_reduce=(1-known[reduce[0]]['close']/peak['close']) if reduce else None
        carried=False;entry_date=None
        if reduce:
            ordered=[s for s in signals if s['date']<=known[reduce[0]]['date']]
            pos=len(ordered)-1
            while pos>0 and LEVELS.get(ordered[pos-1].get('risk_level'),0)>=2:pos-=1
            entry_date=ordered[pos]['date']
            carried=entry_date<peak['date']
        row=dict(symbol=peak['symbol'],peak_date=peak['date'],peak_close=peak['close'],end_date=known[last]['date'],
            episode_ended_on_trailing20_high=event['completed'],left_censored=event['left_censored'],
            trough_date=trough['date'],observed_drawdown_pct=-loss*100,
            first_watch=known[watch[0]]['date'] if watch else None,
            first_warning_at_least_watch=known[warning[0]]['date'] if warning else None,
            first_reduce=known[reduce[0]]['date'] if reduce else None,
            first_reduce_level=reduce[1]['risk_level'] if reduce else None,
            first_reduce_entry_date=entry_date,reduce_carried_at_peak=carried,
            drawdown_at_reduce_pct=-dd_at_reduce*100 if reduce else None,
            observed_fall_fraction_before_reduce=dd_at_reduce/loss if reduce and loss else None,
            reduce_after_observed_trough=reduce[0]>event['trough'] if reduce else None,
            reduce_vix=reduce[1]['indicators'].get('vix') if reduce else None,
            reduce_support_broken=reduce[1].get('conditions',{}).get('support_broken') if reduce else None,
            reduce_conditions='; '.join(reduce[1]['active_conditions']) if reduce else None,
            information_cutoff=reduce[1]['decision_at'] if reduce else None,
            eligible_for_recall=not event['left_censored'] and bool(valid))
        for threshold in (10,15,20):
            index=event['crossings'].get(threshold)
            row[f'drawdown_{threshold}_date']=known[index]['date'] if index is not None else None
            row[f'reduce_lead_{threshold}_sessions']=index-reduce[0] if index is not None and reduce else None
            row[f'warning_lead_{threshold}_sessions']=index-warning[0] if index is not None and warning else None
        output.append(row)
    return output


def entry_outcomes(signals,start,end):
    sample=[s for s in signals if start<=s['date']<=end]
    prior=[s for s in signals if s['date']<start]
    output=[];prev=LEVELS.get(prior[-1].get('risk_level'),0) if prior else 0
    for i,s in enumerate(sample):
        level=LEVELS.get(s.get('risk_level'),0)
        entry=level>=2 and prev<2
        if entry:
            row=dict(symbol=s['symbol'],date=s['date'],risk_level=s['risk_level'],entry_index=i,
                vix=s['indicators'].get('vix'),support_broken=s.get('conditions',{}).get('support_broken'))
            for horizon in (5,10,20):
                complete=i+horizon<len(sample) and all(finite(sample[j]['indicators'].get('close')) and sample[j]['indicators']['close']>0 for j in range(i,i+horizon+1))
                row[f'forward_{horizon}_pct']=(sample[i+horizon]['indicators']['close']/s['indicators']['close']-1)*100 if complete else None
                row[f'worst_forward_{horizon}_pct']=min((sample[j]['indicators']['close']/s['indicators']['close']-1)*100 for j in range(i+1,i+horizon+1)) if complete else None
            complete=row['forward_20_pct'] is not None
            row['censored_20']=not complete
            row['no_further_10pct_decline']=row['worst_forward_20_pct']>-10+1e-10 if complete else None
            row['false_reduce_followed_by_growth']=bool(row['no_further_10pct_decline'] and row['forward_20_pct']>0) if complete else None
            output.append(row)
        prev=level
    return output


def score_run(features_by_symbol,signals_by_symbol,start,end):
    events=[];entries=[];counts={k:0 for k in LEVELS};valid=0;total=0;switches=0;years=set()
    for symbol,signals in signals_by_symbol.items():
        events.extend(event_table(features_by_symbol[symbol],signals,start,end))
        entries.extend(entry_outcomes(signals,start,end))
        prior=[s for s in signals if s['date']<start]
        previous=prior[-1].get('risk_level') if prior else None
        for s in [s for s in signals if start<=s['date']<=end]:
            total+=1;years.add(s['date'][:4])
            level=s.get('risk_level')
            if level is not None:
                valid+=1;counts[level]+=1
                if previous is not None and level!=previous:switches+=1
            previous=level
    eligible=[r for r in events if r['eligible_for_recall']]
    completed=[r for r in entries if not r['censored_20']]
    result=dict(start=start,end=end,symbols=len(signals_by_symbol),sessions=total,valid_sessions=valid,
        unavailable_sessions=total-valid,material_events=len(events),eligible_events=len(eligible),left_censored_events=sum(r['left_censored'] for r in events),
        reduce_entries=len(entries),complete_reduce_horizons=len(completed),censored_reduce_entries=len(entries)-len(completed),
        false_reduce_count=sum(r['false_reduce_followed_by_growth'] for r in completed),
        false_reduce_rate_pct=mean(r['false_reduce_followed_by_growth'] for r in completed)*100 if completed else None,
        no_further_10pct_decline_rate_pct=mean(r['no_further_10pct_decline'] for r in completed)*100 if completed else None,
        switches=switches,switches_per_100_sessions=switches/valid*100 if valid else None,
        switches_per_symbol_year=switches/(len(years)*len(signals_by_symbol)) if years else None,
        reduce_entries_per_symbol_year=len(entries)/(len(years)*len(signals_by_symbol)) if years else None)
    for level,count in counts.items():result[level.lower()+'_time_pct']=count/valid*100 if valid else None
    for threshold in (10,15,20):
        selected=[r for r in eligible if r[f'drawdown_{threshold}_date']]
        leads=[r[f'reduce_lead_{threshold}_sessions'] for r in selected if r[f'reduce_lead_{threshold}_sessions'] is not None]
        early=[lead for lead in leads if lead>0]
        result.update({f'events_{threshold}':len(selected),f'detected_before_{threshold}':len(early),
            f'recall_before_{threshold}_pct':len(early)/len(selected)*100 if selected else None,
            f'median_lead_{threshold}_sessions':median(leads) if leads else None,
            f'median_positive_lead_{threshold}_sessions':median(early) if early else None})
    detected=[r for r in eligible if r['first_reduce']]
    first10=[r for r in eligible if r['drawdown_10_date']]
    result['carried_high_risk_events']=sum(r['reduce_carried_at_peak'] for r in eligible)
    result['recall_before_10_new_entry_pct']=sum(r['reduce_lead_10_sessions'] is not None and r['reduce_lead_10_sessions']>0 and not r['reduce_carried_at_peak'] for r in first10)/len(first10)*100 if first10 else None
    result.update(late_after_half_fall_pct=mean(r['observed_fall_fraction_before_reduce']>.5 for r in detected)*100 if detected else None,
        reduce_after_trough_pct=mean(r['reduce_after_observed_trough'] for r in detected)*100 if detected else None)
    for horizon in (5,10,20):
        returns=[r[f'forward_{horizon}_pct'] for r in entries if r[f'forward_{horizon}_pct'] is not None]
        result[f'mean_forward_{horizon}_pct']=mean(returns) if returns else None
        result[f'forward_{horizon}_n']=len(returns)
    return result,events,entries


def training_objective(metrics):
    """Predeclared trade-off, not a profitability objective or October fit."""
    if not metrics['eligible_events'] or not metrics['complete_reduce_horizons']:return None
    return (metrics['recall_before_10_pct']/100-.5*metrics['false_reduce_rate_pct']/100
            -.25*(metrics['reduce_time_pct']+metrics['critical_time_pct'])/100
            -.01*metrics['switches_per_symbol_year'])
