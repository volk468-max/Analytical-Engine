"""Frozen data helpers and causal price-only features, never target-informed."""
import csv,gzip,hashlib,io,json
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'reports/market-drawdown-precursors-v1';MARKET=('SPY','QQQ','SOXX');STOCK=('AMD','NVDA','MU');SYMBOLS=MARKET+STOCK
TASKS=((5,10),(10,10),(5,20),(10,20),(5,60),(10,60))
BASE_KEYS=('log_rv20','qqq_ma200','qqq_r20','spy_ma200','spy_r20')
M_KEYS=('qqq_spy_relative20','qqq_vol_ratio','spy_vol_ratio');S_KEYS=('sector_relative20','sector_vol_ratio')
X_KEYS=('own_ma50','own_r60','stock_relative20','own_vol_ratio')
MODEL_KEYS={'VOL':('log_rv20',),'SIMPLE':BASE_KEYS,'PLUS_M':BASE_KEYS+M_KEYS,'PLUS_S':BASE_KEYS+S_KEYS,'MINIMAL':BASE_KEYS+M_KEYS+S_KEYS,'PLUS_X':BASE_KEYS+M_KEYS+S_KEYS+X_KEYS}
M_FLAGS=('market_relative_weakness','market_vol_acceleration','sector_relative_weakness','sector_vol_acceleration');X_FLAGS=('stock_extension','stock_relative_weakness','stock_vol_acceleration')

def write(name,rows):
    rows=list(rows)
    if not rows:return
    s=io.StringIO(newline='');w=csv.DictWriter(s,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows);data=s.getvalue().encode();(OUT/name).write_bytes(gzip.compress(data,mtime=0) if name.endswith('.gz') else data)
def read(name):
    if name.endswith('.gz'):
        with gzip.open(OUT/name,'rt') as f:return list(csv.DictReader(f))
    with (OUT/name).open() as f:return list(csv.DictReader(f))
def check_sources():
    reg=json.loads((OUT/'protocol-registration.json').read_text());assert hashlib.sha256((OUT/'protocol.md').read_bytes()).hexdigest()==reg['protocol_sha256']
    m=json.loads((OUT/'data/manifest.json').read_text())
    for name,digest in m['artifacts'].items():assert hashlib.sha256((OUT/name).read_bytes()).hexdigest()==digest,name
    return m

def load_bars():
    check_sources();rs=read('data/prices.csv.gz');calendar=read('data/calendar.csv');dates=[r['date'] for r in calendar];bars={s:pd.DataFrame([r for r in rs if r['symbol']==s]).set_index('date') for s in SYMBOLS}
    for df in bars.values():
        for k in ('open','high','low','close','volume'):df[k]=df[k].astype(float)
    return bars,dates,calendar

def feature_frame(df):
    c=df['close'];r=np.log(c).diff();rv20=r.rolling(20).std(ddof=1)*np.sqrt(252);rv60=r.rolling(60).std(ddof=1)*np.sqrt(252)
    return pd.DataFrame(dict(r20=c/c.shift(20)-1,r60=c/c.shift(60)-1,ma50=c/c.rolling(50).mean()-1,ma200=c/c.rolling(200).mean()-1,rv20=rv20,vol_ratio=rv20/rv60,drawdown=c/c.cummax()-1,warm=c.rolling(252).count()==252))

def build_panel(bars,dates):
    f={s:feature_frame(bars[s]).reindex(dates) for s in SYMBOLS};out={s:[] for s in SYMBOLS};lookup={d:i for i,d in enumerate(dates)}
    q=f['QQQ'];p=f['SPY'];sec=f['SOXX'];shared=pd.DataFrame(dict(qqq_log_rv20=np.log(q['rv20']),qqq_ma200=q['ma200'],qqq_r20=q['r20'],spy_ma200=p['ma200'],spy_r20=p['r20'],qqq_spy_relative20=q['r20']-p['r20'],qqq_vol_ratio=q['vol_ratio'],spy_vol_ratio=p['vol_ratio'],sector_relative20=sec['r20']-q['r20'],sector_vol_ratio=sec['vol_ratio']))
    for symbol in SYMBOLS:
        own=f[symbol]
        for date,r in shared.iterrows():
            i=lookup[date]
            if not bool(own.loc[date,'warm']==True) or not bool(sec.loc[date,'warm']==True) or not np.all(np.isfinite(r.values)):continue
            rr=own.loc[date];vals=dict(r)
            vals.update(log_rv20=float(np.log(rr['rv20'])),own_ma50=float(rr['ma50']),own_r60=float(rr['r60']),stock_relative20=float(rr['r20']-q.loc[date,'r20']),own_vol_ratio=float(rr['vol_ratio']))
            if not all(np.isfinite(x) for x in vals.values()):continue
            flag=dict(market_relative_weakness=vals['qqq_spy_relative20']<=-.03,market_vol_acceleration=max(vals['qqq_vol_ratio'],vals['spy_vol_ratio'])>=1.10,sector_relative_weakness=vals['sector_relative20']<=-.03,sector_vol_acceleration=vals['sector_vol_ratio']>=1.10,stock_extension=vals['own_ma50']>=.10 and vals['own_r60']>=.20,stock_relative_weakness=vals['stock_relative20']<=-.05,stock_vol_acceleration=vals['own_vol_ratio']>=1.10)
            regime='UP' if vals['qqq_ma200']>=0 and vals['qqq_r20']>0 else ('DOWN' if vals['qqq_ma200']<0 and vals['qqq_r20']<=0 else 'MIXED')
            out[symbol].append(dict(symbol=symbol,population='MARKET' if symbol in MARKET else 'STOCK',date=date,calendar_index=i,decision_at=bars[symbol].loc[date,'available_at'],market_regime=regime,near_high=bool(rr['drawdown']>=-.02),**{k:float(v) for k,v in vals.items()},**flag))
    return out

def label(bars,date,threshold,horizon,target):
    # All price rows must follow consecutive exchange sessions, guaranteed by audit.
    idx=bars.index.get_loc(date);end=idx+horizon
    if end>=len(bars):return None,None
    future=bars.iloc[idx+1:end+1];anchor=float(bars.iloc[idx]['close']);value=float(future['low'].min()) if target=='TOUCH' else float(future.iloc[-1]['close'])
    return float(value<=anchor*(1-threshold/100)+anchor*1e-12),str(future.iloc[-1]['available_at'])

def era(date):
    y=int(date[:4])
    for a,b in ((2000,2002),(2003,2007),(2008,2009),(2010,2019),(2020,2020),(2021,2021),(2022,2022),(2023,2026)):
        if a<=y<=b:return str(a) if a==b else f'{a}-{b}'
    return 'OTHER'
