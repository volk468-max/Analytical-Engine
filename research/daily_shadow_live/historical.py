"""Private, revised-history comparison with identical past-only annual protocols.
No raw licensed series or individual historical predictions leave private Railway DB.
"""
import gzip,json
import numpy as np,pandas as pd
from numpy.lib.stride_tricks import sliding_window_view
from research.daily_shadow.core import calendar,canonical,sha
from research.daily_shadow_v3.adapter import EODHDAdapter,SYMBOLS,normalized_prefix
from .config import ROOT
from .bootstrap import CONTRACT

def old_frames():
 base=ROOT/'reports/market-drawdown-precursors-v1';manifest=json.loads((base/'data/manifest.json').read_text());out={}
 for src in manifest['sources']:
  if src['symbol'] not in SYMBOLS:continue
  raw=gzip.decompress((base/src['raw_file']).read_bytes())
  if sha(raw)!=src['raw_sha256']:raise ValueError('FROZEN_PREVIOUS_SOURCE_HASH_MISMATCH')
  o=json.loads(raw)['chart']['result'][0];dates=pd.to_datetime(o['timestamp'],unit='s',utc=True).tz_convert('America/New_York').strftime('%Y-%m-%d')
  out[src['symbol']]=pd.DataFrame(o['indicators']['quote'][0],index=dates)
 if set(out)!=set(SYMBOLS):raise ValueError('PREVIOUS_SIX_SYMBOL_HISTORY_INCOMPLETE')
 return out

def label(frame,h,t,field):
 anchor=frame.close.to_numpy();values=frame[field].to_numpy();out=np.full(len(anchor),np.nan)
 if len(anchor)<=h:return out
 windows=sliding_window_view(values[1:],h);valid=np.isfinite(windows).all(axis=1)&np.isfinite(anchor[:-h])
 out[:len(windows)]=np.where(valid,(windows.min(axis=1)<=anchor[:-h]*(1-t/100)).astype(float),np.nan)
 return out

def regimes(frame):
 c=frame.close;sma=c.rolling(200,min_periods=200).mean();past=c.shift(20)
 r=np.where((c>=sma)&(c>past),'UP',np.where((c<sma)&(c<=past),'DOWN','MIXED')).astype(object)
 r[~(sma.notna()&past.notna())]=None;return r

def annual_predictions(y,regime,common_valid,days,horizon):
    years=np.array([int(d[:4]) for d in days]);hist=np.full(len(days),np.nan);conditioned=hist.copy()
    for year in sorted(set(years)):
        test=np.flatnonzero(common_valid&(years==year))
        fit=np.searchsorted(days,f'{year}-01-01');train=np.flatnonzero(common_valid&(np.arange(len(days))+horizon<fit))
        if len(train)<252:continue
        p=(float(y[train].sum())+1)/(len(train)+2)
        groups={g:train[regime[train]==g] for g in ('UP','DOWN','MIXED')}
        rp={g:(float(y[idx].sum())+20*p)/(len(idx)+20) for g,idx in groups.items()}
        hist[test]=p;conditioned[test]=[rp[regime[i]] for i in test]
    return hist,conditioned

def compare_frames(old,new):
 days=calendar().sessions.strftime('%Y-%m-%d');end=min(max(f.index) for f in old.values());days=days[days<=end]
 old={s:f.reindex(days) for s,f in old.items()};new={s:f.reindex(days) for s,f in new.items()}
 ro,rn=regimes(old['QQQ']),regimes(new['QQQ']);years=np.array([int(d[:4]) for d in days]);results=[];quality=[]
 for symbol in SYMBOLS:
  a,b=old[symbol],new[symbol];both=a.close.notna()&b.close.notna();delta=((a.loc[both,'close']-b.loc[both,'close']).abs()/a.loc[both,'close'])
  quality.append(dict(symbol=symbol,common_price_dates=int(both.sum()),previous_missing=int(a.close.isna().sum()),eodhd_missing=int(b.close.isna().sum()),relative_close_difference_median=float(delta.median()) if len(delta) else None,fraction_relative_difference_gt_1e_4=float((delta>1e-4).mean()) if len(delta) else None,basis_assumption='PREVIOUS_RAW_QUOTE_ASSUMED_SPLIT_ADJUSTED; EODHD_SPLIT_ONLY_TO_COMMON_END; NOT_PIT_QUALIFIED'))
  for field in ('close','low'):
   for h in (10,20,60):
    for t in (5,10,15):
     yo,yn=label(a,h,t,field),label(b,h,t,field);valid=np.isfinite(yo)&np.isfinite(yn)&pd.notna(ro)&pd.notna(rn);forecast={('previous','HIST'):[],('previous','REGIME'):[],('EODHD','HIST'):[],('EODHD','REGIME'):[]}
     for source,y,r in [('previous',yo,ro),('EODHD',yn,rn)]:
      hp,rp=annual_predictions(y,r,valid,days,h)
      for model,p in [('HIST',hp),('REGIME',rp)]:
       selected=np.flatnonzero(np.isfinite(p));forecast[(source,model)]=[(float(p[i]),float(y[i])) for i in selected]
     from .reporting import scores
     results.append(dict(symbol=symbol,label_type='EOD_CLOSE' if field=='close' else 'LOW_INTRADAY',threshold_pct=t,horizon=h,common_eligible_labels=int(valid.sum()),label_disagreements=int(np.sum(yo[valid]!=yn[valid])),metrics={source+'_'+model:scores(data) for (source,model),data in forecast.items()}))
 return dict(classification='EXPLORATORY_REVISED_HISTORY_NOT_ORIGINAL_PIT',source_quality=quality,events=results,fit='ANNUAL_EXPANDING_SAME_COMMON_ANCHORS; LABEL_MATURITY_LT_JAN1; MIN252; BETA1_1; SHRINK20',confidence_intervals=None,independent_events=None,no_validated_advantage_claim=True)

def run_once(store,permit):
 with store.connect() as c:
  if c.execute("select exists(select 1 from alpha_operations_v4.reports where week='2000-01-01')").fetchone()[0]:return 'ALREADY_COMPLETED'
 old=old_frames();end=min(max(f.index) for f in old.values())
 adapter=EODHDAdapter(permit,network_approved=True,history_start='2000-01-01');snap=adapter.collect(end)
 if snap.legal_reason:raise ValueError('HISTORICAL_ACCESS_BLOCKED')
 ref=store.payload(CONTRACT,snap,permit.raw_until)
 new={s:pd.DataFrame(normalized_prefix(snap.bars[s],snap.splits[s],end)).set_index('date') for s in SYMBOLS}
 result=compare_frames(old,new);result.update(raw_snapshot_ref=str(ref),retrieved_at=snap.retrieved_at,source_revision=snap.revision)
 with store.connect() as c:c.execute("select alpha_operations_v4.report('2000-01-01',%s::jsonb)",(canonical(result),))
 return 'PRIVATE_COMPARISON_RECORDED'
