"""Retrieve supplemental research-only retrospective history; never touch old packs."""
import csv,gzip,hashlib,io,json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timedelta,timezone
from pathlib import Path
from urllib.request import Request,urlopen

SYMBOLS=('AVGO','AMAT','LRCX','TSM','MRVL','INTC','QCOM','TXN','AMZN','META','MSFT','GOOGL','PLTR','CRM','ADBE')
ROOT=Path('data/historical-drawdown-anatomy')


def main():
    ROOT.mkdir(parents=True,exist_ok=True);retrieved=datetime.now(timezone.utc).isoformat()
    def fetch(symbol):
        url=f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?period1=1577836800&period2=1792800000&interval=1d&events=div%2Csplits'
        entry=dict(symbol=symbol,url=url,retrieved_at=retrieved,price_basis='provider_split_adjusted_ohlc',
            publication_assumption='next UTC midnight; not independently attested vintage')
        rows=[]
        try:
            with urlopen(Request(url,headers={'User-Agent':'AlphaOS historical research/1.0'}),timeout=25) as response:raw=response.read()
            name=symbol+'-source.json';(ROOT/name).write_bytes(raw);digest=hashlib.sha256(raw).hexdigest()
            result=json.loads(raw)['chart']['result'][0];quote=result['indicators']['quote'][0]
            missing=[]
            for i,timestamp in enumerate(result['timestamp']):
                opened=datetime.fromtimestamp(timestamp,timezone.utc)
                if opened.date().isoformat()>'2026-10-22':continue
                values=[quote[k][i] for k in ('open','high','low','close','volume')]
                if any(x is None for x in values):missing.append(opened.date().isoformat());continue
                rows.append(dict(symbol=symbol,open_at=opened.isoformat(),close_at=(opened+timedelta(hours=6,minutes=30)).isoformat(),
                    available_at=datetime.combine(opened.date()+timedelta(days=1),datetime.min.time(),timezone.utc).isoformat(),
                    **dict(zip(('open','high','low','close','volume'),values)),source='Yahoo '+symbol+' '+digest,
                    verified=False,price_basis='provider_split_adjusted_ohlc'))
            entry.update(status='DOWNLOADED' if rows else 'UNAVAILABLE',rows=len(rows),raw_file=name,raw_sha256=digest,
                first=rows[0]['open_at'] if rows else None,last=rows[-1]['open_at'] if rows else None,
                missing_rows=missing,corporate_actions=result.get('events',{}))
        except Exception as exc:entry.update(status='UNAVAILABLE',error=str(exc))
        return rows,entry
    with ThreadPoolExecutor(max_workers=5) as pool:result=list(pool.map(fetch,SYMBOLS))
    rows=[r for series,_ in result for r in series]
    with (ROOT/'bars.csv').open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=['symbol','open_at','close_at','available_at','open','high','low','close','volume','source','verified','price_basis'],lineterminator='\n')
        writer.writeheader();writer.writerows(rows)
    url='https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10&cosd=2020-01-01&coed=2026-10-22'
    rates=[];rate_entry=dict(symbol='DGS10',url=url,retrieved_at=retrieved,publication_assumption='two subsequent QQQ sessions, next midnight; retrospective, not ALFRED vintages')
    try:
        with urlopen(Request(url,headers={'User-Agent':'AlphaOS historical research/1.0'}),timeout=25) as response:raw=response.read()
        (ROOT/'DGS10-source.csv.gz').write_bytes(gzip.compress(raw,mtime=0))
        for r in csv.DictReader(io.StringIO(raw.decode())):
            date=r.get('observation_date',r.get('DATE'))
            if date and '2020-01-01'<=date<='2026-10-22' and r['DGS10'] not in ('','.'):rates.append(dict(date=date,yield_pct=float(r['DGS10'])))
        rate_entry.update(status='DOWNLOADED' if rates else 'UNAVAILABLE',rows=len(rates),raw_file='DGS10-source.csv.gz',raw_sha256=hashlib.sha256(raw).hexdigest())
    except Exception as exc:rate_entry.update(status='UNAVAILABLE',error=str(exc))
    (ROOT/'rates.json').write_text(json.dumps(rates,indent=2)+'\n')
    manifest=dict(schema_version=1,retrieved_at=retrieved,cutoff='2026-10-22',sources=[e for _,e in result]+[rate_entry],
        inherited_source_manifest='data/risk-signal-v3/manifest.json',
        inherited_manifest_sha256=hashlib.sha256(Path('data/risk-signal-v3/manifest.json').read_bytes()).hexdigest(),
        limitations=['Retrospective provider responses, no original publication vintages.',
            'A fixed surviving-company universe is not survivorship-free historical sector membership.',
            'Price OHLC split-adjusted, not dividend-adjusted; no double split application.',
            'Shorter histories and missing warmup are flagged, not fabricated. Early close times conservatively delayed.',
            'DGS10 if obtained is a retrospective FRED series with an assumed conservative publication lag.'],
        artifact_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.iterdir() if p.name!='manifest.json'})
    (ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print([(e['symbol'],e['status'],e.get('rows')) for e in manifest['sources']])


if __name__=='__main__':main()
