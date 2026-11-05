"""Continuous fixed cash-limited trim/restoration accounts on archived real bars."""
import csv,json
import numpy as np

def restore(sold,cash,price,cost=.0005):
    unit=price*(1+cost)*(1+cost);qty=min(sold,cash/unit);return qty,max(0.,cash-qty*unit)

def run(pred,source,calendar,out,write):
    from study import ENSEMBLES,alert
    bars=list(csv.DictReader((source/'data/risk-signal-v3/bars.csv').open()));manifest=json.loads((source/'data/risk-signal-v3/manifest.json').read_text());divs={}
    for src in manifest['sources']:
        if src['symbol'] not in ('AMD','NVDA','MU'):continue
        for v in src.get('reported_corporate_actions',{}).get('dividends',{}).values():
            from datetime import datetime,timezone
            d=datetime.fromtimestamp(v['date'],timezone.utc).date().isoformat();divs[src['symbol'],d]=float(v['amount'])
    summary=[];daily=[];trades=[];lots=[]
    for symbol in ('AMD','NVDA','MU'):
        bs=sorted([r for r in bars if r['symbol']==symbol],key=lambda r:r['close_at']);lookup={r['close_at'][:10]:i for i,r in enumerate(bs)}
        rs=sorted([r for r in pred if r['symbol']==symbol and r['target']=='touch' and r['threshold_pct']==10. and r['horizon']==20],key=lambda r:r['date'])
        start=lookup[rs[0]['date']]+1;signals={r['date']:r for r in rs}
        for model in ENSEMBLES:
         for delay in (1,2):
            context=dict(symbol=symbol,model=model,delay=delay);qty=100000/(float(bs[start]['open'])*1.0005**2);bhqty=qty;cash=0.;reserved=0.;receivable=0.;bhdiv=0.;pending=None;active=None;last_restore=-1;opportunity=0.;false_count=0;count=0;path=[];bhpath=[];fractions=[]
            for i in range(start,len(bs)):
                bar=bs[i];date=bar['close_at'][:10];op=float(bar['open']);cl=float(bar['close']);div=divs.get((symbol,date),0.)
                receivable+=qty*div;bhdiv+=bhqty*div
                if active is not None and i==active['buy_index']:
                    restored,left=restore(active['sold'],reserved,op);qty+=restored;cash+=left
                    mark=left+restored*op-active['sold']*op;opp=active['sold']*(op-active['sale_open'])
                    false=not active['target_hit']
                    if false:opportunity+=opp;false_count+=1
                    lots.append(dict(context,signal_date=active['signal_date'],sale_date=active['sale_date'],buy_date=date,sold=active['sold'],restored=restored,sale_open=active['sale_open'],buy_open=op,sale_net=reserved,cash_surplus=left,relative_mark=mark,false_warning=false,false_warning_price_opportunity=opp if false else 0.))
                    trades.append(dict(context,date=date,side='BUY',quantity=restored,price=op,cash_flow=-restored*op*1.0005**2));reserved=0.;active=None;last_restore=i
                if pending is not None and i==pending['index']:
                    sold=.25*qty;qty-=sold;reserved=sold*op*.9995**2;count+=1
                    active=dict(sold=sold,buy_index=i+20,signal_date=pending['signal_date'],sale_date=date,sale_open=op,target_hit=pending['target_hit']);pending=None
                    trades.append(dict(context,date=date,side='SELL',quantity=sold,price=op,cash_flow=reserved))
                nav=qty*cl+cash+reserved+receivable;bh=bhqty*cl+bhdiv
                assert min(qty,cash,reserved,receivable)>=-1e-8
                path.append(nav);bhpath.append(bh);fractions.append((cash+reserved)/nav)
                daily.append(dict(context,date=date,shares=qty,free_cash=cash,reserved_cash=reserved,dividend_receivable=receivable,nav=nav,price_only_nav=qty*cl+cash+reserved,bh_nav=bh,bh_shares=bhqty,bh_dividend_receivable=bhdiv,open_lot=active is not None))
                r=signals.get(date)
                if r is not None and active is None and pending is None and i>last_restore and bool(alert([r],model)[0]):
                    execution=i+delay
                    if execution<len(bs):
                        assert bs[execution]['open_at']>r['decision_at']
                        pending=dict(index=execution,signal_date=date,target_hit=bool(r['y']))
            dd=lambda x:float(np.max(1-np.array(x)/np.maximum.accumulate(x)))
            summary.append(dict(context,first_date=bs[start]['close_at'][:10],last_date=date,initial_capital=100000,final_nav=path[-1],bh_final_nav=bhpath[-1],delta_nav=path[-1]-bhpath[-1],price_only_nav=qty*cl+cash+reserved,bh_price_only_nav=bhqty*cl,max_drawdown=dd(path),bh_max_drawdown=dd(bhpath),average_cash_fraction=float(np.mean(fractions)),reductions=count,completed_lots=count-int(active is not None),open_lot=active is not None,pending=pending is not None,missed_dividends=bhdiv-receivable,false_warning_lots=false_count,false_warning_price_opportunity_usd=opportunity,independent_events='UNKNOWN'))
    write('economic-summary.csv',summary);write('economic-daily.csv.gz',daily);write('economic-trades.csv',trades);write('economic-lots.csv',lots)
