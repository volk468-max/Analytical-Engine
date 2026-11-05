"""Optional calendar reference audit; no change to frozen source timestamps."""
import argparse,csv
from pathlib import Path
import exchange_calendars as xc
from study import OUT


def run(source):
    if xc.__version__!='4.11.2':raise ValueError('pin calendar version4.11.2')
    cal=xc.get_calendar('XNYS',start='2020-01-01',end='2026-10-22')
    expected={str(d)[:10] for d in cal.sessions}
    with (source/'data/risk-signal-v3/bars.csv').open() as f:rows=list(csv.DictReader(f))
    results=[]
    for symbol in ('AMD','NVDA','MU','QQQ','^SOX'):
        rs=[r for r in rows if r['symbol']==symbol];days={r['close_at'][:10] for r in rs}
        diffs=sum(r['close_at']!=cal.schedule.loc[r['close_at'][:10],'close'].isoformat() for r in rs)
        results.append(dict(symbol=symbol,reference_calendar='exchange_calendars4.11.2/XNYS',missing_dates=';'.join(sorted(expected-days)),extra_dates=';'.join(sorted(days-expected)),
            normalised_close_time_mismatches=diffs,interpretation='Fixed6.5h archived closes differ on early close dates; next-midnight availability conservative assumption, not PIT attestation'))
    with (OUT/'calendar-audit.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(results[0]),lineterminator='\n');w.writeheader();w.writerows(results)


if __name__=='__main__':
    ap=argparse.ArgumentParser(__doc__);ap.add_argument('--source',type=Path,required=True);a=ap.parse_args();run(a.source)
