"""Prepare frozen completion inputs; original audit files are read-only."""
import csv, hashlib, json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import exchange_calendars as xc
import pandas as pd

ROOT=Path(__file__).resolve().parent
def write_csv(name, rows):
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with (ROOT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys,lineterminator='\n');w.writeheader();w.writerows(rows)
def main():
    baseline=json.loads((ROOT/'baseline.json').read_text())
    repo=ROOT.parents[2]
    for p,h in baseline['sha256'].items():
        assert hashlib.sha256((repo/p).read_bytes()).hexdigest()==h,p
    old=json.loads((ROOT.parent/'inputs.json').read_text())
    prices=list(csv.DictReader((ROOT/'data/prices.csv').open()))
    source=json.loads((ROOT/'data/manifest.json').read_text())
    macro=json.loads((ROOT/'data/macro.json').read_text())
    lookup={(r['symbol'],r['date']):r for r in prices}
    checks=[]
    for r in old['prices']:
        s='^SOX' if r['symbol']=='SOX' else r['symbol'];n=lookup[s,r['date']]
        for col in ('open','high','low','close'):
            checks.append(dict(symbol=r['symbol'],date=r['date'],field=col,original=r[col],downloaded=float(n[col]),match=abs(r[col]-float(n[col]))<1e-5))
    assert all(r['match'] for r in checks),'price overlap revision: do not splice'
    write_csv('overlap-validation.csv',checks)
    symbols={r['symbol'] for r in old['prices']}
    inp=json.loads(json.dumps(old));inp['data_end']='2026-11-02'
    inp['completion_provenance']='Original prefix preserved; new Yahoo rows appended only after 2026-10-22; overlap OHLC verified'
    inp['prices'] += [dict(symbol='SOX' if r['symbol']=='^SOX' else r['symbol'],date=r['date'],**{c:float(r[c]) for c in ('open','high','low','close')},available_at=r['available_at'],publication_verified=False) for r in prices if r['date']>'2026-10-22' and ('SOX' if r['symbol']=='^SOX' else r['symbol']) in symbols]
    inp['vix'] += [dict(date=r['date'],close=float(r['close']),available_at=r['available_at'],publication_verified=False) for r in prices if r['symbol']=='^VIX' and r['date']>'2026-10-22']
    inp['rates'] += [dict(date=r['date'],yield_pct=r['value']) for r in macro if r['series']=='DGS10' and r['date']>'2026-10-22']
    for e in source['sources']:
        if e['symbol'] not in symbols:continue
        for kind,events in e.get('corporate_actions',{}).items():
            for a in events.values():
                d=datetime.fromtimestamp(a['date'],timezone.utc).date().isoformat()
                if '2026-10-22'<d<='2026-11-02':inp['actions'].append(dict(symbol=e['symbol'],kind=kind,**a,date=d))
    (ROOT/'inputs.json').write_text(json.dumps(inp,separators=(',',':'))+'\n')
    cal=xc.get_calendar('XNYS',start='2024-12-01',end='2026-11-15')
    sessions=cal.sessions_in_range('2026-09-01','2026-11-02')
    schedule=[]
    for s in sessions:
        row=cal.schedule.loc[s]
        schedule.append(dict(date=s.date().isoformat(),open_at=row['open'].isoformat(),close_at=row['close'].isoformat(),decision_available_assumed=(s+pd.Timedelta(days=1)).isoformat(),calendar='XNYS exchange_calendars 4.13.2'))
    write_csv('session-calendar.csv',schedule)
    ns=cal.schedule.loc[cal.next_session(sessions[-1])]
    (ROOT/'next-session.json').write_text(json.dumps(dict(date=ns.name.date().isoformat(),open_at=ns['open'].isoformat(),status='KNOWN_CALENDAR_ONLY_NO_EXECUTION_PRICE'))+'\n')
    want={r['date'] for r in schedule}
    coverage=[]
    for e in source['sources']:
        s=e['symbol'];xs=[r for r in prices if r['symbol']==s and r['date'] in want]
        if not xs:xs=[r for r in macro if r['series']==s and r['date'] in want]
        have={r['date'] for r in xs};coverage.append(dict(series=s,provider=e['source'],retrieved_at=e['retrieved_at'],rows=len(xs),first=min(have) if have else None,last=max(have) if have else None,missing_equity_sessions=';'.join(sorted(want-have)),status=e['status'],original_publication_verified=False))
        if s not in ('DGS2','DGS10','BAMLC0A0CM','BAMLH0A0HYM2','^VIX','DX-Y.NYB'):assert have==want,(s,want-have)
    write_csv('data-coverage.csv',coverage)
    known=[];all_sessions=cal.sessions_in_range('2025-01-01','2026-11-10')
    ds=[s.date().isoformat() for s in all_sessions]
    for r in macro:
        ix=next((i for i,d in enumerate(ds) if d>=r['date']),None)
        avail=(datetime.fromisoformat(ds[ix+2])+timedelta(days=1)).replace(tzinfo=timezone.utc).isoformat() if ix is not None and ix+2<len(ds) else None
        known.append(dict(**r,available_at_assumed=avail,publication_verified=False,vintage='RETROSPECTIVE_NOT_ALFRED'))
    (ROOT/'macro-availability.json').write_text(json.dumps(known,separators=(',',':'))+'\n')
    print(json.dumps(dict(sessions=len(schedule),input_prices=len(inp['prices']),overlap_ohlc=len(checks),coverage=coverage)))
if __name__=='__main__':main()
