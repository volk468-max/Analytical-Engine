"""Continuous historical experiment; no signals/threshold selection or live IO."""
import csv,gzip,hashlib,io,json,math,statistics,subprocess
from pathlib import Path
from research.historical_sell_buyback.engine import simulate
from research.historical_sell_buyback.stats import metrics,annual
from research.historical_sell_buyback.prepare import ROOT,R,STOCKS,write

def read(n):return json.loads((R/n).read_text())
def csvrows(n):return list(csv.DictReader((R/n).open()))
def key(c):return f"{c['mode']}_F{c['fraction']}_T{c['threshold']}_D{c['delay']}_S{int(c['stress'])}_C{int(c['fee_rate']*10000)}"
def primary(c):return c['fee_rate']==.0005 and c['delay']==1 and not c['stress'] and (c['fraction']==0 or c['mode']=='sale_only' or c['threshold']==.05)
def scenario_configs():
    out=[]
    for cost in [.0005,.001]:
        out.append(dict(mode='limit',fraction=0,threshold=.05,delay=1,stress=False,fee_rate=cost,slip_rate=cost))
        for f in [.05,.1]:
            for d in [1,2]:
                out.append(dict(mode='sale_only',fraction=f,threshold=.05,delay=d,stress=False,fee_rate=cost,slip_rate=cost))
                for t in [.03,.05,.07,.1]:
                    for stress in [False,True]:out.append(dict(mode='limit',fraction=f,threshold=t,delay=d,stress=stress,fee_rate=cost,slip_rate=cost))
    return out
def stock_bars(inp,s):
    a=[dict(x) for x in inp['prices'] if x['symbol']==s and x['date']>=inp['eligible'][s]];a.sort(key=lambda x:x['date'])
    for x in a:x['dividend']=sum(d['amount'] for d in inp['actions'] if d['symbol']==s and d['kind']=='dividends' and d['date']==x['date'])
    return a
def padded_daily(calendar,ds):
    have={x['date']:x for x in ds};first=ds[0]['date'];out=[]
    for d in calendar:
        if d<first:out.append(dict(date=d,equity=100000,cash=100000,stock_value=0,dividend_receivable=0,shares=0))
        else:
            if d not in have:raise ValueError('missing invested session; no fabricated price')
            out.append(have[d])
    return out
def aggregate(padded,members):
    n=len(members);out=[]
    for xs in zip(*(padded[s] for s in members)):
        assert len({x['date'] for x in xs})==1
        out.append(dict(date=xs[0]['date'],**{k:sum(x[k] for x in xs)/n for k in ['equity','cash','stock_value','dividend_receivable']}))
    return out
