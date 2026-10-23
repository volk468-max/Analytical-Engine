"""Frozen AMD OHLCV source acquisition for the 2021–2026 research pack."""
import csv
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen


def main():
    root=Path('data/core-tactical-ladder'); root.mkdir(parents=True,exist_ok=True)
    url='https://query1.finance.yahoo.com/v8/finance/chart/AMD?period1=1609459200&period2=1792800000&interval=1d&events=div%2Csplits'
    retrieved=datetime.now(timezone.utc)
    with urlopen(Request(url,headers={'User-Agent':'AlphaOS offline research/1.0'}),timeout=30) as response:
        raw=response.read()
    (root/'amd-source.json').write_bytes(raw)
    result=json.loads(raw)['chart']['result'][0]
    quote=result['indicators']['quote'][0]
    adjusted=result['indicators']['adjclose'][0]['adjclose']
    rows=[]; excluded=[]; differences=[]
    for i,ts in enumerate(result['timestamp']):
        opened=datetime.fromtimestamp(ts,timezone.utc)
        closed=opened+timedelta(hours=6,minutes=30)
        available=datetime.combine(opened.date()+timedelta(days=1),datetime.min.time(),timezone.utc)
        if opened.date().isoformat()>'2026-10-22' or available>retrieved:
            excluded.append(opened.date().isoformat()); continue
        values=[quote[key][i] for key in ('open','high','low','close','volume')]
        if any(v is None for v in values):
            raise ValueError('Missing OHLCV: '+opened.date().isoformat())
        differences.append(abs(adjusted[i]-values[3]) if adjusted[i] is not None else float('inf'))
        rows.append(dict(symbol='AMD',session=opened.date().isoformat(),open_at=opened.isoformat(),
            close_at=closed.isoformat(),available_at=available.isoformat(),
            **dict(zip(('open','high','low','close','volume'),values)),source='Yahoo chart',
            verified='false',price_basis='provider_ohlc_no_in_window_adjustments'))
    actions=result.get('events',{})
    # No silent mixing of adjusted/unadjusted prices or invented dividend payment dates.
    if actions.get('splits') or actions.get('dividends') or max(differences)>1e-5:
        raise ValueError('Corporate actions/adjustment mismatch require a nominal-price conversion ledger before research')
    with (root/'amd.csv').open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=list(rows[0]),lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)
    (root/'corporate-actions.json').write_text(json.dumps(actions,indent=2)+'\n')
    manifest=dict(schema_version=1,dataset_version='amd-2021-2026-asof-2026-10-23-v1',symbol='AMD',url=url,retrieved_at=retrieved.isoformat(),
        first=rows[0]['session'],last=rows[-1]['session'],rows=len(rows),excluded_sessions=excluded,
        adjustment_max_abs_difference=max(differences),reported_splits=len(actions.get('splits',{})),
        reported_dividends=len(actions.get('dividends',{})),
        artifact_sha256={name:hashlib.sha256((root/name).read_bytes()).hexdigest()
                         for name in ('amd-source.json','amd.csv','corporate-actions.json')},
        limitations=['Retrospective provider vintage; not an independently verified publication archive.',
                     'OHLC used consistently; adjusted closes used only to check for in-window adjustments.',
                     'No reported splits/dividends in requested window; provider action completeness is not independently attested.',
                     'Bar availability inferred next UTC midnight; early closes conservatively delayed.',
                     'Session 2026-10-23 is excluded even if later revised to complete.'])
    (root/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({key:manifest[key] for key in ('first','last','rows','reported_splits','reported_dividends','adjustment_max_abs_difference')}))


if __name__=='__main__':
    main()
