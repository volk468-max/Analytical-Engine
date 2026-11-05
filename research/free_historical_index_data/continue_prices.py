"""Additional CC0 price archive audit; preserves all original v1 files/results."""
import argparse
import base64
from collections import Counter,defaultdict
import csv
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import urllib.request
import zipfile
from audit import OUT, csv_rows, write_csv

DEST=OUT/'continuation'
URL='https://www.kaggle.com/api/v1/datasets/download/camnugent/sandp500?datasetVersionNumber=4'
ZIP_SHA='4f775195e67179c9c19b63f084e5f2e049fae734023f9d10e233388d6423752a'
CSV_SHA='6aea253cd19de60b568143991aaf1fa482456565c389205658d236e595e716cf'


def rejection(r):
    try:
        o,h,l,c,v=(float(r[k]) for k in ('open','high','low','close','volume'))
    except (ValueError,KeyError):return 'MISSING_OR_NONNUMERIC'
    if not all(math.isfinite(x) for x in (o,h,l,c,v)):return 'NONFINITE'
    if not (0<l<=min(o,c)<=max(o,c)<=h and v>=0):return 'INVALID_OHLCV'
    if r['Name']=='AAL' and r['date']<'2013-12-09':return 'PRE_EFFECTIVE_AAL_IDENTITY'
    if r['Name'] in ('GOOG','GOOGL') and r['date']<'2014-04-03':return 'GOOGLE_PRE_CLASS_SPLIT_IDENTITY_UNRESOLVED'
    return ''


def load_archive(path):
    raw=Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=ZIP_SHA:raise ValueError('archive hash mismatch')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:data=z.read('all_stocks_5yr.csv')
    if hashlib.sha256(data).hexdigest()!=CSV_SHA:raise ValueError('CSV hash mismatch')
    rows=list(csv.DictReader(io.StringIO(data.decode())))
    counts=Counter((r['Name'],r['date']) for r in rows)
    good=set();bad=[]
    for r in rows:
        reason='DUPLICATE_KEY' if counts[r['Name'],r['date']]>1 else rejection(r)
        if reason:bad.append(dict(symbol=r['Name'],date=r['date'],reason=reason))
        else:good.add((r['Name'],r['date']))
    return rows,good,bad


def run(archive, dest=DEST):
    dest.mkdir(parents=True,exist_ok=True)
    rows,good,bad=load_archive(archive)
    sessions=[r['date'] for r in csv_rows(OUT/'sessions.csv')]
    session_set=set(sessions)
    non_session=sorted((t,d) for t,d in good if d not in session_set)
    good={(t,d) for t,d in good if d in session_set}
    ready50=set();ready200=set()
    for t in {r['Name'] for r in rows}:
        streak=0
        for d in sessions:
            streak=streak+1 if (t,d) in good else 0
            if streak>=50:ready50.add((t,d))
            if streak>=200:ready200.add((t,d))
    membership=list(csv.DictReader(io.StringIO(gzip.decompress(base64.b64decode((OUT/'daily-membership.csv.gz.b64').read_bytes())).decode())))
    departed={(r['source'],r['symbol']) for r in csv_rows(OUT/'delisted-price-coverage.csv') if r['source_observed_departure']=='True'}
    annual={};inventory={}
    for r in membership:
        source,idx,d=r['source'],r['index'],r['date'];year=int(d[:4]);k=(source,year)
        a=annual.setdefault(k,dict(index=idx,source=source,year=year,member_days=0,new_archive_quote_days=0,new_ma50_days=0,new_ma200_days=0,
            departed_member_days=0,departed_new_quote_days=0,confirmed_pit_days=0))
        for t in r['tickers'].split(';'):
            a['member_days']+=1;a['new_archive_quote_days']+=(t,d) in good
            a['new_ma50_days']+=(t,d) in ready50;a['new_ma200_days']+=(t,d) in ready200
            a['departed_member_days']+=(source,t) in departed
            a['departed_new_quote_days']+=(source,t) in departed and (t,d) in good
            q=inventory.setdefault((source,t),dict(index=idx,source=source,symbol=t,member_days=0,new_archive_quote_days=0,
                source_observed_departure=(source,t) in departed,exchange_delisting_status='UNKNOWN',security_id='',qualified=False))
            q['member_days']+=1;q['new_archive_quote_days']+=(t,d) in good
    original={(r['source'],int(r['year'])):r for r in csv_rows(OUT/'historical-membership-coverage.csv')}
    # Original archive starts 2020; new archive ends 2018, so these are disjoint counts.
    assert max(d for t,d in good)<'2020-01-01'
    for k,a in annual.items():
        a['original_quote_days']=int(original[k]['archived_quote_observations'])
        a['union_candidate_quote_days']=a['original_quote_days']+a['new_archive_quote_days']
        a['union_candidate_coverage_pct']=round(100*a['union_candidate_quote_days']/a['member_days'],6)
        a['departed_new_coverage_pct']=round(100*a['departed_new_quote_days']/a['departed_member_days'],6) if a['departed_member_days'] else ''
    write_csv(dest/'annual-price-coverage.csv',[annual[k] for k in sorted(annual)])
    write_csv(dest/'all-ticker-price-coverage.csv',[inventory[k] for k in sorted(inventory)])
    write_csv(dest/'rejected-price-rows.csv',bad)
    sources=[]
    for source in sorted({k[0] for k in annual}):
        ars=[a for (s,y),a in annual.items() if s==source]
        q=lambda field:sum(a[field] for a in ars)
        sources.append(dict(source=source,member_days=q('member_days'),original_quote_days=q('original_quote_days'),new_quote_days=q('new_archive_quote_days'),
            union_coverage_pct=round(100*(q('new_archive_quote_days')+q('original_quote_days'))/q('member_days'),6),
            departed_member_days=q('departed_member_days'),departed_new_quote_days=q('departed_new_quote_days'),
            departed_coverage_pct=round(100*q('departed_new_quote_days')/q('departed_member_days'),6)))
    summary=dict(date='2026-11-05',input_rows=len(rows),input_symbols=len({r['Name'] for r in rows}),first=min(r['date'] for r in rows),last=max(r['date'] for r in rows),
        accepted_session_rows=len(good),rejected_rows=len(bad),rejection_reasons=dict(Counter(r['reason'] for r in bad)),non_session_rows=len(non_session),
        archive_zip_sha256=ZIP_SHA,archive_csv_sha256=CSV_SHA,archive_url=URL,licence_declared='CC0-1.0 on dataset page; upstream rights not independently attested',
        dataset_page='https://www.kaggle.com/datasets/camnugent/sandp500',dataset_version=4,selection='constituents selected at Feb2018 snapshot; survivorship bias remains',
        adjustment_basis='NOT_INDEPENDENTLY_VERIFIED',security_mapping='NOT_VERIFIED',historical_backtest_eligible=False,sources=sources)
    (dest/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary


if __name__=='__main__':
    ap=argparse.ArgumentParser(__doc__);ap.add_argument('--archive',type=Path,required=True);ap.add_argument('--fetch',action='store_true');ap.add_argument('--output',type=Path,default=DEST);a=ap.parse_args()
    if a.fetch and not a.archive.exists():
        a.archive.parent.mkdir(parents=True,exist_ok=True)
        with urllib.request.urlopen(URL,timeout=60) as r:a.archive.write_bytes(r.read())
    print(json.dumps(run(a.archive,a.output),indent=2))
