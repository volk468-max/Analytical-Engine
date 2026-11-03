import csv,hashlib,json,math
from datetime import datetime,timezone
from pathlib import Path
import exchange_calendars as xc
from research.historical_sell_buyback.signals import reconstruct
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'reports/historical-sell-buyback-v1'
STOCKS=['AMD','NVDA','MU','TSM','AVGO','AMAT','AMZN','META','PLTR','LRCX','NBIS']
def write(n,rows):
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with (R/n).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=keys,lineterminator='\n');w.writeheader();w.writerows(rows)
def main():
    assert json.loads((R/'control/gate.json').read_text())['gate_passed']
    manifest=json.loads((R/'data/manifest.json').read_text());raw=list(csv.DictReader((R/'data/prices.csv').open()))
    for e in manifest['sources']:
        assert e['status']=='DOWNLOADED',e
        assert hashlib.sha256((R/'data'/e['raw_file']).read_bytes()).hexdigest()==e['raw_sha256']
    actions=[]
    for e in manifest['sources']:
        for kind,evs in e['corporate_actions'].items():
            for a in evs.values():
                d=datetime.fromtimestamp(a['date'],timezone.utc).date().isoformat()
                if d<='2026-11-02':actions.append(dict(symbol=e['symbol'],date=d,kind=kind,amount=a.get('amount'),ratio=a.get('numerator',1)/a.get('denominator',1)))
    def factor(s,d):return math.prod(a['ratio'] for a in actions if a['symbol']==s and a['kind']=='splits' and a['date']>d)
    prices=[]
    for x in raw:
        s=x['symbol'];d=x['date'];f=factor(s,d)
        prices.append(dict(symbol=s,date=d,**{k:float(x[k]) for k in ['open','high','low','close']},volume=int(float(x['volume'])),split_future_factor=f,nominal_close=float(x['close'])*f,available_at=x['available_at'],publication_verified=False))
    daily,signals=reconstruct(prices,'2021-01-01','2026-11-02');write('historical-signals.csv',signals);write('sector-daily.csv',daily)
    # Gate AGAIN on new provider history: stop on dates or frozen price revisions before long economics.
    _,control=reconstruct(prices,'2026-09-01','2026-11-02');expected=json.loads((R/'control/gate.json').read_text())['signal_dates'];assert [x['date'] for x in control]==expected,'new-history control signals differ'
    old=json.loads((R/'control/pr10/reports/fixed-5pct-buyback-v1/inputs/inputs.json').read_text());lookup={(x['symbol'],x['date']):x for x in prices};overlap=0
    for x in old['prices']:
        s='^SOX' if x['symbol']=='SOX' else x['symbol']
        for k in ['open','high','low','close']:assert abs(x[k]-lookup[s,x['date']][k])<1e-5,(s,x['date'],k)
        overlap+=1
    cal=xc.get_calendar('XNYS',start='2019-12-01',end='2026-11-15');ss=cal.sessions_in_range('2021-01-01','2026-11-02')
    calendar=[dict(date=s.date().isoformat(),open_at=cal.schedule.loc[s,'open'].isoformat(),close_at=cal.schedule.loc[s,'close'].isoformat()) for s in ss];write('calendar.csv',calendar);dates=[x['date'] for x in calendar]
    groups={}
    for x in prices:groups.setdefault(x['symbol'],[]).append(x)
    coverage=[];eligible={};unitchecks=[]
    for s,rows in groups.items():
        rows.sort(key=lambda x:x['date'])
        start='2024-10-21' if s=='NBIS' else '2021-01-04'
        if s in STOCKS:
            entry=next(x['date'] for x in rows if x['date']>=start);eligible[s]=entry
            want={d for d in dates if d>=entry};have={x['date'] for x in rows if x['date']>=entry}
            assert have==want,(s,'missing or non-session equity quotes',sorted(want-have))
        else:entry=next(x['date'] for x in rows if x['date']>='2021-01-04')
        coverage.append(dict(symbol=s,first_provider_date=rows[0]['date'],study_entry=entry,last=rows[-1]['date'],study_rows=sum(x['date']>=entry for x in rows),status='COMPLETE_AFTER_ELIGIBILITY' if s in STOCKS else 'CONTEXT_ONLY',universe_bias='FIXED_CURRENT_SURVIVORS'))
        for i in range(5,len(rows)):
            now,prev=rows[i],rows[i-5];effective=math.prod(a['ratio'] for a in actions if a['symbol']==s and a['kind']=='splits' and prev['date']<a['date']<=now['date'])
            causal=now['nominal_close']/prev['nominal_close']*effective-1;adjusted=now['close']/prev['close']-1
            assert abs(causal-adjusted)<1e-11,(s,now['date'])
            if effective!=1:unitchecks.append(dict(symbol=s,date=now['date'],causal_known_effective_splits=effective,causal_return5=causal,constant_unit_return5=adjusted,match=True))
    write('data-coverage.csv',coverage);write('corporate-actions.csv',actions);write('split-return-invariance.csv',unitchecks)
    # Fixed rule: later entrant's equal11 slot remains cash; comparable portfolio excludes it.
    assert eligible['NBIS']=='2024-10-21'
    q=groups['QQQ'];regimes=[]
    for i,x in enumerate(q):
        ma=sum(v['close'] for v in q[i-199:i+1])/200 if i>=199 else None;ret=x['close']/q[i-20]['close']-1 if i>=20 else None
        state='UNKNOWN' if ma is None or ret is None else 'BULL' if x['close']>ma and ret>0 else 'BEAR' if x['close']<ma and ret<0 else 'SIDEWAYS'
        regimes.append(dict(date=x['date'],close=x['close'],ma200=ma,return20=ret,regime=state))
    write('regimes.csv',regimes)
    payload=dict(prices=prices,actions=actions,eligible=eligible,calendar=calendar,signals=signals,source_manifest_sha256=hashlib.sha256((R/'data/manifest.json').read_bytes()).hexdigest(),control_new_history_dates_match=True,control_overlap_prices_match=overlap,corporate_unit_checks=len(unitchecks))
    (R/'prepared.json').write_text(json.dumps(payload,separators=(',',':'))+'\n');print(json.dumps(dict(sessions=len(calendar),signals=len(signals),eligible=eligible,overlap=overlap,split_windows=len(unitchecks))))
if __name__=='__main__':main()
