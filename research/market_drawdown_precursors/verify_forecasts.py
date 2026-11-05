"""Independent price-array label audit of every saved forecast and primary score."""
from common import *

def main():
    bars,dates,calendar=load_bars();rows_checked=0;score_checks=0;ms=read('metrics.csv.gz')
    for symbol in SYMBOLS:
        df=bars[symbol];lookup={d:i for i,d in enumerate(df.index)};low=df['low'].to_numpy();close=df['close'].to_numpy();available=df['available_at'].to_numpy();opens=df['open_at'].to_numpy();rs=read('forecasts-'+symbol+'.csv.gz')
        names=('HIST','REGIME','VOL','SIMPLE','PLUS_M','PLUS_S','MINIMAL')+(('PLUS_X',) if symbol in STOCK else ())
        for r in rs:
            i=lookup[r['date']];h=int(r['horizon']);t=float(r['threshold_pct']);assert i+h<len(df)
            x=float(np.min(low[i+1:i+h+1])) if r['target']=='TOUCH' else float(close[i+h]);y=float(x<=close[i]*(1-t/100)+close[i]*1e-12)
            assert y==float(r['y']);assert r['label_available_at']==available[i+h];assert r['decision_at']==available[i];assert r['decision_at']<opens[i+1]
            for m in names:
                assert np.isfinite(float(r[m])) and 0<=float(r[m])<=1
                assert np.isfinite(float(r[m+'_raw'])) and 0<=float(r[m+'_raw'])<=1
            rows_checked+=1
        for target in ('TOUCH','TERMINAL'):
         for t,h in TASKS:
          ss=[r for r in rs if r['target']==target and int(r['threshold_pct'])==t and int(r['horizon'])==h];y=np.array([float(r['y']) for r in ss])
          for model in names:
            p=np.array([float(r[model]) for r in ss]);m=next(x for x in ms if x['symbol']==symbol and x['target']==target and int(x['threshold_pct'])==t and int(x['horizon'])==h and x['model']==model and x['dimension']=='ALL' and x['operating_threshold']=='0.2');assert abs(float(m['brier'])-np.mean((p-y)**2))<1e-12;score_checks+=1
    result=dict(forecast_labels_recomputed=rows_checked,probabilities_range_checked=True,first_future_open_after_decision=True,full_horizon_maturity_checked=True,brier_recomputed_groups=score_checks,PIT_certification=False)
    (OUT/'forecast-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
