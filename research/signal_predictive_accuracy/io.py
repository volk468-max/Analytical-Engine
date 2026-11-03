import csv,gzip,hashlib,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'reports/signal-predictive-accuracy-audit-v1';I=R/'inputs'
STOCKS=['AMD','NVDA','MU','TSM','AVGO','AMAT','AMZN','META','PLTR','LRCX','NBIS']
MARKETS=['QQQ','SPY','^GSPC','^IXIC','^SOX','SOXX','SMH']
def rows(p):return list(csv.DictReader(p.open()))
def write(name,data):
    keys=list(dict.fromkeys(k for r in data for k in r))
    if name.endswith('.gz'):
        import io
        s=io.StringIO();w=csv.DictWriter(s,fieldnames=keys,lineterminator='\n');w.writeheader();w.writerows(data);(R/name).write_bytes(gzip.compress(s.getvalue().encode(),mtime=0))
    else:
        with (R/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=keys,lineterminator='\n');w.writeheader();w.writerows(data)
def load():
    meta=json.loads((I/'provenance.json').read_text())
    for x in meta['source_objects']:assert hashlib.sha256((ROOT/x['local']).read_bytes()).hexdigest()==x['sha256'],x['local']
    p=json.loads(gzip.decompress((I/'prices.json.gz').read_bytes()));bars={s:[dict(zip(p['columns'],r)) for r in rs] for s,rs in p['prices'].items()}
    for rs in bars.values():rs.sort(key=lambda x:x['date'])
    signals=rows(I/'historical-signals.csv');calendar=rows(I/'calendar.csv');regime={x['date']:x['regime'] for x in rows(I/'regimes.csv')}
    spec=importlib.util.spec_from_file_location('immutable_sector_formula',I/'frozen_sector_formula.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    prices=[dict(symbol=s,**x) for s,rs in bars.items() for x in rs];daily,events=module.reconstruct(prices,'2021-01-01','2026-11-02')
    assert [x['date'] for x in events]==[x['date'] for x in signals]
    frozen=rows(I/'sector-daily.csv');assert len(daily)==len(frozen)==1465
    for a,b in zip(daily,frozen):assert a['date']==b['date'] and str(a['sector_flag'])==b['sector_flag']
    return dict(bars=bars,signals=signals,calendar=calendar,regimes=regime,eligible={**p['eligible'],**{s:'2021-01-04' for s in MARKETS}},sector_daily={x['date']:x for x in daily})
