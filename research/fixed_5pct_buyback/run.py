"""Offline, deterministic experiment using immutable PR9 snapshots only."""
import csv,hashlib,json,statistics,subprocess
from pathlib import Path
from research.fixed_5pct_buyback.engine import simulate

ROOT=Path(__file__).resolve().parents[2];REPORT=ROOT/'reports/fixed-5pct-buyback-v1';INPUT=REPORT/'inputs'
STOCKS=['AMD','NVDA','MU','TSM','AVGO','AMAT','AMZN','META','PLTR','LRCX','NBIS']
def read(n):return json.loads((INPUT/n).read_text())
def rows(p):return list(csv.DictReader(p.open()))
def write(n,rs):
    ks=list(dict.fromkeys(k for r in rs for k in r))
    with (REPORT/n).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=ks,lineterminator='\n');w.writeheader();w.writerows(rs)
def aggregate(daily,scenario):
    out=[];peak=100000;maxdd=0
    for d in sorted({r['date'] for r in daily}):
        xs=[r for r in daily if r['date']==d];assert len(xs)==11
        equity=sum(r['equity'] for r in xs)/11;cash=sum(r['cash'] for r in xs)/11;stock=sum(r['stock_value'] for r in xs)/11;div=sum(r['dividend_receivable'] for r in xs)/11
        peak=max(peak,equity);dd=100*(1-equity/peak);maxdd=max(maxdd,dd)
        out.append(dict(scenario=scenario,date=d,equity=equity,cash=cash,stock_value=stock,dividend_receivable=div,drawdown_pct=dd,weights='INITIAL_1_OVER11_NO_REBALANCE_MODEL_ONLY'))
    return out,dict(scenario=scenario,final_equity=out[-1]['equity'],return_pct=100*(out[-1]['equity']/100000-1),maximum_drawdown_pct=maxdd,cash=out[-1]['cash'],stock_value=out[-1]['stock_value'],dividend_receivable=out[-1]['dividend_receivable'])
