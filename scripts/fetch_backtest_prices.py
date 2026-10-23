"""Optional public-data acquisition. Never supplies verified PIT provenance."""
import argparse
import csv
import hashlib
import io
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen

SYMBOLS = 'AMD NVDA MU TSM AVGO AMAT AMZN META PLTR LRCX NBIS'.split()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='data/backtest')
    args = parser.parse_args()
    root = Path(args.output)
    root.mkdir(parents=True, exist_ok=True)
    retrieved = datetime.now(timezone.utc)
    start = int(datetime(2023, 1, 1, tzinfo=timezone.utc).timestamp())
    end = int(datetime(2026, 10, 24, tzinfo=timezone.utc).timestamp())
    manifest = dict(retrieved_at=retrieved.isoformat(), sources=[], limitations=[
        'Retrospective prices, not verified historical vintages.',
        'Yahoo OHLC may be split-adjusted to retrieval vintage; no dividend or corporate-action ledger.',
        'Publication times inferred conservatively as next UTC midnight, not provider-attested.',
        'Uncompleted/unpublished sessions at retrieval are excluded.'])

    def get(symbol):
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?period1={start}&period2={end}&interval=1d&events=div%2Csplits'
        entry = dict(symbol=symbol, url=url)
        rows = []
        try:
            with urlopen(Request(url, headers={'User-Agent': 'AlphaOS historical-research/1.0'}), timeout=30) as response:
                raw = response.read()
            entry['raw_sha256'] = hashlib.sha256(raw).hexdigest()
            result = json.loads(raw)['chart']['result'][0]
            quote = result['indicators']['quote'][0]
            excluded = 0
            for index, ts in enumerate(result.get('timestamp', [])):
                opened = datetime.fromtimestamp(ts, timezone.utc)
                closed = opened + timedelta(hours=6, minutes=30)
                published = datetime.combine(opened.date() + timedelta(days=1), datetime.min.time(), timezone.utc)
                if published > retrieved or closed > retrieved:
                    excluded += 1
                    continue
                values = [quote[key][index] for key in ('open', 'high', 'low', 'close')]
                if any(value is None for value in values):
                    continue
                rows.append(dict(symbol=symbol, open_at=opened.isoformat(), close_at=closed.isoformat(),
                                 available_at=published.isoformat(), **dict(zip(('open', 'high', 'low', 'close'), values)),
                                 source='Yahoo chart; ' + entry['raw_sha256'], verified='false',
                                 price_basis='retrospective_provider_ohlc'))
            entry.update(status='downloaded', rows=len(rows), excluded_incomplete=excluded,
                         first=rows[0]['close_at'] if rows else None, last=rows[-1]['close_at'] if rows else None,
                         corporate_actions=result.get('events', {}))
        except Exception as exc:
            entry.update(status='error', error=str(exc))
        return rows, entry

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(get, SYMBOLS))
    bars = []
    for rows, entry in results:
        bars.extend(rows)
        manifest['sources'].append(entry)
        print(entry['symbol'], entry['status'], entry.get('rows'), entry.get('last'))
    with (root/'bars.csv').open('w', newline='') as file:
        fields = ['symbol', 'open_at', 'close_at', 'available_at', 'open', 'high', 'low', 'close', 'source', 'verified', 'price_basis']
        writer = csv.DictWriter(file, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(bars)
    url = 'https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv'
    try:
        with urlopen(url, timeout=30) as response:
            raw = response.read()
        digest = hashlib.sha256(raw).hexdigest()
        markets = []
        for row in csv.DictReader(io.StringIO(raw.decode())):
            date = datetime.strptime(row['DATE'], '%m/%d/%Y').replace(tzinfo=timezone.utc)
            if date.year < 2023:
                continue
            close = date + timedelta(hours=20, minutes=15)
            available = date + timedelta(days=1)
            if available <= retrieved:
                markets.append(dict(observed_at=close.isoformat(), available_at=available.isoformat(),
                                    value={'vix': float(row['CLOSE'])}, source='CBOE VIX; ' + digest, verified=False))
        (root/'markets.json').write_text(json.dumps(markets, indent=2) + '\n')
        manifest['sources'].append(dict(symbol='VIX', url=url, status='downloaded', raw_sha256=digest,
                                        rows=len(markets), last=markets[-1]['observed_at'] if markets else None))
    except Exception as exc:
        (root/'markets.json').unlink(missing_ok=True)
        manifest['sources'].append(dict(symbol='VIX', url=url, status='error', error=str(exc)))
    for name in ('bars.csv', 'markets.json'):
        if (root/name).exists():
            manifest.setdefault('artifact_sha256', {})[name] = hashlib.sha256((root/name).read_bytes()).hexdigest()
    (root/'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
