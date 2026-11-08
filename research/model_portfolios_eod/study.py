import csv,gzip,hashlib,io,json,urllib.request,sys
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import pandas as pd
import exchange_calendars as xc
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'reports/model-portfolios-eod-v1';SYMS=('AMD','NVDA','MU','QQQ')
def write(name,rows):
 rows=list(rows);s=io.StringIO();w=csv.DictWriter(s,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows);b=s.getvalue().encode();(OUT/name).write_bytes(gzip.compress(b,mtime=0) if name.endswith('.gz') else b)
def acquire():
 sources=[]
 for sym in SYMS:
  url=f'https://query1.finance.yahoo.com/v8/finance/chart/{sym}?period1=946684800&period2=1794009600&interval=1d&includePrePost=false&events=div%2Csplits'
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'AlphaOS research'}),timeout=30) as r:b=r.read()
   obj=json.loads(b);assert obj['chart']['result'];(OUT/'data'/f'{sym}.json.gz').write_bytes(gzip.compress(b,mtime=0));sources.append(dict(symbol=sym,url=url,retrieved_at=datetime.now(timezone.utc).isoformat(),raw_sha256=hashlib.sha256(b).hexdigest(),status='DOWNLOADED'))
  except Exception as e:sources.append(dict(symbol=sym,url=url,status='BLOCKED',error=type(e).__name__))
 (OUT/'sources.json').write_text(json.dumps(sources,indent=2)+'\n');assert all(x['status']=='DOWNLOADED' for x in sources),'BLOCKED: no backtest'
def capped_inverse(vol):
 vol=np.asarray(vol,float)
 if np.any(~np.isfinite(vol)) or np.any(vol<=0):raise ValueError('MISSING_VOL')
 lo,hi=0.,float(max(vol)*10)
 for _ in range(100):
  mid=(lo+hi)/2
  if np.clip(mid/vol,.1,.5).sum()>1:hi=mid
  else:lo=mid
 return np.clip((lo+hi)/2/vol,.1,.5)
def weights_at(close,div,i):
 if i<252 or not np.all(np.isfinite(close[i-252:i+1])) or not np.all(np.isfinite(div[i-251:i+1])):raise ValueError('INSUFFICIENT_HISTORY')
 r=(close[i-251:i+1]+div[i-251:i+1])/close[i-252:i]-1
 return capped_inverse(np.std(r,axis=0,ddof=1))
def neff(y,lag=120):
 z=y-y.mean();n=len(z);g=z@z/n
 if g==0:return None
 lr=g+2*sum((1-k/(lag+1))*(z[k:]@z[:-k]/n) for k in range(1,min(lag,n-1)+1))
 return min(n,max(1,n*g/max(lr,1e-12)))
def frozen_path(close,div,i,w,cash,h=60):
 if i+h>=len(close):return None
 c=close[i:i+h+1];d=div[i+1:i+h+1]
 if not np.all(np.isfinite(c)) or not np.all(np.isfinite(d)):return None
 return cash+(c[1:]+np.cumsum(d,axis=0))@(w/close[i])
def load():
 dates=xc.get_calendar('XNYS',start='2000-01-01',end='2026-11-06').sessions.strftime('%Y-%m-%d');frames={};audit=[];actions=[]
 sources=json.loads((OUT/'sources.json').read_text())
 for src in sources:
  sym=src['symbol'];b=gzip.decompress((OUT/'data'/f'{sym}.json.gz').read_bytes());assert hashlib.sha256(b).hexdigest()==src['raw_sha256'];r=json.loads(b)['chart']['result'][0];q=r['indicators']['quote'][0];dd=pd.to_datetime(r['timestamp'],unit='s',utc=True).tz_convert('America/New_York').strftime('%Y-%m-%d');assert len(dd)==len(set(dd));f=pd.DataFrame(q,index=dd);f=f.loc[(f.index>=dates[0])&(f.index<=dates[-1])];assert r['meta']['currency']=='USD';assert set(f.index)==set(dates);assert f[['close','open','high','low','volume']].notna().all().all();assert ((f.low>0)&(f.low<=f.close)&(f.high>=f.close)&(f.low<=f.open)&(f.high>=f.open)).all();f=f.reindex(dates);f['div']=0.
  for kind,events in r.get('events',{}).items():
   for e in events.values():
    d=pd.to_datetime(e['date'],unit='s',utc=True).tz_convert('America/New_York').strftime('%Y-%m-%d');actions.append(dict(symbol=sym,kind=kind,date=d,record=json.dumps(e,sort_keys=True)))
    if kind=='dividends' and d in f.index:f.loc[d,'div']+=e['amount']
  frames[sym]=f;audit.append(dict(symbol=sym,first=f.index[0],last=f.index[-1],rows=len(f),gaps=0,classification='RESEARCH_PRICE_REPLAY_NOT_PIT',delisting_evidence='SURVIVING_SELECTED_TICKER_ONLY',corporate_actions='PROVIDER_REPORTED_NOT_INDEPENDENTLY_CERTIFIED'))
 write('data-audit.csv',audit);write('actions.csv',actions);return frames,list(dates)
