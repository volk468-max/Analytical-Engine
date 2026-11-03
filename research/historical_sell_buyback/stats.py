"""Close-to-close statistics, risk-free0%, no changes to account state."""
from datetime import date
import math,statistics
def metrics(daily,initial=100000,start=None):
    start=start or daily[0]['date'];end=daily[-1]['date'];prev=initial;peak=initial;dd=0.;returns=[]
    for x in daily:
        nav=x['equity'];returns.append(nav/prev-1);prev=nav;peak=max(peak,nav);dd=max(dd,1-nav/peak)
    sd=statistics.stdev(returns) if len(returns)>1 else 0;mean=statistics.mean(returns);years=(date.fromisoformat(end)-date.fromisoformat(start)).days/365.25
    return dict(first_date=start,last_date=end,initial_equity=initial,final_equity=prev,total_return_pct=100*(prev/initial-1),cagr_pct=100*((prev/initial)**(1/years)-1) if years>=1 else None,maximum_drawdown_pct=dd*100,volatility_pct=sd*math.sqrt(252)*100,sharpe=mean/sd*math.sqrt(252) if sd>0 else None,risk_free_rate_pct=0,average_cash_fraction=sum(x['cash']/x['equity'] for x in daily)/len(daily),days_with_cash_fraction=sum(x['cash']>1e-7 for x in daily)/len(daily),average_dividend_receivable_fraction=sum(x.get('dividend_receivable',0)/x['equity'] for x in daily)/len(daily),sessions=len(daily))
def annual(daily,initial=100000):
    out=[];previous=initial
    for year in sorted({x['date'][:4] for x in daily}):
        ds=[x for x in daily if x['date'].startswith(year)];m=metrics(ds,previous);out.append(dict(year=year,**m,return_pct=m['total_return_pct']));previous=ds[-1]['equity']
    out.append(dict(year='ALL',**metrics(daily,initial),return_pct=100*(daily[-1]['equity']/initial-1)));return out
