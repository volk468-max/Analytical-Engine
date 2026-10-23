"""Publication-gated extensions to the unchanged PR #3 diagnostics."""
import csv,hashlib,json
from math import log,sqrt
from pathlib import Path
from statistics import stdev
from aae.backtest.simulator import Bar,Observation
from aae.backtest.diagnostics import features as v2_diagnostic_features
from .risk_signal_v3 import REQUIRED,OPTIONAL

DATA=Path('data/risk-signal-v3')


def wilder_rsi(closes,period=14):
    if len(closes)<=period:return None
    changes=[b-a for a,b in zip(closes,closes[1:])]
    gain=sum(max(x,0) for x in changes[:period])/period
    loss=sum(max(-x,0) for x in changes[:period])/period
    for x in changes[period:]:
        gain=(gain*(period-1)+max(x,0))/period
        loss=(loss*(period-1)+max(-x,0))/period
    if not gain and not loss:return 50.0
    return 100 if not loss else 100-100/(1+gain/loss)


def load_pack():
    manifest=json.loads((DATA/'manifest.json').read_text())
    for name,digest in manifest['artifact_sha256'].items():
        if hashlib.sha256((DATA/name).read_bytes()).hexdigest()!=digest:raise ValueError('Source checksum: '+name)
    rows=list(csv.DictReader((DATA/'bars.csv').open()))
    if {r['price_basis'] for r in rows}!={'provider_split_adjusted_ohlc'}:raise ValueError('Mixed price bases')
    bars=[Bar(r['symbol'],r['open_at'],r['close_at'],r['available_at'],
              *[float(r[k]) for k in ('open','high','low','close')],r['source'],False) for r in rows]
    if any(b.close_at.date().isoformat()>'2026-10-22' for b in bars):raise ValueError('Incomplete/future session')
    markets=[Observation(**r) for r in json.loads((DATA/'markets.json').read_text())]
    return bars,markets,manifest


def build_features(stock,markets,qqq,sox=()):
    stock=sorted(stock,key=lambda b:b.close_at)
    if any(a.available_at>=b.available_at for a,b in zip(stock,stock[1:])):raise ValueError('Nonmonotone price publications')
    rows=v2_diagnostic_features(stock,markets,qqq)
    sox_by_date={b.close_at.date():b for b in sox}
    rv20=[]
    for index,row in enumerate(rows):
        at=stock[index].available_at
        known=[b for b in stock[:index+1] if b.available_at<=at]
        closes=[b.close for b in known]
        returns=[log(b/a) for a,b in zip(closes,closes[1:])]
        volatility={n:stdev(returns[-n:])*sqrt(252)*100 if len(returns)>=n else None for n in (20,60)}
        rv20.append(volatility[20])
        slope={};change={}
        for n in (20,50):
            current=row[f'ma{n}'];previous=rows[index-5][f'ma{n}'] if index>=5 else None
            earlier=rows[index-10][f'ma{n}'] if index>=10 else None
            slope[n]=(current/previous-1)*100 if current is not None and previous else None
            old=(previous/earlier-1)*100 if previous is not None and earlier else None
            change[n]=slope[n]-old if slope[n] is not None and old is not None else None
        prior_vol=rv20[index-5] if index>=5 else None
        vol_change=(volatility[20]/prior_vol-1) if prior_vol else (0 if prior_vol==0 and volatility[20]==0 else None)
        current_sox=sox_by_date.get(stock[index].close_at.date())
        old_sox=sox_by_date.get(stock[index-20].close_at.date()) if index>=20 else None
        valid_sox=current_sox and old_sox and current_sox.available_at<=at and old_sox.available_at<=at
        semi_return=(current_sox.close/old_sox.close-1)*100 if valid_sox else None
        indicators={k:row.get(k) for k in REQUIRED+OPTIONAL}
        indicators.update(rsi14=wilder_rsi(closes),ma20_slope_5_pct=slope[20],ma50_slope_5_pct=slope[50],
            ma20_slope_change_pp=change[20],ma50_slope_change_pp=change[50],rv20_pct=volatility[20],
            rv60_pct=volatility[60],rv20_change_5_ratio=vol_change,
            relative_return_qqq20_pp=row['relative_return_20_pp'],
            relative_return_sox20_pp=row['return_20_pct']-semi_return if semi_return is not None and row['return_20_pct'] is not None else None)
        quality=dict(quote_observed_at=row['observed_at'],quote_available_at=row['decision_at'],
            qqq_observed_at=row['qqq_observed_at'],qqq_available_at=row['qqq_available_at'],
            sox_observed_at=current_sox.close_at.isoformat() if valid_sox else None,
            sox_available_at=current_sox.available_at.isoformat() if valid_sox else None,
            vix_observed_at=row['vix_observed_at'],vix_available_at=row['vix_available_at'],
            publication_vintage_verified=False,price_basis='provider_split_adjusted_ohlc',
            warmup_rows=len(known),source=stock[index].source)
        row.update(indicators_v3=indicators,quality_v3=quality)
    return rows