def main():
    gate=read('control/gate.json');assert gate['gate_passed'] and gate['adapted_engine_control_cases_equal']==66
    inp=read('prepared.json');calendar={r['date']:r for r in inp['calendar']};dates=sorted(calendar);signals=inp['signals'];bars={s:stock_bars(inp,s) for s in STOCKS};configs=scenario_configs()
    regimes=csvrows('regimes.csv');prev_regime={regimes[i]['date']:regimes[i-1]['regime'] if i else 'UNKNOWN' for i in range(len(regimes))}
    full11=STOCKS;comparable=[s for s in STOCKS if inp['eligible'][s]==dates[0]];variants={'RESERVED11':full11,'COMPARABLE10':comparable}
    stockstats=[];portstats=[];years=[];regstats=[];sale_rows=[];buy_rows=[];lot_rows=[];quality=[];portdaily=[];corp_ledger=[];daily_stock_primary=[]
    for ci,c in enumerate(configs):
        name=key(c);is_primary=primary(c);results={};padded={}
        for s in STOCKS:
            z=simulate(bars[s],signals,calendar,**c);results[s]=z;padded[s]=padded_daily(dates,z['daily'])
            sm=metrics(z['daily']);sm.update(z['summary']);last=bars[s][-1];sm.update(scenario=name,symbol=s,primary=is_primary,**c,final_nominal_shares=z['summary']['shares']/last['split_future_factor'],share_units='TERMINAL_SPLIT_NORMALIZED',first_eligible_date=inp['eligible'][s]);stockstats.append(sm)
            if is_primary:
                bmap={x['date']:x for x in bars[s]}
                for t in z['trades']:
                    f=bmap[t['date']]['split_future_factor'];tr=dict(scenario=name,symbol=s,**t,nominal_fill_price=t['price']*f,nominal_quantity=t['quantity']/f,split_unit_factor=f,fee_rate=c['fee_rate'],sale_delay=c['delay'])
                    if t['side']=='SELL':sale_rows.append(tr)
                    if t['side']=='BUY':buy_rows.append(tr)
                for l in z['lots']:
                    f=bmap[l['sale_date']]['split_future_factor'];fend=last['split_future_factor'];fb=bmap[l['buy_date']]['split_future_factor'] if l['buy_date'] else None
                    row=dict(scenario=name,symbol=s,**l,nominal_original_sale_price=l['sale_price']*f,nominal_original_sold_quantity=l['quantity']/f,nominal_buy_price=l['buy_price']*fb if fb else None,nominal_restored_quantity=l['quantity']/fb if fb else 0,nominal_terminal_limit=l['limit_price']*fend,signal_regime=next((r['regime'] for r in regimes if r['date']==l['signal_date']),'UNKNOWN'))
                    lot_rows.append(row)
                for d in z['daily']:
                    factor=bmap[d['date']]['split_future_factor'];daily_stock_primary.append(dict(scenario=name,symbol=s,**d,nominal_shares=d['shares']/factor,nominal_close=bmap[d['date']]['close']*factor,split_unit_factor=factor))
        for variant,members in variants.items():
            pd=aggregate(padded,members);m=metrics(pd);zs=[results[s]['summary'] for s in members]
            m.update(scenario=name,variant=variant,primary=is_primary,**c,sales=sum(z['sales'] for z in zs),closed_buybacks=sum(z['closed_cycles'] for z in zs),open_lots=sum(z['open_cycles'] for z in zs),realized_savings=sum(z['realized_net_cash_surplus'] for z in zs)/len(members),open_marked_benefit=sum(z['unrealized_missing_shares_benefit'] for z in zs)/len(members),missed_dividends=sum(z['missed_dividends'] for z in zs)/len(members),fees=sum(z['fees'] for z in zs)/len(members),slippage=sum(z['slippage'] for z in zs)/len(members),cash=pd[-1]['cash'],stock_value=pd[-1]['stock_value'],dividend_receivable=pd[-1]['dividend_receivable'],initial_slot_count=len(members));portstats.append(m)
            years.extend(dict(scenario=name,variant=variant,primary=is_primary,**y) for y in annual(pd))
            if is_primary:
                portdaily.extend(dict(scenario=name,variant=variant,**d) for d in pd)
                prev=100000;bucket={}
                for d in pd:
                    state=prev_regime[d['date']];ret=d['equity']/prev-1;prev=d['equity'];bucket.setdefault(state,[]).append(ret)
                for state,rets in bucket.items():regstats.append(dict(scenario=name,variant=variant,regime=state,sessions=len(rets),average_daily_return=statistics.mean(rets),conditional_compounded_return=math.prod(1+r for r in rets)-1,annualized_volatility=statistics.stdev(rets)*math.sqrt(252) if len(rets)>1 else None,interpretation='DISCONNECTED_CONDITIONAL_DAYS_NOT_TRADABLE_REGIME_STRATEGY'))
        if ci%10==0:print('completed',ci+1,'of',len(configs),flush=True)
    # Relatives compare identical cost and original sell delay. Sell-only legitimately exhausts shares.
    def matching(rows,c,mode,fraction):return next(x for x in rows if x['mode']==mode and x['fraction']==fraction and x['fee_rate']==c['fee_rate'] and (fraction==0 or x['delay']==c['delay']) and not x['stress'] and x['threshold']==.05)
    for x in portstats:
        same=[z for z in portstats if z['variant']==x['variant']];bh=matching(same,x,'limit',0);x['excess_vs_buyhold']=x['final_equity']-bh['final_equity'];x['excess_vs_sale_only']=x['final_equity']-matching(same,x,'sale_only',x['fraction'])['final_equity'] if x['fraction'] else 0
    for x in stockstats:
        same=[z for z in stockstats if z['symbol']==x['symbol']];bh=matching(same,x,'limit',0);x['excess_vs_buyhold']=x['final_equity']-bh['final_equity'];x['excess_vs_sale_only']=x['final_equity']-matching(same,x,'sale_only',x['fraction'])['final_equity'] if x['fraction'] else 0
    # One canonical signal-quality cohort prevents duplicated sensitivities being counted as independent trials.
    canon=key(dict(mode='limit',fraction=.1,threshold=.05,delay=1,stress=False,fee_rate=.0005,slip_rate=.0005))
    for signal in signals:
        ls=[l for l in lot_rows if l['scenario']==canon and l['signal_date']==signal['date']];mature=[l for l in ls if l['horizon_10_complete']];wait=[l['wait_sessions'] for l in ls if l['status']=='CLOSED']
        quality.append(dict(signal_date=signal['date'],available_at=signal['available_at'],regime=next(r['regime'] for r in regimes if r['date']==signal['date']),executed_stocks=len(ls),stocks_observed_down5=sum(l['down5_observed_date'] is not None for l in ls),mature10=len(mature),false10=sum(l['false_sale_10'] for l in mature),continued_growth10=sum(l['terminal10_return_pct'] is not None and l['terminal10_return_pct']>0 for l in mature),closed=len(wait),open=sum(l['status']=='OPEN' for l in ls),mean_wait=statistics.mean(wait) if wait else None,median_wait=statistics.median(wait) if wait else None,mean_runup_lower=statistics.mean(l['runup_before_fill_day_pct'] for l in ls) if ls else None,original_production_signal=False))
    write('portfolio-comparison.csv',[x for x in portstats if x['primary']]);write('sensitivity.csv',portstats);write('stock-performance.csv',stockstats);write('annual-performance.csv',[x for x in years if x['primary']]);write('annual-sensitivity.csv',years);write('regime-performance.csv',regstats)
    write('sales.csv',sale_rows);write('buybacks.csv',buy_rows);write('lots.csv',lot_rows);write('open-lots.csv',[x for x in lot_rows if x['status']=='OPEN']);write('signal-quality.csv',quality);write('daily-portfolio.csv',portdaily)
    cols=list(dict.fromkeys(k for r in daily_stock_primary for k in r));buf=io.StringIO();w=csv.DictWriter(buf,fieldnames=cols,lineterminator='\n');w.writeheader();w.writerows(daily_stock_primary);(R/'daily-stock.csv.gz').write_bytes(gzip.compress(buf.getvalue().encode(),mtime=0))
    run=dict(gate=gate,scenarios=len(configs),variants=variants,primary_configs=sum(primary(c) for c in configs),source_snapshot='Yahoo2020warmup..2026-11-02',sectors_reconstructed_not_production=True,full_period_days=len(dates),signal_count=len(signals),parameter_optimization=False,risk_free_rate=0,corporate_ledger='CONSTANT_SPLIT_UNITS_WITH_EXPLICIT_CONTEMPORANEOUS_NOMINAL_REPORTS',prior_strategy_status='OPTIONAL_NOT_YET_INCLUDED')
    (R/'run.json').write_text(json.dumps(run,indent=2)+'\n');print(json.dumps([x for x in portstats if x['primary']],indent=2))
if __name__=='__main__':main()