def main():
    provenance=read('provenance.json')
    for e in provenance['read_only_snapshots']:assert hashlib.sha256((ROOT/e['local']).read_bytes()).hexdigest()==e['sha256'],e['local']
    inp=read('inputs.json');calendar={r['date']:r for r in rows(INPUT/'session-calendar.csv')}
    signals=[r for r in rows(INPUT/'warning-timeline.csv') if r['flag']=='sector_flag'];assert len(signals)==4
    bars={}
    for s in STOCKS:
        xs=sorted([dict(r) for r in inp['prices'] if r['symbol']==s and '2026-09-01'<=r['date']<='2026-11-02'],key=lambda r:r['date'])
        for r in xs:r['dividend']=sum(a['amount'] for a in inp['actions'] if a['symbol']==s and a['kind']=='dividends' and a['date']==r['date'])
        assert [x['date'] for x in xs]==sorted(calendar);bars[s]=xs
    configs=[dict(scenario='A_BUY_HOLD',fraction=0,threshold=.05,delay=1,stress=False,mode='limit')]
    for f in [.05,.1]:
        for d in [1,2]:configs.append(dict(scenario=f'B_SALE_ONLY_{f}_D{d}',fraction=f,threshold=.05,delay=d,stress=False,mode='sale_only'))
        for t in [.03,.05,.07,.1]:
            for d in [1,2]:
                for stress in [False,True]:configs.append(dict(scenario=f'LIMIT_{f}_T{t}_D{d}_S{int(stress)}',fraction=f,threshold=t,delay=d,stress=stress,mode='limit'))
    all_daily=[];all_trades=[];all_lots=[];all_orders=[];summaries=[];portfolios=[];portfolio_daily=[]
    for config in configs:
        scenario=config['scenario'];ds=[];ss=[]
        for symbol in STOCKS:
            z=simulate(bars[symbol],signals,calendar,**{k:v for k,v in config.items() if k!='scenario'})
            tag=dict(scenario=scenario,symbol=symbol,**{k:v for k,v in config.items() if k!='scenario'})
            ss.append(dict(**tag,**z['summary']));ds.extend(dict(**tag,**r) for r in z['daily'])
            all_trades.extend(dict(**tag,**r) for r in z['trades']);all_lots.extend(dict(**{k:v for k,v in tag.items() if k!='threshold'},**r) for r in z['lots']);all_orders.extend(dict(**tag,**r) for r in z['orders'])
        all_daily.extend(ds);summaries.extend(ss);pd,ps=aggregate(ds,scenario);portfolio_daily.extend(pd)
        ls=[r for r in all_lots if r['scenario']==scenario];wait=[r['wait_sessions'] for r in ls if r['status']=='CLOSED']
        ps.update(config);ps.update(sales=len(ls),closed_cycles=sum(r['status']=='CLOSED' for r in ls),open_cycles=sum(r['status']=='OPEN' for r in ls),fill_fraction=len(wait)/len(ls) if ls else None,mean_wait=statistics.mean(wait) if wait else None,median_wait=statistics.median(wait) if wait else None,realized_net_cash_surplus=sum(r['realized_net_cash_surplus'] or 0 for r in ls)/11,open_marked_benefit=sum(r['unrealized_missing_shares_benefit'] for r in ls)/11,missed_dividends=sum(r['missed_dividends'] for r in ls)/11,fees=sum(r['fees'] for r in ss)/11,slippage=sum(r['slippage'] for r in ss)/11)
        portfolios.append(ps)
    # E is not reimplemented. Re-execute the archived original JS and check its results against the published archive.
    script="const A=require(process.argv[1]),fs=require('fs');console.log(JSON.stringify(A.run(JSON.parse(fs.readFileSync(process.argv[2])))));"
    old=json.loads(subprocess.check_output(['node','-e',script,str(INPUT/'pr9-audit.cjs'),str(INPUT/'inputs.json')],text=True))
    old_saved=rows(INPUT/'strategy-economics.csv')
    for x in old['summary']:
        saved=next(y for y in old_saved if y['symbol']==x['symbol'] and float(y['fraction'])==x['fraction'] and int(y['delay'])==x['delay'])
        assert abs(x['final_equity']-float(saved['final_equity']))<1e-7
        if x['fraction']==0:
            bh=next(y for y in summaries if y['symbol']==x['symbol'] and y['scenario']=='A_BUY_HOLD');assert abs(bh['final_equity']-x['final_equity'])<1e-7
    for f in [.05,.1]:
        for d in [1,2]:
            name=f'E_PRIOR_{f}_D{d}';xs=[x for x in old['daily'] if x['fraction']==f and x['delay']==d];pd,ps=aggregate(xs,name);portfolio_daily.extend(pd);ps.update(fraction=f,delay=d,threshold=None,stress=False,mode='PR9_ORIGINAL_REPLAY')
            es=[x for x in old['summary'] if x['fraction']==f and x['delay']==d];ps.update(fees=sum(x['fees'] for x in es)/11,slippage=sum(x['slippage'] for x in es)/11,sales=sum(x['sales'] for x in es),closed_cycles=None,open_cycles=None);portfolios.append(ps)
            summaries.extend(dict(scenario=name,**x) for x in es)
    bh=portfolios[0]['final_equity']
    for x in portfolios:x['excess_vs_buyhold']=x['final_equity']-bh
    for x in summaries:
        base=next(y for y in summaries if y['symbol']==x['symbol'] and y['scenario']=='A_BUY_HOLD');x['excess_vs_buyhold']=x['final_equity']-base['final_equity']
    def primary(s):return s in ['A_BUY_HOLD','B_SALE_ONLY_0.05_D1','B_SALE_ONLY_0.1_D1','LIMIT_0.05_T0.05_D1_S0','LIMIT_0.1_T0.05_D1_S0','E_PRIOR_0.05_D1','E_PRIOR_0.1_D1']
    write('comparison.csv',[x for x in portfolios if primary(x['scenario'])]);write('sensitivity.csv',portfolios);write('stock-results.csv',summaries)
    write('sales.csv',[t for t in all_trades if t['side']=='SELL']);write('limit-orders.csv',all_orders);write('buybacks.csv',[t for t in all_trades if t['side']=='BUY']);write('trades.csv',all_trades)
    write('cycles.csv',all_lots);write('daily-stock-equity.csv',all_daily);write('daily-portfolio-equity.csv',portfolio_daily)
    write('opportunity-cost.csv',[dict(scenario=l['scenario'],symbol=l['symbol'],lot_id=l['lot_id'],sale_date=l['sale_date'],status=l['status'],net_realized=l['realized_net_cash_surplus'],open_marked_benefit=l['unrealized_missing_shares_benefit'],missed_dividends=l['missed_dividends'],false_sale_10=l['false_sale_10'],terminal10_return_pct=l['terminal10_return_pct'],runup_before_fill_day_pct=l['runup_before_fill_day_pct'],runup_possible_including_fill_day_pct=l['runup_possible_including_fill_day_pct'],intraday_order_unknown=l['intraday_order_unknown']) for l in all_lots])
    write('signals-used.csv',signals)
    (REPORT/'run.json').write_text(json.dumps(dict(source_commit='7135c2bdc0653986d93dfcfc66b202a6fb2f741e',initial_portfolio_capital=100000,signals=signals,scenarios=len(portfolios),new_scenarios=len(configs),input_original_prices_unchanged=True,prior_replay_matched=True,original_production_signals=False,long_history_completed=False,parameter_optimization=False,output_counts=dict(cycles=len(all_lots),trades=len(all_trades),daily_stock=len(all_daily),daily_portfolio=len(portfolio_daily))),indent=2)+'\n')
    print(json.dumps([x for x in portfolios if primary(x['scenario'])],indent=2))
if __name__=='__main__':main()
