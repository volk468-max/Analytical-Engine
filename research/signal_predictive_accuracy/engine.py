"""Pure competing-barrier outcomes. Future prices are evaluation labels only."""
HORIZONS=(5,10,20)
THRESHOLDS=(.03,.05,.10,.15)
def classify(window,anchor,down=.05,up=.05,horizon=10):
    if anchor is None:return dict(classification='UNRESOLVED',order='NO_REFERENCE_PRICE',complete=False,observed_sessions=0,down_date=None,up_date=None,down_latency=None,up_latency=None)
    xs=window[:horizon];di=next((i for i,x in enumerate(xs) if x['low']<=anchor*(1-down)),None);ui=next((i for i,x in enumerate(xs) if x['high']>=anchor*(1+up)),None)
    if di is not None and ui is not None and di==ui:state='UNKNOWN';order='SAME_BAR_UNKNOWN'
    elif di is not None and (ui is None or di<ui):state='TRUE_POSITIVE';order='DOWN_FIRST'
    elif ui is not None and (di is None or ui<di):state='FALSE_POSITIVE';order='UP_FIRST'
    elif len(xs)==horizon:state='FALSE_POSITIVE';order='NEITHER'
    else:state='UNRESOLVED';order='CENSORED'
    return dict(classification=state,order=order,complete=len(xs)==horizon,observed_sessions=len(xs),down_date=xs[di]['date'] if di is not None else None,up_date=xs[ui]['date'] if ui is not None else None,down_latency=di+1 if di is not None else None,up_latency=ui+1 if ui is not None else None)

def features(bars,i):
    r=bars[i];out={}
    for n in [5,20]:out['past_return_'+str(n)+'_pct']=100*(r['close']/bars[i-n]['close']-1) if i>=n else None
    for n in [20,60]:
        prior=bars[max(0,i-n):i];peak=max((x['close'] for x in prior),default=None)
        out['known_drawdown_'+str(n)+'_pct']=100*max(0,1-r['close']/peak) if peak is not None and len(prior)==n else None
    return out

def outcome(bars,i,anchor_kind='OPEN'):
    if anchor_kind not in ['OPEN','CLOSE']:raise ValueError('invalid anchor')
    signal=bars[i];future=bars[i+1:i+21];ref=future[0] if anchor_kind=='OPEN' and future else signal if anchor_kind=='CLOSE' else None
    price=ref['open'] if anchor_kind=='OPEN' and ref else signal['close'] if anchor_kind=='CLOSE' else None
    out=dict(anchor=anchor_kind,signal_date=signal['date'],reference_date=ref['date'] if ref else None,evaluation_start=future[0]['date'] if future else None,reference_price=price,nominal_reference_price=price*ref.get('factor',1) if ref and price is not None else None,reference_basis='CONSTANT_SPLIT_UNITS_NO_DIVIDEND_ADJCLOSE',**features(bars,i))
    primary=classify(future,price);out.update(primary)
    for n in [1,3,5,10,20]:out['return_'+str(n)+'_pct']=100*(future[n-1]['close']/price-1) if price is not None and len(future)>=n else None
    for n in HORIZONS:
        xs=future[:n];complete=len(xs)==n and price is not None;low=min(xs,key=lambda x:x['low']) if xs else None;high=max(xs,key=lambda x:x['high']) if xs else None
        out['complete_'+str(n)]=complete
        out['max_drop_'+str(n)+'_pct']=100*max(0,1-low['low']/price) if complete else None
        out['max_rise_'+str(n)+'_pct']=100*max(0,high['high']/price-1) if complete else None
        out['observed_min_'+str(n)]=low['low'] if low else None;out['observed_min_'+str(n)+'_date']=low['date'] if low else None
        out['observed_max_'+str(n)]=high['high'] if high else None;out['observed_max_'+str(n)+'_date']=high['date'] if high else None
        if n==20:
            out['min20']=low['low'] if complete else None;out['max20']=high['high'] if complete else None;out['min20_nominal_on_date']=low['low']*low.get('factor',1) if complete else None;out['max20_nominal_on_date']=high['high']*high.get('factor',1) if complete else None
        for d in THRESHOLDS:
            c=classify(future,price,d,.05,n);suffix=str(int(d*100))+'_'+str(n)
            for k in ['classification','order','down_date','down_latency']:out[k+'_'+suffix]=c[k]
    return out

def episodes(bars,start,end,seed=20,recovery=1.):
    first=next((i for i,x in enumerate(bars) if x['date']>=start),None)
    if first is None:return []
    prior=bars[max(0,first-seed):first];peak=max(prior,key=lambda x:x['close']) if prior else bars[first];event=None;out=[]
    for x in bars[first:]:
        if x['date']>end:break
        if event and x['close']>=peak['close']*recovery:
            event.update(status='RECOVERED',recovery_date=x['date'])
            if event['depth_pct']>=5:out.append(event)
            event=None;peak=x;continue
        if not event and x['close']>=peak['close']:peak=x;continue
        if event is None:event=dict(peak_date=peak['date'],peak_close=peak['close'],start_date=x['date'],trough_date=x['date'],trough_close=x['close'],depth_pct=0.,status='UNFINISHED',recovery_date=None,left_censored=peak['date']<start,seed_rows=len(prior))
        if x['close']<event['trough_close']:event.update(trough_close=x['close'],trough_date=x['date'])
        event['depth_pct']=100*(1-event['trough_close']/peak['close'])
        for n in [5,10,15]:
            if 'hit_'+str(n) not in event and x['close']<=peak['close']*(1-n/100):event['hit_'+str(n)]=x['date']
    if event and event['depth_pct']>=5:out.append(event)
    return out