def boot(values,L,reps=999):
 a=np.asarray(values,float);rng=np.random.default_rng(2308);n=len(a);out=[]
 for _ in range(reps):
  ix=((rng.integers(n,size=(n+L-1)//L)[:,None]+np.arange(L))%n).ravel()[:n];out.append(a[ix].mean(axis=0))
 return np.array(out)
def run():
 f,dates=load();c=np.column_stack([f[s].close for s in SYMS[:3]]);d=np.column_stack([f[s]['div'] for s in SYMS[:3]]);ret=(c[1:]+d[1:])/c[:-1]-1;qq=f['QQQ'].close.to_numpy();rows=[]
 for i in range(253,len(c)-60):
  rv=np.std(ret[i-252:i],axis=0,ddof=1);reg='UP' if qq[i]>=qq[i-199:i+1].mean() and qq[i]>qq[i-20] else ('DOWN' if qq[i]<qq[i-199:i+1].mean() and qq[i]<=qq[i-20] else 'MIXED')
  for recipe,w,cash in [('A',np.ones(3)/3,0.),('B',np.ones(3)*.2,.4),('C',weights_at(c,d,i),0.)]:
   path=frozen_path(c,d,i,w,cash);dd=1-np.r_[1,path]/np.maximum.accumulate(np.r_[1,path]);v=np.std(ret[i-20:i]@w,ddof=1)*np.sqrt(252)
   rows.append(dict(recipe=recipe,date=dates[i],index=i,maturity=dates[i+60],w_AMD=w[0],w_NVDA=w[1],w_MU=w[2],cash=cash,units_AMD=100000*w[0]/c[i,0],units_NVDA=100000*w[1]/c[i,1],units_MU=100000*w[2]/c[i,2],nav0=100000,min_nav=100000*min(path),terminal_nav=100000*path[-1],event=bool(min(path)<=.9+1e-12),scenario_DD=float(max(dd)),regime=reg,vol_bin=int(np.digitize(v,[.2,.4,.6]))))
 write('labels.csv.gz',rows);pred=[]
 for year in range(2010,2027):
  boundary=next(i for i,x in enumerate(dates) if x>=f'{year}-01-01')
  for recipe in ('A','B','C'):
   train=[r for r in rows if r['recipe']==recipe and r['maturity']<f'{year}-01-01' and r['index']<boundary-60];test=[r for r in rows if r['recipe']==recipe and r['date'][:4]==str(year)];base=(sum(r['event'] for r in train)+1)/(len(train)+2)
   assert max(r['maturity'] for r in train)<min(r['date'] for r in test)
   for r in test:
    p=dict(r,HIST=base,training_n=len(train),training_last_maturity=max(x['maturity'] for x in train))
    for model,key in [('REGIME','regime'),('VOL','vol_bin')]:
     group=[x for x in train if x[key]==r[key]];p[model]=(sum(x['event'] for x in group)+20*base)/(len(group)+20)
    pred.append(p)
 write('forecasts.csv.gz',pred);metrics=[];comparisons=[];reliability=[];summary=[]
 for recipe in ('A','B','C'):
  allr=[r for r in rows if r['recipe']==recipe];summary.append(dict(recipe=recipe,n=len(allr),frequency=float(np.mean([r['event'] for r in allr])),mean_anchor_scenario_DD=float(np.mean([r['scenario_DD'] for r in allr])),continuous_MaxDD=None,risk_budget_guaranteed=False))
  rs=[r for r in pred if r['recipe']==recipe];y=np.array([r['event'] for r in rs],float)
  for model in ('HIST','REGIME','VOL'):
   p=np.array([r[model] for r in rs]);b=(p-y)**2;ll=-y*np.log(p)-(1-y)*np.log1p(-p);samples=boot(np.c_[b,ll,y],120);ci=np.quantile(samples,[.025,.975],axis=0);metrics.append(dict(recipe=recipe,model=model,n=len(rs),brier=float(b.mean()),brier_low=ci[0,0],brier_high=ci[1,0],logloss=float(ll.mean()),base_rate=float(y.mean()),calendar_blocks120=len(rs)//120,effective_n=neff(y),logloss_low=ci[0,1],logloss_high=ci[1,1],frequency_low=ci[0,2],frequency_high=ci[1,2],calibration_bias=float((p-y).mean())))
   for k in range(10):
    mask=(p>=k/10)&(p<(k+1)/10);reliability.append(dict(recipe=recipe,model=model,bin=k,n=int(mask.sum()),p=float(p[mask].mean()) if mask.any() else None,observed=float(y[mask].mean()) if mask.any() else None))
   if model!='HIST':
    base=np.array([r['HIST'] for r in rs]);delta=b-(base-y)**2;row=dict(recipe=recipe,model=model,delta_brier=float(delta.mean()))
    for L in (60,120,180):row['low'+str(L)],row['high'+str(L)]=np.quantile(boot(delta,L),[.025,.975])
    row['p']=(1+sum(boot(delta,120)-delta.mean()<=delta.mean()))/1000;comparisons.append(row)
 order=sorted(range(6),key=lambda i:comparisons[i]['p']);running=0
 for rank,i in enumerate(order):running=max(running,(6-rank)*comparisons[i]['p']);comparisons[i]['holm_p']=min(1,running)
 write('metrics.csv',metrics);write('comparisons.csv',comparisons);write('reliability.csv',reliability);write('summary.csv',summary)
if __name__=='__main__':
 if '--acquire' in sys.argv:acquire()
 else:run()
