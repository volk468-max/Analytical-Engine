"""Descriptive overlap/coherence audit, NOT an accuracy or retirement decision."""
import csv
import io
import hashlib
from itertools import combinations
import numpy as np


def audit_predictions(blob):
    rows = list(csv.DictReader(io.StringIO(blob.decode())))
    banks = {}
    for r in rows:
        if r['probability_raw'] == '':
            continue
        key = (r['symbol'],int(r['horizon']),int(r['threshold_pct']),r['label_type'])
        bank = banks.setdefault(r['model'],{})
        if key in bank:
            raise ValueError('DUPLICATE_AUDIT_KEY')
        bank[key] = float(r['probability_raw'])
    pairs=[]
    for a,b in combinations(sorted(banks),2):
        keys=sorted(set(banks[a])&set(banks[b]))
        x=np.array([banks[a][k] for k in keys]); y=np.array([banks[b][k] for k in keys])
        if not len(x):
            continue
        pairs.append(dict(models=[a,b],matched_targets=len(x),exact_equal=int(np.sum(x==y)),
                          mean_absolute_difference_pp=float(np.mean(np.abs(x-y))*100),
                          correlation=float(np.corrcoef(x,y)[0,1]) if np.std(x)>0 and np.std(y)>0 else None))
    violations={}
    for name,bank in banks.items():
        counts=dict(threshold=0,horizon=0,low_vs_close=0)
        for (s,h,t,l),p in bank.items():
            if t in (5,10) and (s,h,t+5,l) in bank and p+1e-12<bank[s,h,t+5,l]:
                counts['threshold']+=1
            if h==10 and (s,30,t,l) in bank and p>bank[s,30,t,l]+1e-12:
                counts['horizon']+=1
            if l=='EOD_CLOSE' and (s,h,t,'LOW_INTRADAY') in bank and p>bank[s,h,t,'LOW_INTRADAY']+1e-12:
                counts['low_vs_close']+=1
        violations[name]=counts
    return dict(csv_sha256=hashlib.sha256(blob).hexdigest(),row_count=len(rows),
                sessions=sorted({r['session_date'] for r in rows}),pairs=pairs,
                coherence_violations=violations,accuracy='NOT_EVALUATED_NO_MATURE_OUTCOMES',
                retirement_decision='NOT_SUPPORTED_BY_SINGLE_SESSION_SIMILARITY')
