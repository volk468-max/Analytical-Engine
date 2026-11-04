"""Exact PR9 fixed-seven sector flag; no other market input enters the rule."""
from datetime import date,timedelta
SEMIS=['AMD','NVDA','MU','TSM','AVGO','AMAT','LRCX']
def reconstruct(prices,start,end):
    groups={}
    for r in prices:groups.setdefault(r['symbol'],[]).append(r)
    lookup={}
    for s,rows in groups.items():
        rows.sort(key=lambda r:r['date'])
        if len({r['date'] for r in rows})!=len(rows):raise ValueError('duplicate session')
        lookup[s]={r['date']:dict(r,ret5=r['close']/rows[i-5]['close']-1 if i>=5 else None) for i,r in enumerate(rows)}
    prev=None;daily=[];events=[]
    for d in sorted(lookup['QQQ']):
        q=lookup['QQQ'][d];ss=[lookup.get(s,{}).get(d) for s in SEMIS]
        valid=all(r is not None and r['ret5'] is not None for r in ss) and q['ret5'] is not None
        neg=sum(r['ret5']<0 for r in ss) if valid else None
        ret=sum(r['ret5'] for r in ss)/7 if valid else None
        flag=neg>=4 and ret<q['ret5'] if valid else None
        if start<=d<=end:
            row=dict(date=d,available_at=(date.fromisoformat(d)+timedelta(days=1)).isoformat()+'T00:00:00.000Z',sector_negative_7=neg,sector_ret5=ret,qqq_ret5=q['ret5'],sector_flag=flag,publication_status='ASSUMED_NEXT_UTC_MIDNIGHT_NOT_ORIGINAL_ARCHIVE',signal_kind='RETROSPECTIVE_RECONSTRUCTED_NOT_PRODUCTION')
            daily.append(row)
            if flag is True and prev is not True:events.append(row)
        prev=flag
    return daily,events
