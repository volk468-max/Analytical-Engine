"""Read-only QQQ research download; publication times are assumed, not verified."""
import csv
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen


def main():
    root = Path('data/risk-diagnostics')
    root.mkdir(parents=True, exist_ok=True)
    url = 'https://query1.finance.yahoo.com/v8/finance/chart/QQQ?period1=1672531200&period2=1792800000&interval=1d'
    retrieved = datetime.now(timezone.utc)
    with urlopen(Request(url, headers={'User-Agent': 'AlphaOS historical-research/1.0'}), timeout=30) as response:
        raw = response.read()
    digest = hashlib.sha256(raw).hexdigest()
    result = json.loads(raw)['chart']['result'][0]
    quote = result['indicators']['quote'][0]
    rows = []
    for i, ts in enumerate(result['timestamp']):
        opened = datetime.fromtimestamp(ts, timezone.utc)
        closed = opened + timedelta(hours=6, minutes=30)
        published = datetime.combine(opened.date()+timedelta(days=1), datetime.min.time(), timezone.utc)
        values = [quote[key][i] for key in ('open','high','low','close')]
        if published > retrieved or opened.date().isoformat() > '2026-10-22' or any(v is None for v in values):
            continue
        rows.append(dict(symbol='QQQ', open_at=opened.isoformat(), close_at=closed.isoformat(),
                         available_at=published.isoformat(), **dict(zip(('open','high','low','close'), values)),
                         source='Yahoo chart; '+digest, verified='false', price_basis='retrospective_provider_ohlc'))
    with (root/'qqq.csv').open('w', newline='') as file:
        writer=csv.DictWriter(file, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    manifest=dict(url=url, retrieved_at=retrieved.isoformat(), raw_sha256=digest,
                  rows=len(rows), first=rows[0]['close_at'], last=rows[-1]['close_at'],
                  artifact_sha256={'qqq.csv': hashlib.sha256((root/'qqq.csv').read_bytes()).hexdigest()},
                  limitations='Retrospective provider prices; availability inferred next UTC midnight; not verified PIT.')
    (root/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print('QQQ:', len(rows), 'bars;', manifest['last'])


if __name__ == '__main__':
    main()
