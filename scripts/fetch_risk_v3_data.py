"""Frozen retrospective price/benchmark research pack; no trade or service calls."""
import csv,gzip,hashlib,io,json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timedelta,timezone
from pathlib import Path
from urllib.request import Request,urlopen


def main():
    root=Path('data/risk-signal-v3'); root.mkdir(parents=True,exist_ok=True)
    retrieved=datetime.now(timezone.utc)
    symbols=('AMD','NVDA','MU','QQQ','^SOX')
    def fetch(symbol):
        url=f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?period1=1577836800&period2=1792800000&interval=1d&events=div%2Csplits'
        entry=dict(symbol=symbol,url=url,retrieved_at=retrieved.isoformat())
        rows=[]
        try:
            with urlopen(Request(url,headers={'User-Agent':'AlphaOS offline signal research/1.0'}),timeout=30) as response:
                raw=response.read()
            name=symbol.replace('^','')+'-source.json'; (root/name).write_bytes(raw)
            entry.update(raw_file=name,raw_sha256=hashlib.sha256(raw).hexdigest())
            r=json.loads(raw)['chart']['result'][0]; q=r['indicators']['quote'][0]
            for i,ts in enumerate(r.get('timestamp',[])):
                opened=datetime.fromtimestamp(ts,timezone.utc)
                available=datetime.combine(opened.date()+timedelta(days=1),datetime.min.time(),timezone.utc)
                if opened.date().isoformat()>'2026-10-22' or available>retrieved:
                    continue
                values=[q[k][i] for k in ('open','high','low','close','volume')]
                if any(x is None for x in values):
                    raise ValueError('Missing OHLCV '+opened.date().isoformat())
                rows.append(dict(symbol=symbol,open_at=opened.isoformat(),close_at=(opened+timedelta(hours=6,minutes=30)).isoformat(),
                    available_at=available.isoformat(),**dict(zip(('open','high','low','close','volume'),values)),
                    source='Yahoo '+symbol+' '+entry['raw_sha256'],verified='false',price_basis='provider_split_adjusted_ohlc'))
            entry.update(status='downloaded',rows=len(rows),first=rows[0]['close_at'],last=rows[-1]['close_at'],
                         reported_corporate_actions=r.get('events',{}))
        except Exception as exc:
            entry.update(status='UNAVAILABLE',error=str(exc))
            rows=[]
        return rows,entry
    with ThreadPoolExecutor(max_workers=5) as pool:
        fetched=list(pool.map(fetch,symbols))
    rows=[row for series,e in fetched for row in series]
    with (root/'bars.csv').open('w',newline='') as file:
        w=csv.DictWriter(file,fieldnames=['symbol','open_at','close_at','available_at','open','high','low','close','volume','source','verified','price_basis'],lineterminator='\n')
        w.writeheader(); w.writerows(rows)
    url='https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv'
    markets=[]
    try:
        with urlopen(url,timeout=30) as response: raw=response.read()
        (root/'vix-source.csv.gz').write_bytes(gzip.compress(raw,mtime=0))
        digest=hashlib.sha256(raw).hexdigest()
        for row in csv.DictReader(io.StringIO(raw.decode())):
            date=datetime.strptime(row['DATE'],'%m/%d/%Y').replace(tzinfo=timezone.utc)
            if not '2020-01-01'<=date.date().isoformat()<='2026-10-22': continue
            markets.append(dict(observed_at=(date+timedelta(hours=20,minutes=15)).isoformat(),
                available_at=(date+timedelta(days=1)).isoformat(),value={'vix':float(row['CLOSE'])},
                source='CBOE '+digest,verified=False))
        vix_entry=dict(symbol='VIX',url=url,raw_file='vix-source.csv.gz',status='downloaded',rows=len(markets),raw_sha256=digest)
    except Exception as exc:
        vix_entry=dict(symbol='VIX',url=url,status='UNAVAILABLE',error=str(exc))
    (root/'markets.json').write_text(json.dumps(markets,indent=2)+'\n')
    manifest=dict(schema_version=1,dataset_version='risk-v3-asof-2026-10-23-v1',retrieved_at=retrieved.isoformat(),
        sources=[e for r,e in fetched]+[vix_entry],
        limitations=['Retrospective provider vintages, not verified original publication archives.',
            'One consistent provider split-adjusted OHLC basis; adjusted-close dividend series not mixed in.',
            'Signals use scale-invariant ratios, not historical nominal share quantities; no orders or P&L accounting.',
            '2020 is indicator warm-up only. 2026-10-23 excluded. Publication times inferred next UTC midnight.',
            'Semiconductor ^SOX context is optional retrospective index data, not independently verified PIT.'],
        artifact_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir() if p.name!='manifest.json'})
    (root/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print([(e['symbol'],e['status'],e.get('rows')) for e in manifest['sources']])


if __name__=='__main__':main()
