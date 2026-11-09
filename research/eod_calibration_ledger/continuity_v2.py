"""Same-provider arithmetic diagnostic; not independent history qualification."""
import gzip,json
import numpy as np
try:
 from .preliminary import *
except ImportError:
 from preliminary import *

def run():
 frames,dates,actions=load_prices();rows=[]
 for symbol,day in [('NVDA','2021-07-20'),('NVDA','2024-06-10'),('MU','2024-10-07'),('QQQ','2024-03-18')]:
  f=frames[symbol];i=dates.index(day);prev=f.close.iloc[i-1];close=f.close.iloc[i];div=f['div'].iloc[i];r=json.loads(gzip.decompress((BASE/'data'/(symbol+'.json.gz')).read_bytes()))['chart']['result'][0];adj=np.asarray(r['indicators']['adjclose'][0]['adjclose']);factor_ratio=(adj[i]/close)/(adj[i-1]/prev);expected=1/(1-div/prev)
  rows.append(dict(symbol=symbol,date=day,previous_normalized_close=prev,normalized_close=close,provider_dividend=div,price_return=close/prev-1,gross_total_return=(close+div)/prev-1,adj_factor_ratio=factor_ratio,expected_dividend_factor_ratio=expected,factor_residual_bps=(factor_ratio/expected-1)*10000,split_memo=[x for x in actions if x['symbol']==symbol and x['date']==day and x['kind']=='splits'],independent_price_evidence=False,qualification='DIAGNOSTIC_ONLY_NO_FULL_PASS'))
 write('continuity-diagnostic.csv',rows)
if __name__=='__main__':run()
