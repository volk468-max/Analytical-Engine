"""Owner-authorized preliminary replay, not PIT certification or deployable model.
No network calls; original v1 output files are never modified.
"""
import csv,gzip,hashlib,io,json,math
from pathlib import Path
from decimal import Decimal,ROUND_HALF_UP
import numpy as np
import pandas as pd
import exchange_calendars as xc
try:
 from .calibration import calibrate,logistic,logit
except ImportError:
 from calibration import calibrate,logistic,logit
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'reports/model-portfolios-eod-v1'
OUT=ROOT/'reports/eod-calibration-ledger-v2'
SYMS=('AMD','NVDA','MU','QQQ');MODELS=('HIST','REGIME','VOL')
CLASS='PRELIMINARY_RESEARCH_PRICE_REPLAY_NOT_PIT'

def write(name,rows):
 rows=list(rows)
 if not rows:raise ValueError('EMPTY_OUTPUT:'+name)
 out=io.StringIO();w=csv.DictWriter(out,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows);b=out.getvalue().encode()
 (OUT/name).write_bytes(gzip.compress(b,mtime=0) if name.endswith('.gz') else b)

def verified_bytes(path,expected):
 b=gzip.decompress(path.read_bytes())
 if hashlib.sha256(b).hexdigest()!=expected:raise ValueError('SOURCE_HASH_MISMATCH')
 return b

def rounding_check(independent,provider,exdate,provider_date):
 a,b=Decimal(independent),Decimal(provider);unit=Decimal('.001')
 return dict(difference=str(a-b),half_unit=str(unit/2),rounded=str(a.quantize(unit,rounding=ROUND_HALF_UP)),compatible=bool(exdate==provider_date and a.quantize(unit,rounding=ROUND_HALF_UP)==b and abs(a-b)<=unit/2),vendor_policy_confirmed=False,fully_qualified=False)

def validate_frame(frame,dates):
 if not frame.index.is_unique:raise ValueError('DUPLICATE_SESSION')
 if set(frame.index)!=set(dates):raise ValueError('SESSION_GAP')
 f=frame.reindex(dates)
 if not np.isfinite(f[['close','open','low','high']].to_numpy()).all() or (f[['close','open','low','high']]<=0).any().any():raise ValueError('INVALID_PRICE')
 if ((f.low>f.close)|(f.high<f.close)|(f.low>f.open)|(f.high<f.open)).any():raise ValueError('INVALID_OHLC')
 return f

def load_prices():
 dates=xc.get_calendar('XNYS',start='2000-01-01',end='2026-11-06').sessions.strftime('%Y-%m-%d').tolist();frames={};actions=[]
 for src in json.loads((BASE/'sources.json').read_text()):
  r=json.loads(verified_bytes(BASE/'data'/(src['symbol']+'.json.gz'),src['raw_sha256']))['chart']['result'][0]
  if r['meta']['currency']!='USD':raise ValueError('NON_USD')
  dd=pd.to_datetime(r['timestamp'],unit='s',utc=True).tz_convert('America/New_York').strftime('%Y-%m-%d')
  f=pd.DataFrame(r['indicators']['quote'][0],index=dd);f=f.loc[(f.index>=dates[0])&(f.index<=dates[-1])];f=validate_frame(f,dates);f['div']=0.
  for kind,events in r.get('events',{}).items():
   for e in events.values():
    d=pd.to_datetime(e['date'],unit='s',utc=True).tz_convert('America/New_York').strftime('%Y-%m-%d');actions.append(dict(symbol=src['symbol'],kind=kind,date=d,record=e))
    if kind=='dividends' and d in f.index:
     if e['amount']<0:raise ValueError('INVALID_DIVIDEND')
     f.loc[d,'div']+=e['amount']
  frames[src['symbol']]=f
 return frames,dates,actions

