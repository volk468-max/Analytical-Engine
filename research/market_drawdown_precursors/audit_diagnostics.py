"""Additional source/adjustment evidence; never infer original PIT certification."""
from common import *
from datetime import datetime,timezone

def run():
    bars,dates,calendar=load_bars();manifest=json.loads((OUT/'data/manifest.json').read_text());splits=[];eras=[]
    for src in manifest['sources']:
        s=src['symbol'];df=bars[s];events=src.get('corporate_actions',{}).get('splits',{})
        for event in events.values():
            d=datetime.fromtimestamp(event['date'],timezone.utc).date().isoformat()
            if d not in df.index:continue
            i=df.index.get_loc(d);previous=float(df.iloc[i-1]['close']) if i else None
            splits.append(dict(symbol=s,date=d,split_ratio=event.get('splitRatio'),previous_normalized_close=previous,current_normalized_close=float(df.iloc[i]['close']),normalized_close_ratio=float(df.iloc[i]['close'])/previous if previous else None,normalization='PROVIDER_SPLIT_NORMALIZED_OHLC_UNCHANGED_NO_SECOND_ADJUSTMENT',independent_action_reconciliation=False))
        for a,b in ((2000,2002),(2003,2007),(2008,2009),(2010,2019),(2020,2020),(2021,2021),(2022,2022),(2023,2026)):
            sub=df[(df.index>=f'{a}-01-01')&(df.index<=f'{b}-12-31')];eras.append(dict(symbol=s,era=f'{a}-{b}',rows=len(sub),first=sub.index[0] if len(sub) else None,last=sub.index[-1] if len(sub) else None,PIT_certified=False,predictive_role='TRAIN_DESCRIPTIVE' if b<2010 else 'CHRONOLOGICAL_REUSED_TEST'))
    write('split-quality.csv',splits);write('source-coverage-era.csv',eras)
    print('Split-basis diagnostics and era coverage saved')

if __name__=='__main__':run()
