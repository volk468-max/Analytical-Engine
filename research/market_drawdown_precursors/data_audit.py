"""Stage1 only: free-source attempts and structural audit; no outcome analysis."""
import csv,gzip,hashlib,io,json,subprocess,urllib.request,urllib.error
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timedelta,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np
import exchange_calendars as xc
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'reports/market-drawdown-precursors-v1';DATA=OUT/'data'
SYMBOLS=('SPY','QQQ','SOXX','AMD','NVDA','MU');SOURCE='5d5092b5d03e16f03241c1b5a5d5a19c1816c9c7';PREFIX='reports/historical-sell-buyback-v1/data/'

def sha(b):return hashlib.sha256(b).hexdigest()
def write(name,rows):
    rows=list(rows)
    if not rows:return
    s=io.StringIO(newline='');w=csv.DictWriter(s,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows);data=s.getvalue().encode()
    (OUT/name).write_bytes(gzip.compress(data,mtime=0) if name.endswith('.gz') else data)
def gitfile(path):return subprocess.check_output(['git','show',SOURCE+':'+PREFIX+path],cwd=ROOT)

def request(symbol):
    url=f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?period1=946684800&period2=1793664000&interval=1d&includePrePost=false&events=div%2Csplits'
    now=datetime.now(timezone.utc).isoformat();result=dict(symbol=symbol,url=url,retrieved_at=now,requested_first='2000-01-01',requested_last='2026-11-02',attempts=0)
    for attempt in range(2):
        result['attempts']+=1
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'AlphaOS-research/1.0'})
            with urllib.request.urlopen(req,timeout=30) as r:data=r.read()
            obj=json.loads(data)
            if not obj.get('chart',{}).get('result'):raise ValueError('no chart result')
            result.update(status='DOWNLOADED',raw_sha256=sha(data),raw_file=f'data/fresh-{symbol}.json.gz');(OUT/result['raw_file']).write_bytes(gzip.compress(data,mtime=0));return result,obj
        except urllib.error.HTTPError as e:
            result.update(status='UNAVAILABLE',error=f'HTTP_{e.code}')
            if e.code not in (429,500,502,503,504):break
        except (OSError,ValueError,KeyError) as e:result.update(status='UNAVAILABLE',error=type(e).__name__)
    return result,None

def normalize(symbol,obj,calendar):
    r=obj['chart']['result'][0];q=r['indicators']['quote'][0];rows=[];issues=[];dates=[]
    for i,ts in enumerate(r['timestamp']):
        date=datetime.fromtimestamp(ts,timezone.utc).astimezone(ZoneInfo('America/New_York')).date().isoformat()
        if date>'2026-11-02':continue
        vals=[q[k][i] for k in ('open','high','low','close','volume')]
        if any(v is None or not np.isfinite(v) for v in vals):issues.append(date+':NULL');continue
        op,hi,lo,cl,vol=map(float,vals)
        if not (0<lo<=min(op,cl)<=max(op,cl)<=hi and vol>=0):issues.append(date+':OHLC')
        if date not in calendar:issues.append(date+':NON_SESSION');continue
        sched=calendar[date];available=(datetime.fromisoformat(date)+timedelta(days=1)).replace(tzinfo=timezone.utc).isoformat()
        rows.append(dict(symbol=symbol,date=date,open=op,high=hi,low=lo,close=cl,volume=vol,provider_bar_timestamp=ts,open_at=sched[0],close_at=sched[1],available_at=available,price_basis='PROVIDER_SPLIT_ADJUSTED_OHLC_NOT_DIVIDEND_ADJCLOSE',PIT_certified=False));dates.append(date)
    if not rows:raise ValueError('empty source')
    if len(dates)!=len(set(dates)):issues.append('DUPLICATE')
    expected={d for d in calendar if min(dates)<=d<=max(dates)};missing=sorted(expected-set(dates));issues+=['MISSING:'+d for d in missing]
    if max(dates)!='2026-11-02':issues.append('END_COVERAGE')
    return rows,issues,r

