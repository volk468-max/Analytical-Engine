"""Freeze a new provider snapshot. Never called by offline reproduction."""
import csv,hashlib,json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone,timedelta
from pathlib import Path
from urllib.request import Request,urlopen
from zoneinfo import ZoneInfo
ROOT=Path(__file__).resolve().parents[2]/'reports/historical-sell-buyback-v1/data'
STOCKS=['AMD','NVDA','MU','TSM','AVGO','AMAT','AMZN','META','PLTR','LRCX','NBIS']
CONTEXT=['QQQ','SPY','^GSPC','^IXIC','^SOX','SOXX','SMH','^VIX']
def main():
    ROOT.mkdir(parents=True,exist_ok=True);stamp=datetime.now(timezone.utc).isoformat();begin=int(datetime(2020,1,1,tzinfo=timezone.utc).timestamp());end=int(datetime(2026,11,3,tzinfo=timezone.utc).timestamp())
    def fetch(s):
        url=f'https://query1.finance.yahoo.com/v8/finance/chart/{s}?period1={begin}&period2={end}&interval=1d&includePrePost=false&events=div%2Csplits'
        e=dict(symbol=s,provider='Yahoo chart',url=url,retrieved_at=stamp,publication_verified=False);rows=[]
        try:
            raw=urlopen(Request(url,headers={'User-Agent':'AlphaOS independent historical audit/1.0'}),timeout=30).read();name=s.replace('^','INDEX-')+'.json';(ROOT/name).write_bytes(raw);z=json.loads(raw)['chart']['result'][0];q=z['indicators']['quote'][0];tz=ZoneInfo(z['meta'].get('exchangeTimezoneName','America/New_York'));bad=[]
            for i,t in enumerate(z['timestamp']):
                d=datetime.fromtimestamp(t,timezone.utc).astimezone(tz).date().isoformat()
                if d>'2026-11-02':continue
                values={k:q[k][i] for k in ['open','high','low','close','volume']}
                if any(v is None for v in values.values()):bad.append(d);continue
                rows.append(dict(symbol=s,date=d,**values,provider_bar_timestamp=t,available_at=(datetime.fromisoformat(d)+timedelta(days=1)).replace(tzinfo=timezone.utc).isoformat(),price_basis='PROVIDER_SPLIT_ADJUSTED_OHLC_NOT_DIVIDEND_ADJCLOSE',publication_verified=False))
            e.update(status='DOWNLOADED',raw_file=name,raw_sha256=hashlib.sha256(raw).hexdigest(),first=rows[0]['date'],last=rows[-1]['date'],rows=len(rows),missing_rows=bad,exchange_timezone=str(tz),first_trade_timestamp=z['meta'].get('firstTradeDate'),corporate_actions=z.get('events',{}),meta_instrument_type=z['meta'].get('instrumentType'))
        except Exception as ex:e.update(status='UNAVAILABLE',error=str(ex))
        return rows,e
    with ThreadPoolExecutor(max_workers=5) as pool:xs=list(pool.map(fetch,STOCKS+CONTEXT))
    prices=[r for rows,_ in xs for r in rows]
    with (ROOT/'prices.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(prices[0]),lineterminator='\n');w.writeheader();w.writerows(prices)
    m=dict(retrieved_at=stamp,window='2020 warmup through2026-11-02',sources=[e for _,e in xs],limitations=['Original publication timestamps/vintages not independently archived','Fixed current survivors; no historical neutral universe','Provider OHLC/actions use split-adjusted terminal share units; nominal views reconstructed explicitly','NBIS pre-resumption YNDX/suspension history excluded from investable universe'])
    m['artifact_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.iterdir() if p.name!='manifest.json'};(ROOT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps([(e['symbol'],e['status'],e.get('rows'),e.get('first'),e.get('last')) for e in m['sources']]))
if __name__=='__main__':main()