def capped(vol):
 vol=np.asarray(vol,float)
 if not np.isfinite(vol).all() or (vol<=0).any():raise ValueError('VOL_SUPPORT')
 lo,hi=0.,max(vol)*10
 for _ in range(100):
  x=(lo+hi)/2
  if np.clip(x/vol,.1,.5).sum()>1:hi=x
  else:lo=x
 return np.clip((lo+hi)/2/vol,.1,.5)

def weights(c,d,i,recipe):
 if recipe=='A':return np.ones(3)/3
 if recipe=='B':return np.ones(3)*.2
 if recipe!='C' or i<252:raise ValueError('WEIGHT_WARMUP')
 r=(c[i-251:i+1]+d[i-251:i+1])/c[i-252:i]-1
 return capped(np.std(r,axis=0,ddof=1))

def frozen_label(c,d,i,w):
 if i+60>=len(c):raise ValueError('IMMATURE_LABEL')
 path=1-w.sum()+(c[i+1:i+61]+np.cumsum(d[i+1:i+61],axis=0))@(w/c[i])
 return bool(path.min()<=.9+1e-12),float(path.min())

def load_labels(frames,dates):
 rs=pd.read_csv(BASE/'labels.csv.gz');rs['y']=rs.event.astype(int)
 if rs.duplicated(['recipe','date']).any():raise ValueError('DUPLICATE_LABEL')
 c=np.column_stack([frames[s].close for s in SYMS[:3]]);d=np.column_stack([frames[s]['div'] for s in SYMS[:3]]);checks=0
 for row in rs.itertuples():
  i=row.index
  if dates[i]!=row.date or i+60>=len(dates) or dates[i+60]!=row.maturity:raise ValueError('LABEL_CALENDAR_OR_MATURITY')
  w=weights(c,d,i,row.recipe);y,minimum=frozen_label(c,d,i,w)
  if y!=row.y or not np.isclose(minimum*100000,row.min_nav,atol=1e-7,rtol=1e-12):raise ValueError('FROZEN_LABEL_RECONSTRUCTION')
  if not np.allclose(w,[row.w_AMD,row.w_NVDA,row.w_MU],atol=1e-12):raise ValueError('FROZEN_WEIGHTS_RECONSTRUCTION')
  qq=frames['QQQ'].close.to_numpy();reg='UP' if qq[i]>=qq[i-199:i+1].mean() and qq[i]>qq[i-20] else ('DOWN' if qq[i]<qq[i-199:i+1].mean() and qq[i]<=qq[i-20] else 'MIXED')
  r=(c[i-19:i+1]+d[i-19:i+1])/c[i-20:i]-1;vb=int(np.digitize(np.std(r@w,ddof=1)*np.sqrt(252),[.2,.4,.6]))
  if reg!=row.regime or vb!=row.vol_bin:raise ValueError('FROZEN_FEATURE_RECONSTRUCTION')
  checks+=1
 return rs,c,d,dict(all_labels_reconstructed=checks,label_file_sha256=hashlib.sha256((BASE/'labels.csv.gz').read_bytes()).hexdigest())

def windows(rows,year,dates):
 tb=next(i for i,d in enumerate(dates) if d>=f'{year-3}-01-01');vb=next(i for i,d in enumerate(dates) if d>=f'{year}-01-01')
 tr=rows[(rows['index']<tb-60)&(rows.maturity<f'{year-3}-01-01')]
 ca=rows[(rows['index']>=tb+60)&(rows.date<f'{year}-01-01')&(rows.maturity<dates[vb-60])]
 te=rows[(rows['index']>=vb+60)&(rows.date.str[:4]==str(year))]
 return tr,ca,te

def bank(train,rows,model):
 if train.empty:raise ValueError('EMPTY_TRAIN')
 base=(train.y.sum()+1)/(len(train)+2)
 if model=='HIST':return np.full(len(rows),base)
 key={'REGIME':'regime','VOL':'vol_bin'}[model];groups=train.groupby(key).y.agg(['sum','count'])
 return np.array([(groups.loc[v,'sum']+20*base)/(groups.loc[v,'count']+20) if v in groups.index else base for v in rows[key]])

