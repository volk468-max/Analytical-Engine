"""Offline, source-separated historical membership/price audit. No signal or trading code."""
from __future__ import annotations

import argparse
import base64
from bisect import bisect_right
from collections import defaultdict, Counter
import csv
from datetime import date
import gzip
import hashlib
import io
import itertools
import json
from pathlib import Path
import urllib.request

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[1] / 'reports/free-historical-index-data-v1'
START, END = '2010-01-01', '2026-11-03'
SPECS = {
    'fja_sp500': ('SP500', 'fja05680/S&P 500 Historical Components & Changes (Updated).csv', '2026-09-07', 'fja_base'),
    'thuning_sp500': ('SP500', 'thuningxu/sp500_components_history.csv', '2026-06-06', 'fja_base'),
    'thuning_ndx': ('NDX100', 'thuningxu/nasdaq100_components_history.csv', '2026-06-06', 'wiki_backward'),
    'lawcal_sp500': ('SP500', 'lawcal/data/components_history.csv', '2026-10-26', 'wiki_revisions'),
}


def csv_rows(path):
    with Path(path).open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields=None, compressed=False):
    rows = list(rows)
    buf = io.StringIO(newline='')
    w = csv.DictWriter(buf, fieldnames=fields or list(rows[0]), lineterminator='\n')
    w.writeheader()
    w.writerows(rows)
    raw = buf.getvalue().encode()
    if compressed:
        packed = base64.b64encode(gzip.compress(raw, mtime=0)).decode()
        Path(path).write_text(packed+'\n')
    else:
        Path(path).write_bytes(raw)


def source_url(source):
    manifest = json.loads((OUT/'source-manifest.json').read_text())
    rel = SPECS[source][1]
    return next(x['url'] for x in manifest['files'] if x['cache_path'] == rel)


def load_snapshots(path):
    rows = csv_rows(path)
    dates, values = [], []
    for r in rows:
        date.fromisoformat(r['date'])
        tickers = r['tickers'].split(',')
        if len(tickers) != len(set(tickers)):
            raise ValueError('duplicate ticker in source snapshot')
        if dates and r['date'] <= dates[-1]:
            raise ValueError('duplicate or unsorted snapshot date')
        dates.append(r['date'])
        values.append(frozenset(tickers))
    return dates, values


def snapshot_at(dates, values, day):
    i = bisect_right(dates, day)-1
    return (values[i], dates[i]) if i >= 0 else (frozenset(), '')


def lawcal_active(r, day, require_created=True):
    # Match published list_components helper, without importing/executing upstream code.
    added = r['date_added'].rstrip('*') or '0001-01-01'
    removed = r['date_removed'].rstrip('*') or '9999-12-31'
    created = r['created_at'] or '0001-01-01'
    return added <= day < removed and (not require_created or created <= day)


def load_prices(path):
    prices = {}
    duplicates = []
    bad = []
    for r in csv_rows(path):
        key = (r['symbol'], r['date'])
        if key in prices:
            duplicates.append(key)
        try:
            o, h, l, c, v = (float(r[k]) for k in ('open', 'high', 'low', 'close', 'volume'))
            if not (0 < l <= min(o,c) <= max(o,c) <= h and v >= 0):
                bad.append(key)
        except ValueError:
            bad.append(key)
        prices[key] = r
    if duplicates or bad:
        raise ValueError(f'invalid archived OHLCV: duplicates={len(duplicates)}, invalid={len(bad)}')
    return prices


def ma_ready(prices, symbol, sessions, i, n):
    # Require consecutive exchange sessions, including current session; never fill gaps.
    return i >= n-1 and all((symbol, d) in prices for d in sessions[i-n+1:i+1])


def fetch_inputs(cache):
    manifest = json.loads((OUT/'source-manifest.json').read_text())
    if hashlib.sha256((OUT/'sessions.csv').read_bytes()).hexdigest() != manifest['calendar']['sha256']:
        raise ValueError('calendar hash mismatch')
    for r in manifest['files']:
        p = cache/r['cache_path']
        if not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            # Pinned public GitHub files only. No provider access, auth bypass or retries.
            if not r['url'].startswith('https://raw.githubusercontent.com/'):
                raise ValueError('fetch only allows pinned public GitHub inputs')
            with urllib.request.urlopen(r['url'], timeout=90) as resp:
                p.write_bytes(resp.read())
        raw = p.read_bytes()
        if hashlib.sha256(raw).hexdigest() != r['sha256']:
            raise ValueError('input SHA256 mismatch: '+r['cache_path'])
        if hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest() != r['git_blob']:
            raise ValueError('input Git blob mismatch: '+r['cache_path'])