def run(acquire=True):
    assert xc.__version__=='4.11.2';DATA.mkdir(exist_ok=True)
    cal=xc.get_calendar('XNYS',start='2000-01-01',end='2026-11-02');calendar={str(d)[:10]:(cal.schedule.loc[d,'open'].isoformat(),cal.schedule.loc[d,'close'].isoformat()) for d in cal.sessions}
    write('data/calendar.csv',[dict(date=d,open_at=o,close_at=c) for d,(o,c) in calendar.items()])
    if acquire:
        with ThreadPoolExecutor(max_workers=6) as pool:fresh=list(pool.map(request,SYMBOLS))
        (DATA/'acquisition-attempts.json').write_text(json.dumps([m for m,o in fresh],indent=2)+'\n')
    else:
        attempts=json.loads((DATA/'acquisition-attempts.json').read_text());fresh=[(m,json.loads(gzip.decompress((OUT/m['raw_file']).read_bytes()))) if m['status']=='DOWNLOADED' else (m,None) for m in attempts]
    fresh_issues={};normalized={}
    for m,obj in fresh:
        if obj is None:fresh_issues[m['symbol']]=[m['error']];continue
        try:normalized[m['symbol']],fresh_issues[m['symbol']],_=normalize(m['symbol'],obj,calendar)
        except (ValueError,KeyError,TypeError) as e:fresh_issues[m['symbol']]=[type(e).__name__]
    fallback=any(fresh_issues.get(s) for s in SYMBOLS) or len(normalized)!=6
    manifest=dict(dataset_version='issue19-frozen-v1',selected='FROZEN_PR11_ALL_SIX' if fallback else 'FRESH_YAHOO_ALL_SIX',fallback_trigger=fresh_issues,original_PIT_certified=False,price_reconstruction_only=True,sources=[])
    oldmanifest=json.loads(gitfile('manifest.json'));(DATA/'pr11-manifest.json').write_bytes(gitfile('manifest.json'))
    allrows=[];inventory=[];actions=[];overlap=[]
    oldprices=list(csv.DictReader(io.StringIO(gitfile('prices.csv').decode())))
    for symbol in SYMBOLS:
        if fallback:
            data=gitfile(symbol+'.json');old=next(x for x in oldmanifest['sources'] if x['symbol']==symbol);assert sha(data)==old['raw_sha256']
            (DATA/(symbol+'.json.gz')).write_bytes(gzip.compress(data,mtime=0));obj=json.loads(data)
            meta=dict(symbol=symbol,url=old['url'],retrieved_at=old['retrieved_at'],raw_file='data/'+symbol+'.json.gz',raw_sha256=sha(data),source_commit=SOURCE,source_path=PREFIX+symbol+'.json')
        else:meta=next(m for m,o in fresh if m['symbol']==symbol);obj=next(o for m,o in fresh if m['symbol']==symbol)
        rows,issues,result=normalize(symbol,obj,calendar)
        if issues:raise ValueError('Selected panel failed audit '+symbol+':'+str(issues[:5]))
        firsttrade=result.get('meta',{}).get('firstTradeDate');firsttrade_date=datetime.fromtimestamp(firsttrade,timezone.utc).date().isoformat() if firsttrade is not None else 'UNKNOWN'
        for kind,events in result.get('events',{}).items():
            for key,event in events.items():actions.append(dict(symbol=symbol,kind=kind,provider_epoch=key,record=json.dumps(event,sort_keys=True),basis='PROVIDER_REPORTED_NOT_INDEPENDENTLY_ATTESTED'))
        bydate={r['date']:r for r in rows};diffs=[]
        for r in oldprices:
            if r['symbol']==symbol and r['date'] in bydate:
                for k in ('open','high','low','close'):diffs.append(abs(float(r[k])-bydate[r['date']][k])/max(1e-12,abs(float(r[k]))))
        overlap.append(dict(symbol=symbol,comparison_commit=SOURCE,field_comparisons=len(diffs),max_relative_difference=max(diffs) if diffs else None,selection_by_outcome=False))
        inventory.append(dict(symbol=symbol,rows=len(rows),first=rows[0]['date'],last=rows[-1]['date'],first_trade_date=firsttrade_date,missing_sessions=0,duplicates=0,ohlc_errors=0,calendar='XNYS4.11.2',source=manifest['selected'],retrospective_price_gate='PASS',PIT_certified=False,availability='ASSUMED_NEXT_UTC_MIDNIGHT',use='EXPLORATORY_PRICE_ONLY'))
        meta['corporate_actions']=result.get('events',{});meta['meta_first_trade_date']=firsttrade_date;manifest['sources'].append(meta);allrows+=rows
    write('data/prices.csv.gz',allrows);write('data-inventory.csv',inventory);write('corporate-actions.csv',actions);write('archive-overlap.csv',overlap)
    factors=[]
    for name,reason in [('VIX','NO_ATTESTED_ORIGINAL_PUBLICATION_TIMESTAMPS'),('credit_yields_liquidity','NO_ORIGINAL_VINTAGES_AND_TIMESTAMPS'),('market_breadth','NO_QUALIFIED_PIT_MEMBERSHIPS'),('sector_breadth_concentration','NO_QUALIFIED_PIT_MEMBERSHIPS_HOLDINGS'),('survivor_peer_breadth','NOT_TRUE_HISTORICAL_BREADTH_EXCLUDED_BY_PROTOCOL'),('H4_fundamental_revisions','NOT_TESTABLE_NO_ORIGINAL_DATED_ESTIMATE_VINTAGES')]:factors.append(dict(factor=name,decision='STOP_NO_GO',reason=reason,imputed=False))
    write('missing-factors.csv',factors)
    manifest['artifacts']={str(p.relative_to(OUT)):sha(p.read_bytes()) for p in sorted(DATA.iterdir()) if p.is_file() and p.name!='manifest.json'}
    (DATA/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (OUT/'data-qualification.md').write_text('''# Historical data qualification (Stage1, before outcome comparisons)

Selected panel: **'''+manifest['selected']+'''**. See data-inventory.csv for actual
coverage by input; acquisition-attempts.json records free2000 requests/errors.
Raw responses/actions, source URLs/retrieval times, normalized bars and XNYS4.11.2
calendar are frozen with SHA256 in data/manifest.json. No source stitching/filling.

All six price series passed structural OHLC/duplicate/calendar/end-coverage and
raw-normalization checks. Calendar timestamps include early closes and DST.
Source OHLC is provider split-normalized, adjclose excluded, splits not applied
twice. Corporate actions are provider reports, not independent reconciliation.
Historical original vintages/publication times and adjustment history are NOT
PIT-certified. Assumed next-midnight availability permits only conditional causal
reconstruction; it is not original release evidence. Fresh chart response alone
cannot qualify2000–2026 as a genuine PIT archive. Strict PIT-certified gate:FAIL.

Qualified scope is EXPLORATORY price-only retrospective analysis. Deployment or
validated predictive-core claim:NO-GO. Unqualified VIX/macroeconomic/breadth/
concentration/H4 inputs are STOP_NO_GO, not imputed. missing-factors.csv records all.
Data before the selected panel's actual earliest date is UNAVAILABLE, not zero.
A failed2000 request does not establish that the underlying history does not exist.

Known economic caveat: these are price-only ETF/stock labels; ex-dividend changes
are included, not dividend-adjusted total returns. Ratio invariance under a constant
split unit does not attest time-varying original provider corrections. Human source/
licensing review remains necessary; no paid provider/account/trial was activated.
''')
    print(json.dumps(dict(selected=manifest['selected'],inventory=inventory,attempt_errors=fresh_issues),indent=2))

if __name__=='__main__':
    import sys
    run('--offline' not in sys.argv)