def fit_year(rows,year,dates):
 tr,ca,te=windows(rows,year,dates);blocks=len(set((ca['index']-ca['index'].min())//120)) if len(ca) else 0
 support=dict(year=year,train_n=len(tr),cal_n=len(ca),test_n=len(te),cal_events=int(ca.y.sum()),cal_blocks120=blocks,train_last_maturity=tr.maturity.max() if len(tr) else None,cal_last_maturity=ca.maturity.max() if len(ca) else None)
 if len(ca)<240 or min(ca.y.sum(),len(ca)-ca.y.sum())<10 or blocks<4 or tr.empty or te.empty:return [],dict(support,status='INSUFFICIENT_SUPPORT')
 assert tr.maturity.max()<ca.date.min() and ca.maturity.max()<te.date.min()
 result=te[['recipe','date','index','maturity','y','regime']].to_dict('records')
 for model in MODELS:
  cp=bank(tr,ca,model);p=bank(tr,te,model);a=calibrate(cp.tolist(),ca.y.tolist())
  for r,raw in zip(result,p):r[model+'_raw']=float(raw);r[model+'_cal']=logistic(logit(raw)+a)
  support[model+'_intercept']=a
 for r in result:
  cut=(pd.Timestamp(r['date'])-pd.DateOffset(years=5)).strftime('%Y-%m-%d');known=rows[(rows.maturity<r['date'])&(rows.date>=cut)]
  r['CLIM']=(known.y.sum()+1)/(len(known)+2);r['clim_n']=len(known);r['clim_last_maturity']=known.maturity.max();r['base_fit_cutoff']=f'{year-3}-01-01';r['cal_fit_cutoff']=dates[next(i for i,x in enumerate(dates) if x>=f'{year}-01-01')-60];r['score_kind']=CLASS
 return result,dict(support,status='SUPPORTED')

def hac(y,lag=120):
 y=np.asarray(y,float);z=y-y.mean();n=len(z);g=z@z/n
 if not g:return None
 lr=g+2*sum((1-k/(lag+1))*np.dot(z[k:],z[:-k])/n for k in range(1,min(lag,n-1)+1))
 return float(min(n,max(1,n*g/max(lr,1e-12))))

def calendar_neff(y,indices,total,lag=120):
 """HAC with missing session positions retained; descriptive effective support."""
 y=np.asarray(y,float);indices=np.asarray(indices,int)
 if len(y)<2 or len(set(indices))!=len(y):return None
 z=np.zeros(total);z[indices]=y-y.mean();g=float(z@z/len(y))
 if g<=0:return None
 lr=g+2*sum((1-k/(lag+1))*np.dot(z[k:],z[:-k])/len(y) for k in range(1,min(lag,total-1)+1))
 return float(min(len(y),max(1,len(y)*g/max(lr,1e-12))))

def disjoint_windows(indices,h=60):
 chosen=[]
 for i in sorted(indices):
  if not chosen or i>=chosen[-1]+h:chosen.append(int(i))
 return chosen

def boot_calendar(values,indices,total,L,reps=9999):
 """Synchronous resampling; gaps have zero count, never compressed into time."""
 v=np.asarray(values,float)
 if v.ndim==1:v=v[:,None]
 sums=np.zeros((total,v.shape[1]));np.add.at(sums,indices,v);counts=np.bincount(indices,minlength=total);rng=np.random.default_rng(2509);out=[]
 # Blocks sums permit fast9999 resamples without allocating reps*dates*models.
 circle=np.vstack([sums,sums[:L-1]]);cs=np.vstack([np.zeros((1,v.shape[1])),np.cumsum(circle,axis=0)]);cn=np.r_[0,np.cumsum(np.r_[counts,counts[:L-1]])]
 k,tail=divmod(total,L)
 for _ in range(reps):
  starts=rng.integers(total,size=k+(tail>0));ends=starts+L
  if tail:ends[-1]=starts[-1]+tail
  n=(cn[ends]-cn[starts]).sum()
  if n:out.append((cs[ends]-cs[starts]).sum(axis=0)/n)
 return np.array(out)

def holm(rows):
 order=sorted(range(len(rows)),key=lambda i:rows[i]['p']);running=0
 for rank,i in enumerate(order):running=max(running,(len(rows)-rank)*rows[i]['p']);rows[i]['holm_p']=min(1.,running)

def auc(y,p):
 if min(sum(y),len(y)-sum(y))==0:return None
 ranks=pd.Series(p).rank().to_numpy();n=sum(y);return float((ranks[np.asarray(y,bool)].sum()-n*(n+1)/2)/(n*(len(y)-n)))

def evaluate(pred,dates):
 metrics=[];reliability=[];thresholds=[];families={'CAL_V_RAW':[],'CAL_V_CLIM':[]};breakdown=[]
 for recipe in 'ABC':
  r=pred[pred.recipe==recipe].sort_values('date');y=r.y.to_numpy(float);indices=r['index'].to_numpy()-r['index'].min();total=int(indices.max()+1);keys=[m+s for m in MODELS for s in ('_raw','_cal')]+['CLIM'];ps=r[keys].to_numpy();b=(ps-y[:,None])**2;q=np.clip(ps,1e-8,1-1e-8);ll=-y[:,None]*np.log(q)-(1-y[:,None])*np.log1p(-q);bias=ps-y[:,None];values=np.c_[b,ll,bias,np.repeat(y[:,None],len(keys),axis=1)];boots={L:boot_calendar(values,indices,total,L) for L in (60,120,180)};K=len(keys)
  for j,key in enumerate(keys):
   p=ps[:,j];ci=np.quantile(boots[120][:,j],[.025,.975]);freqci=np.quantile(boots[120][:,3*K+j],[.025,.975]);ece=0.
   for k in range(10):
    mask=(p>=k/10)&((p<(k+1)/10) if k<9 else p<=1);n=int(mask.sum());fr=float(y[mask].mean()) if n else None;meanp=float(p[mask].mean()) if n else None
    if n:ece+=n/len(y)*abs(meanp-fr)
    reliability.append(dict(recipe=recipe,model=key,bin=k,n=n,mean_p=meanp,event_frequency=fr,effective_n=calendar_neff(y[mask],indices[mask],total) if n else None,support='GAPS_OR_DEPENDENCE; NOT_INDEPENDENT_BINOMIAL'))
   metrics.append(dict(recipe=recipe,model=key,n=len(y),first=r.date.min(),last=r.date.max(),base_rate=float(y.mean()),frequency_low=freqci[0],frequency_high=freqci[1],brier=float(b[:,j].mean()),brier_low=ci[0],brier_high=ci[1],logloss=float(ll[:,j].mean()),logloss_low=float(np.quantile(boots[120][:,K+j],.025)),logloss_high=float(np.quantile(boots[120][:,K+j],.975)),bias=float(bias[:,j].mean()),bias_low=float(np.quantile(boots[120][:,2*K+j],.025)),bias_high=float(np.quantile(boots[120][:,2*K+j],.975)),ece10=ece,auc=auc(y,p),slope=None,slope_status='LOW_EFFECTIVE_SUPPORT_OR_FROZEN_BANK_TIES; NOT_FITTED',effective_n=calendar_neff(y,indices,total),disjoint60_windows=len(disjoint_windows(indices)),disjoint60_hits=sum(y[np.isin(indices,disjoint_windows(indices))]),observed_blocks120=len(set(indices//120)),independent_market_events='UNKNOWN'))
   for threshold in (.35,.51,.60):
    mask=p>=threshold;n=int(mask.sum());cols=np.c_[mask*y,mask];bs=boot_calendar(cols,indices,total,120,reps=9999);supported=bs[:,1]>0;ratio=bs[supported,0]/bs[supported,1];lo,hi=np.quantile(ratio,[.025,.975]) if len(ratio) else (None,None)
    support_ok=n>=20 and min(y[mask].sum(),n-y[mask].sum())>=10 and len(set(indices[mask]//120))>=4
    if not support_ok:lo=hi=None
    thresholds.append(dict(recipe=recipe,model=key,threshold=threshold,n=n,observed_frequency=float(y[mask].mean()) if n else None,mean_p=float(p[mask].mean()) if n else None,low=lo,high=hi,calendar_blocks120=len(set(indices[mask]//120)),effective_n=calendar_neff(y[mask],indices[mask],total) if n else None,status='NOT VALIDATED',ci_kind='DEPENDENT_DESCRIPTIVE_SELECTED_SUBSET' if support_ok else 'INSUFFICIENT_SUPPORT_NO_INTERVAL'))
   for period,mask in [('2013-2019',r.date<'2020-01-01'),('2020-2026',r.date>='2020-01-01')]+[(x,r.regime==x) for x in ('UP','DOWN','MIXED')]:
    if mask.any():breakdown.append(dict(recipe=recipe,model=key,period_or_regime=period,n=int(mask.sum()),brier=float(b[mask,j].mean()),logloss=float(ll[mask,j].mean()),bias=float(bias[mask,j].mean())))
  for m in MODELS:
   j=keys.index(m+'_cal')
   for family,k in [('CAL_V_RAW',keys.index(m+'_raw')),('CAL_V_CLIM',keys.index('CLIM'))]:
    delta=float((b[:,j]-b[:,k]).mean());row=dict(family=family,recipe=recipe,model=m,delta_brier=delta,relative_gain=-delta/float(b[:,k].mean()),delta_logloss=float((ll[:,j]-ll[:,k]).mean()))
    for L in (60,120,180):row['low'+str(L)],row['high'+str(L)]=np.quantile(boots[L][:,j]-boots[L][:,k],[.025,.975])
    draws=boots[120][:,j]-boots[120][:,k];row['p']=(1+int(((draws-delta)<=delta).sum()))/(len(draws)+1);families[family].append(row)
 for family,rows in families.items():holm(rows)
 rank_rows=[]
 for recipe in 'ABC':
  for year in range(2013,2027):
   r=pred[(pred.recipe==recipe)&(pred.date.str[:4]==str(year))]
   if len(r):
    for model in MODELS:rank_rows.append(dict(recipe=recipe,year=year,model=model,auc_raw=auc(r.y.to_numpy(),r[model+'_raw'].to_numpy()),auc_cal=auc(r.y.to_numpy(),r[model+'_cal'].to_numpy()),interpretation='INTERCEPT_PRESERVES_WITHIN_FROZEN_YEAR_RANKING'))
 write('ranking-by-year.csv',rank_rows)
 write('calibration-metrics.csv',metrics);write('reliability.csv',reliability);write('thresholds.csv',thresholds);write('comparisons.csv',[x for rows in families.values() for x in rows]);write('period-regime-metrics.csv',breakdown)
 return metrics,families

def rebalance(units,cash,receivable,price,w,rate):
 """Targets use pretrade NAV; all sells fund buys, never use receivables."""
 units=np.asarray(units,float).copy();price=np.asarray(price,float);w=np.asarray(w,float)
 if (w<0).any() or w.sum()>1+1e-10 or cash<-1e-8 or receivable<0:raise ValueError('INVALID_ACCOUNT')
 nav=float(units@price+cash+receivable);desired=nav*w;positions=units*price;sell=np.maximum(positions-desired,0.);notional=float(sell.sum());cash+=notional*(1-rate);units-=sell/price;buy=np.maximum(desired-units*price,0.);wanted=float(buy.sum());scale=min(1.,max(0.,cash)/(wanted*(1+rate))) if wanted else 1.;buy*=scale;cash-=float(buy.sum())*(1+rate);units+=buy/price;notional+=float(buy.sum());fees=notional*rate
 if cash<-1e-7 or (units<-1e-10).any():raise ValueError('LEVERAGE')
 assert np.isclose(units@price+cash+receivable,nav-fees,atol=1e-7)
 return units,max(0.,cash),notional,fees

def ledger(c,d,dates,recipe,fee_bps=0,spread_bps=0,payments=None,start=253):
 """Split-normalized numeraire; actions are memos, not a second share adjustment."""
 units=np.zeros(3);cash=100000.;pending=[];rows=[];previous_nav=100000.;hwm=100000.;totalfees=0.;payments=payments or {};target=None;decision=None;rate=(fee_bps+spread_bps)/10000
 for i in range(start,len(dates)):
  excredited=float(units@d[i]);
  for j in range(3):
   value=float(units[j]*d[i,j])
   if value:pending.append(dict(amount=value,pay=payments.get((SYMS[j],dates[i]))))
  paid=sum(x['amount'] for x in pending if x['pay'] is not None and x['pay']<=dates[i]);cash+=paid;pending=[x for x in pending if x['pay'] is None or x['pay']>dates[i]];receivable=sum(x['amount'] for x in pending);traded=fee=0.
  if i==start:target=weights(c,d,i-1,recipe[0]);decision=dates[i-1]
  execution_decision=decision if target is not None else None
  if target is not None:
   units,cash,traded,fee=rebalance(units,cash,receivable,c[i],target,rate);target=None;totalfees+=fee
  nav=float(units@c[i]+cash+receivable);hwm=max(hwm,nav)
  rows.append(dict(recipe=recipe,fee_bps=fee_bps,spread_bps=spread_bps,date=dates[i],index=i,nav=nav,cash=cash,receivable=receivable,units_AMD=units[0],units_NVDA=units[1],units_MU=units[2],stock_exposure=float(units@c[i])/nav,cash_exposure=cash/nav,receivable_exposure=receivable/nav,dividend_accrued=excredited,dividend_paid=paid,traded_notional=traded,fees=fee,cumulative_fees=totalfees,hwm=hwm,drawdown=1-nav/hwm,daily_return=nav/previous_nav-1,execution_decision_date=execution_decision,classification='DESCRIPTIVE_NON_EXECUTABLE'))
  previous_nav=nav
  # First session close of month decides, next session close executes.
  if not recipe.endswith('_STATIC') and i>start and dates[i][:7]!=dates[i-1][:7]:target=weights(c,d,i,recipe);decision=dates[i]
 return rows

def episodes(mask):
 lengths=[];n=0
 for b in mask:
  if b:n+=1
  elif n:lengths.append(n);n=0
 if n:lengths.append(n)
 return lengths

def economics(rows,period='FULL',initial=100000.):
 r=pd.DataFrame(rows);nav=r.nav.to_numpy();path=np.r_[initial,nav];dd=1-path/np.maximum.accumulate(path);ret=path[1:]/path[:-1]-1;years=len(nav)/252;breach=episodes(dd[1:]>.15+1e-12);under=episodes(dd[1:]>1e-12);ratio60=path[60:]/path[:-60]-1
 return dict(recipe=r.recipe.iloc[0],fee_bps=int(r.fee_bps.iloc[0]),spread_bps=int(r.spread_bps.iloc[0]),period=period,start=r.date.iloc[0],end=r.date.iloc[-1],initial_nav=initial,terminal_nav=float(nav[-1]),cagr=float((nav[-1]/initial)**(1/years)-1),annual_vol=float(np.std(ret,ddof=1)*np.sqrt(252)),max_dd=float(dd.max()),days_below_hwm=int(sum(dd[1:]>1e-12)),longest_hwm_duration=max(under,default=0),breach15_episodes=len(breach),breach15_days=sum(breach),breach15_longest=max(breach,default=0),worst60_return=float(ratio60.min()) if len(ratio60) else None,turnover=float((r.traded_notional/r.nav).sum()),fees=float(r.fees.sum()),mean_stock_exposure=float(r.stock_exposure.mean()),mean_cash_exposure=float(r.cash_exposure.mean()),mean_receivable_exposure=float(r.receivable_exposure.mean()),terminal_receivable=float(r.receivable.iloc[-1]),execution='NON_EXECUTABLE',independent_events='UNKNOWN')

def run():
 frames,dates,actions=load_prices();rs,c,d,reconstruction=load_labels(frames,dates);pred=[];support=[]
 for recipe in 'ABC':
  rows=rs[rs.recipe==recipe]
  for year in range(2013,2027):
   result,info=fit_year(rows,year,dates);support.append(dict(recipe=recipe,**info));pred.extend(result)
 pred=pd.DataFrame(pred);common=set.intersection(*(set(pred[pred.recipe==r].date) for r in 'ABC'));pred=pred[pred.date.isin(common)].sort_values(['recipe','date']);write('forecast-calibration.csv.gz',pred.to_dict('records'));write('window-support.csv',support)
 metrics,families=evaluate(pred,dates)
 all_ledgers=[];stats=[]
 # Verified single event only. All other payment dates explicitly unknown.
 payments={('MU','2024-10-07'):'2024-10-23'}
 audit=json.loads((OUT/'action-reconciliation.json').read_text())
 if not audit['MU_sample_reconciled']:raise ValueError('MU_PAYMENT_EVIDENCE_REQUIRED')
 for recipe in ('A','B','C','A_STATIC','B_STATIC'):
  for fee in (0,10,25):
   for spread in (0,5):
    lr=ledger(c,d,dates,recipe,fee,spread,payments);all_ledgers.extend(lr);stats.append(economics(lr))
    for start,end,name in [('2013-01-01','2019-12-31','2013-2019'),('2020-01-01','2026-12-31','2020-2026')]:
     sub=[x for x in lr if start<=x['date']<=end];i=next(i for i,x in enumerate(lr) if x['date']==sub[0]['date']);stats.append(economics(sub,name,initial=lr[i-1]['nav']))
 write('continuous-ledgers.csv.gz',all_ledgers);write('ledger-economics.csv',stats)
 drag=[]
 for static in ('','_STATIC'):
  for fee in (0,10,25):
   for spread in (0,5):
    a=next(x for x in stats if x['recipe']=='A'+static and x['fee_bps']==fee and x['spread_bps']==spread and x['period']=='FULL');b=next(x for x in stats if x['recipe']=='B'+static and x['fee_bps']==fee and x['spread_bps']==spread and x['period']=='FULL');drag.append(dict(comparison='B'+static+' versus A'+static,fee_bps=fee,spread_bps=spread,terminal_opportunity_cost_usd=a['terminal_nav']-b['terminal_nav'],cagr_gap=a['cagr']-b['cagr'],max_dd_reduction=a['max_dd']-b['max_dd'],interpretation='EXPOSURE_DIFFERENCE_NOT_MODEL_ALPHA_OR_FALSE_ALERT_COST'))
 write('cash-reserve-cost.csv',drag)
 summary=dict(classification=CLASS,qualified=False,protocol_sha256=hashlib.sha256((OUT/'protocol-supplement.md').read_bytes()).hexdigest(),price_source_hashes=json.loads((BASE/'sources.json').read_text()),reconstruction=reconstruction,common_forecast_dates=len(common),total_forecasts=len(pred),first_test=pred.date.min(),last_test=pred.date.max(),support_exclusions=[x for x in support if x['status']!='SUPPORTED'],independent_market_events=None,bootstrap_reps=9999,bootstrap_interpretation='CONDITIONAL_ON_FROZEN_FITS; shared date blocks across assets/models; not independent holdout',unknown_payment_dates='ALL_EXCEPT_MU_2024_10_07; nonspendable receivables0interest',real_trades=False)
 (OUT/'run-manifest.json').write_text(json.dumps(summary,indent=2)+'\n')
 print(json.dumps(dict(forecasts=len(pred),common_dates=len(common),ledger_rows=len(all_ledgers),supported_years=sum(x['status']=='SUPPORTED' for x in support)),indent=2))

if __name__=='__main__':run()
