"""Stage-one data snapshot only; no forecasts, fitting, services or trades."""
import csv,gzip,hashlib,io,json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timedelta,timezone
from pathlib import Path
from urllib.request import Request,urlopen
from zoneinfo import ZoneInfo

STOCKS=('AMD','NVDA','MU','TSM','AVGO','AMAT','AMZN','META','PLTR','LRCX','NBIS')
BENCHMARKS=('^GSPC','^IXIC','^NDX','^RUT','^SOX','^VIX','DX-Y.NYB','QQQ','SPY','IWM','SMH','SOXX')
RATES=('DGS2','DGS10','BAMLC0A0CM','BAMLH0A0HYM2')
ROOT=Path('reports/october-risk-failure-audit-v2/completion/data')


def main():
    ROOT.mkdir(parents=True,exist_ok=True);stamp=datetime.now(timezone.utc).isoformat()
    begin=int(datetime(2025,1,1,tzinfo=timezone.utc).timestamp());end=int(datetime(2026,11,3,tzinfo=timezone.utc).timestamp())
    def stock(symbol):
        url=f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?period1={begin}&period2={end}&interval=1d&events=div%2Csplits'
        entry=dict(symbol=symbol,source='Yahoo chart',url=url,retrieved_at=stamp);rows=[]
        try:
            with urlopen(Request(url,headers={'User-Agent':'AlphaOS Stage1 audit/1.0'}),timeout=25) as response:raw=response.read()
            name=symbol.replace('^','INDEX-')+'-source.json';(ROOT/name).write_bytes(raw)
            digest=hashlib.sha256(raw).hexdigest();r=json.loads(raw)['chart']['result'][0];q=r['indicators']['quote'][0]
            tz=ZoneInfo(r['meta'].get('exchangeTimezoneName','America/New_York'));ny=ZoneInfo('America/New_York');missing=[]
            for i,ts in enumerate(r.get('timestamp',[])):
                opened=datetime.fromtimestamp(ts,timezone.utc);date=opened.astimezone(tz).date()
                if date.isoformat()>'2026-11-02':continue
                values=[q[k][i] for k in ('open','high','low','close','volume')]
                if any(x is None for x in values):missing.append(date.isoformat());continue
                observed=datetime.combine(date,datetime.min.time(),ny).replace(hour=17 if symbol=='DX-Y.NYB' else 16,minute=15 if symbol=='^VIX' else 0).astimezone(timezone.utc)
                ambiguous=opened>=observed
                if ambiguous:observed=opened+timedelta(hours=24)
                available=datetime.combine(date+timedelta(days=2 if ambiguous else 1),datetime.min.time(),timezone.utc)
                if available<observed:available=observed+timedelta(hours=12)
                rows.append(dict(symbol=symbol,date=date.isoformat(),open_at=opened.isoformat(),observed_at=observed.isoformat(),
                    available_at=available.isoformat(),**dict(zip(('open','high','low','close','volume'),values)),
                    source=digest,price_basis='provider_split_adjusted_ohlc',publication_verified=False,
                    timestamp_status='AMBIGUOUS_SESSION_CONSERVATIVE_LAG' if ambiguous else 'ASSUMED_PUBLICATION'))
            entry.update(status='DOWNLOADED' if rows else 'UNAVAILABLE',rows=len(rows),first=rows[0]['date'] if rows else None,
                last=rows[-1]['date'] if rows else None,raw_file=name,raw_sha256=digest,missing=missing,
                exchange_timezone=str(tz),corporate_actions=r.get('events',{}),publication_verified=False)
        except Exception as exc:entry.update(status='UNAVAILABLE',error=str(exc))
        return rows,entry
    with ThreadPoolExecutor(max_workers=5) as pool:fetched=list(pool.map(stock,STOCKS+BENCHMARKS))
    prices=[r for rows,_ in fetched for r in rows]
    with (ROOT/'prices.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(prices[0]) if prices else ['symbol','date'],lineterminator='\n');w.writeheader();w.writerows(prices)
    macro=[];entries=[]
    for series in RATES:
        url=f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}&cosd=2025-01-01&coed=2026-11-02'
        e=dict(symbol=series,source='FRED retrospective daily series',url=url,retrieved_at=stamp,publication_verified=False)
        try:
            with urlopen(Request(url,headers={'User-Agent':'AlphaOS Stage1 audit/1.0'}),timeout=25) as response:raw=response.read()
            name=series+'-source.csv.gz';(ROOT/name).write_bytes(gzip.compress(raw,mtime=0));n=0
            for r in csv.DictReader(io.StringIO(raw.decode())):
                date=r.get('observation_date',r.get('DATE'))
                if not date or date>'2026-11-02' or r[series] in ('','.'):continue
                macro.append(dict(series=series,date=date,value=float(r[series]),source=hashlib.sha256(raw).hexdigest()));n+=1
            e.update(status='DOWNLOADED',rows=n,raw_file=name,raw_sha256=hashlib.sha256(raw).hexdigest())
        except Exception as exc:e.update(status='UNAVAILABLE',error=str(exc))
        entries.append(e)
    (ROOT/'macro.json').write_text(json.dumps(macro,indent=2)+'\n')
    manifest=dict(schema_version=1,dataset_version='october-stage1-asof-2026-11-03',retrieved_at=stamp,cutoff='2026-11-02',
        sources=[e for _,e in fetched]+entries,
        limitations=['No original historical publication vintages; conservative assumed lags.',
            'No splicing with prior packs; compare overlapping price vintages explicitly.',
            'NBIS historical identity/legacy suspension is not extrapolated into an uninterrupted old series.',
            'Whole-market breadth and actual positions/trades/decision payloads not supplied by these sources.'],
        artifact_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.iterdir() if p.name!='manifest.json'})
    (ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print([(e['symbol'],e['status'],e.get('rows'),e.get('last')) for e in manifest['sources']])


if __name__=='__main__':main()