def run(cache, output=OUT):
    output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((OUT/'source-manifest.json').read_text())
    if hashlib.sha256((OUT/'sessions.csv').read_bytes()).hexdigest() != manifest['calendar']['sha256']:
        raise ValueError('calendar hash mismatch')
    for r in manifest['files']:
        if hashlib.sha256((cache/r['cache_path']).read_bytes()).hexdigest() != r['sha256']:
            raise ValueError('input hash mismatch: '+r['cache_path'])
    sessions = [r['date'] for r in csv_rows(OUT/'sessions.csv')]
    if sessions != sorted(set(sessions)) or not all(START <= d <= END for d in sessions):
        raise ValueError('invalid frozen calendar')
    law = csv_rows(cache/SPECS['lawcal_sp500'][1])
    prices = load_prices(cache/'alphaos/prices.csv')
    pm = json.loads((cache/'alphaos/manifest.json').read_text())
    price_info = {r['symbol']: r for r in pm['sources']}
    price_symbols = set(s for s,d in prices)
    inputs, source_stats = {}, []
    for source, (idx, rel, horizon, family) in SPECS.items():
        if source == 'lawcal_sp500':
            counts = [len([r for r in law if lawcal_active(r,d)]) for d in sessions]
            source_stats.append(dict(source=source,index=idx,rows=len(law),first_date='2007-03-05',last_change_date=max(r['created_at'] for r in law),
                audited_horizon=horizon,family=family,approx_added=sum('*' in r['date_added'] for r in law),approx_removed=sum('*' in r['date_removed'] for r in law),
                min_study_count=min(counts),max_study_count=max(counts)))
        else:
            dates, vals = load_snapshots(cache/rel)
            inputs[source] = (dates, vals)
            counts = [len(v) for d,v in zip(dates,vals) if START<=d<=END]
            source_stats.append(dict(source=source,index=idx,rows=len(dates),first_date=dates[0],last_change_date=dates[-1],
                audited_horizon=horizon,family=family,approx_added='',approx_removed='',min_study_count=min(counts),max_study_count=max(counts)))
    master = []
    for i,r in enumerate(law):
        master.append(dict(source_record_id=f'lawcal:{i:04d}',issuer_cik=r['cik'],security_id='',symbol=r['symbol'],name=r['name'],
            date_added=r['date_added'],date_removed=r['date_removed'],created_at=r['created_at'],identity_quality='ISSUER_CIK_ONLY_NOT_SECURITY_ID'))
    write_csv(output/'issuer-security-records.csv', master)
    timeline = defaultdict(list)
    daily, disagreements = [], []
    membership = {}
    alt_date_diffs = []
    events = []
    previous = {}
    # First reconstruct independently; no choice of a canonical index history.
    for day in sessions:
        daysets = {}
        for source,(idx, rel, horizon, family) in SPECS.items():
            if source == 'lawcal_sp500':
                active = [r for r in law if lawcal_active(r,day)]
                tickers = frozenset(r['symbol'] for r in active)
                rowdate = max((max(r['created_at'],r['date_added'].rstrip('*')) for r in active), default='')
                alt = frozenset(r['symbol'] for r in law if lawcal_active(r,day,False))
                if alt != tickers:
                    alt_date_diffs.append(dict(date=day,only_effective=';'.join(sorted(alt-tickers)),only_helper=';'.join(sorted(tickers-alt))))
                duplicate_count = len(active)-len(tickers)
                approx = sum('*' in r['date_added'] or '*' in r['date_removed'] for r in active)
                issuers = len({r['cik'] for r in active})
            else:
                tickers,rowdate = snapshot_at(*inputs[source],day)
                duplicate_count,approx,issuers = 0,'',''
            daysets[source] = tickers
            membership[source,day] = tickers
            timeline[source].append(tickers)
            stale = day > horizon
            daily.append(dict(date=day,index=idx,source=source,source_row_date=rowdate,source_horizon=horizon,
                quality='STALE_UNCONFIRMED' if stale else 'APPROXIMATE_SOURCE_RECONSTRUCTION',component_count=len(tickers),
                unique_issuer_ciks=issuers,duplicate_tickers=duplicate_count,approximate_date_records=approx,
                security_ids_verified=0,full_membership_verified=False,tickers=';'.join(sorted(tickers))))
            if source in previous:
                old = previous[source]
                for action,delta in [('add',tickers-old),('remove',old-tickers)]:
                    for t in sorted(delta):
                        matches = [r for r in law if r['symbol']==t and (lawcal_active(r,day) or lawcal_active(r,sessions[max(0,sessions.index(day)-1)]))]
                        events.append(dict(index=idx,source=source,date=day,action=action,symbol=t,issuer_cik=';'.join(sorted({r['cik'] for r in matches})),
                            security_id='',announcement_date='',effective_date_verified=False,quality='STALE_UNCONFIRMED' if stale else 'SOURCE_ASSERTED_UNCONFIRMED',source_url=source_url(source)))
            previous[source] = tickers
        for a,b in itertools.combinations([s for s in SPECS if SPECS[s][0]=='SP500'],2):
            if daysets[a] != daysets[b]:
                disagreements.append(dict(date=day,source_a=a,source_b=b,only_a=';'.join(sorted(daysets[a]-daysets[b])),only_b=';'.join(sorted(daysets[b]-daysets[a])),
                    shared_lineage=SPECS[a][3]==SPECS[b][3],tail_stale=day>SPECS[a][2] or day>SPECS[b][2]))
    # Compress each constant disagreement into exact trading-date intervals, per ticker.
    intervals = {}
    for r in disagreements:
        for side in ['only_a','only_b']:
            for ticker in r[side].split(';'):
                if not ticker:
                    continue
                key=(r['source_a'],r['source_b'],side,ticker)
                intervals.setdefault(key,[]).append(r)
    disputes = []
    day_index = {d:i for i,d in enumerate(sessions)}
    for (a,b,side,ticker),rows in sorted(intervals.items()):
        groups=[]
        for r in rows:
            if not groups or day_index[r['date']]!=day_index[groups[-1][-1]['date']]+1 or r['tail_stale']!=groups[-1][-1]['tail_stale']:
                groups.append([])
            groups[-1].append(r)
        for group in groups:
            names = sorted({r['name'] for r in law if r['symbol']==ticker})
            disputes.append(dict(index='SP500',first_date=group[0]['date'],last_date=group[-1]['date'],sessions=len(group),
                source_a=a,source_b=b,side=side,symbol=ticker,names=';'.join(names) or 'UNKNOWN',
                issuer_cik=';'.join(sorted({r['cik'] for r in law if r['symbol']==ticker})),security_id='',
                shared_lineage=group[0]['shared_lineage'],tail_stale=group[0]['tail_stale'],resolution='UNRESOLVED_NO_CANONICAL_CHOICE',
                source_a_url=source_url(a),source_b_url=source_url(b)))
    write_csv(output/'source-disagreements.csv',disputes)
    write_csv(output/'daily-membership.csv.gz.b64',daily,compressed=True)
    write_csv(output/'membership-changes.csv',events)
    write_csv(output/'lawcal-date-semantics.csv',alt_date_diffs)
    # Conservative ticker-exact inventory; no silent FB->META or old->new security substitution.
    inventory=[]
    annual=[]
    for source,(idx,rel,horizon,family) in SPECS.items():
        dates_by_ticker=defaultdict(list)
        for d,ts in zip(sessions,timeline[source]):
            for t in ts:
                dates_by_ticker[t].append(d)
        departed={t for t,ds in dates_by_ticker.items() if ds[-1] < min(END,horizon)}
        # 'Departed' is source-observed index exit, NOT exchange delisting or company death.
        for t,ds in sorted(dates_by_ticker.items()):
            matched=sum((t,d) in prices for d in ds)
            info=price_info.get(t,{})
            inventory.append(dict(index=idx,source=source,symbol=t,first_member_session=ds[0],last_member_session=ds[-1],
                source_observed_departure=t in departed,exchange_delisted_status='UNKNOWN',
                issuer_cik=';'.join(sorted({r['cik'] for r in law if r['symbol']==t})),security_id='',
                member_sessions=len(ds),matched_ohlcv_sessions=matched,ohlcv_coverage_pct=round(100*matched/len(ds),6),
                quote_first=info.get('first',''),quote_last=info.get('last',''),provider_status='ARCHIVE_EXACT_TICKER_CANDIDATE' if matched else 'NOT_ACQUIRED_NOT_PROOF_UNAVAILABLE',
                corporate_action_events=len(info.get('corporate_actions',{}).get('splits',{})),verified_security_mapping=False,
                confirmed_pit_quote_sessions=0,live_provider_all_symbols_queried=False))
        for year in range(2010,2027):
            ydays=[(i,d) for i,d in enumerate(sessions) if d.startswith(str(year))]
            sets=[membership[source,d] for i,d in ydays]
            universe=set().union(*sets)
            member_days=sum(len(ts) for ts in sets)
            priced={t for t in universe if any(t in membership[source,d] and (t,d) in prices for i,d in ydays)}
            matched=sum((t,d) in prices for i,d in ydays for t in membership[source,d])
            ma50=sum(ma_ready(prices,t,sessions,i,50) for i,d in ydays for t in membership[source,d] if t in price_symbols)
            ma200=sum(ma_ready(prices,t,sessions,i,200) for i,d in ydays for t in membership[source,d] if t in price_symbols)
            depart_days=sum(t in departed for i,d in ydays for t in membership[source,d])
            depart_prices=sum(t in departed and (t,d) in prices for i,d in ydays for t in membership[source,d])
            annual.append(dict(index=idx,source=source,year=year,period='YTD_TO_2026_11_03' if year==2026 else 'FULL_CALENDAR_YEAR',
                trading_sessions=len(ydays),min_candidate_count=min(map(len,sets)),max_candidate_count=max(map(len,sets)),
                candidate_unique_tickers=len(universe),candidate_member_observations=member_days,confirmed_components=0,
                components_with_archived_quotes=len(priced),component_any_quote_pct=round(100*len(priced)/len(universe),6),
                archived_quote_observations=matched,quote_observation_coverage_pct=round(100*matched/member_days,6),
                missing_or_ambiguous_securities=len(universe),not_acquired_tickers=len(universe-priced),
                unconfirmed_changes=sum(e['source']==source and e['date'].startswith(str(year)) for e in events),
                ma50_candidate_observations=ma50,ma200_candidate_observations=ma200,ma50_confirmed_observations=0,ma200_confirmed_observations=0,
                departed_unique_tickers=len(universe&departed),departed_member_observations=depart_days,departed_quote_observations=depart_prices,
                departed_quote_coverage_pct=round(100*depart_prices/depart_days,6) if depart_days else '',
                stale_sessions=sum(d>horizon for i,d in ydays),confirmed_full_membership_sessions=0))
    write_csv(output/'historical-membership-coverage.csv',annual)
    write_csv(output/'delisted-price-coverage.csv',inventory)
    write_csv(output/'source-statistics.csv',source_stats)
    write_csv(output/'daily-source-disagreements.csv.gz.b64',disagreements,compressed=True)
    summary=dict(study_start=sessions[0],study_end=sessions[-1],sessions=len(sessions),daily_source_rows=len(daily),
        annual_rows=len(annual),source_ticker_inventory_rows=len(inventory),disagreement_intervals=len(disputes),
        sp500_disagreement_pair_days=len(disagreements),sp500_any_disagreement_days=len({r['date'] for r in disagreements}),
        lawcal_effective_vs_helper_days=len(alt_date_diffs),lawcal_records=len(law),lawcal_issuer_ciks=len({r['cik'] for r in law}),
        lawcal_repeated_symbols=sum(v>1 for v in Counter(r['symbol'] for r in law).values()),
        archived_price_rows=len(prices),archived_symbols=sorted(price_symbols),full_membership_verified=False,
        historical_backtest_eligible=False,live_provider_all_symbols_queried=False,
        source_totals=[dict(source=s,candidate_member_observations=sum(r['candidate_member_observations'] for r in annual if r['source']==s),
            archived_quote_observations=sum(r['archived_quote_observations'] for r in annual if r['source']==s),
            source_unique_tickers=sum(r['source']==s for r in inventory),departed_source_tickers=sum(r['source']==s and r['source_observed_departure'] for r in inventory),
            departed_quote_observations=sum(r['departed_quote_observations'] for r in annual if r['source']==s)) for s in SPECS])
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary


def main():
    ap=argparse.ArgumentParser(__doc__)
    ap.add_argument('--cache',type=Path,required=True)
    ap.add_argument('--fetch',action='store_true',help='download pinned public GitHub files; no market-provider calls')
    ap.add_argument('--output',type=Path,default=OUT)
    args=ap.parse_args()
    if args.fetch:
        fetch_inputs(args.cache)
    print(json.dumps(run(args.cache,args.output),indent=2))


if __name__=='__main__':
    main()
