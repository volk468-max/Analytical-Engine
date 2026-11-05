"""Audit frozen inputs / package computed CSVs; no new provider requests."""
import base64,csv,gzip,hashlib,json,sys
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
from study import OUT,write,SOURCE_SHA


def main(source):
    raw=list(csv.DictReader((source/'data/risk-signal-v3/bars.csv').open()))
    manifest=json.load(open(source/'data/risk-signal-v3/manifest.json'))
    actions=[]
    for s in manifest['sources']:
        for kind,events in s.get('reported_corporate_actions',{}).items():
            for key,r in events.items():actions.append(dict(symbol=s['symbol'],kind=kind,provider_epoch=key,provider_record=json.dumps(r,sort_keys=True),interpretation='FROZEN_PROVIDER_EVENT_NOT_VERIFIED_VINTAGE'))
    write('corporate-actions.csv',actions)
    quality=[]
    with gzip.open(source/'reports/risk-signal-v3/daily-signals.jsonl.gz','rt') as f:
        for line in f:
            r=json.loads(line)
            if r['variant']!='C' or r['mode']!='fixed_balanced':continue
            q=r['quality'];future=sum(v is not None and str(v)>r['decision_at'] for k,v in q.items() if k.endswith('_available_at'))
            quality.append(dict(symbol=r['symbol'],date=r['date'],decision_at=r['decision_at'],data_status=r['data_status'],future_available_fields=future,
                historical_vintage_verified=q['publication_vintage_verified'],fundamentals_used=False,record_type='RECONSTRUCTED_FROM_REAL_FROZEN_OBSERVATIONS'))
    write('feature-audit.csv',quality)
    if any(r['future_available_fields'] for r in quality):raise ValueError('feature lookahead')
    # Keep the published source packs external; pin every actual input by Git tree and SHA256.
    used=['data/risk-signal-v3/manifest.json','data/risk-signal-v3/bars.csv','data/risk-signal-v3/markets.json',
          'reports/risk-signal-v3/daily-signals.jsonl.gz','reports/risk-signal-v3/fold-selection.csv',
          'aae/research/risk_forecast.py','aae/research/risk_forecast_study.py','aae/research/risk_forecast_statistics.py',
          'aae/research/risk_signal_v3.py','aae/research/risk_v3_features.py']
    (OUT/'source-manifest.json').write_text(json.dumps(dict(repository='volk468-max/Analytical-Engine',commit=SOURCE_SHA,files=[dict(path=n,sha256=hashlib.sha256((source/n).read_bytes()).hexdigest(),url='https://github.com/volk468-max/Analytical-Engine/blob/'+SOURCE_SHA+'/'+n) for n in used],data_pack_manifest=manifest,independent_pit=False),indent=2)+'\n')
    (OUT/'forecast-daily.csv.gz.b64').write_bytes(base64.b64encode((OUT/'forecast-daily.csv.gz').read_bytes())+b'\n')
    # First chronological false/missed alerts, all27 stock/task pairs; no outcome cherry-picking.
    with gzip.open(OUT/'forecast-daily.csv.gz','rt') as f:rs=list(csv.DictReader(f))
    examples=[]
    for symbol in ('AMD','NVDA','MU'):
      for h in ('5','10','20'):
       for t in ('5.0','10.0','15.0'):
        group=sorted([r for r in rs if r['symbol']==symbol and r['horizon']==h and r['threshold_pct']==t and r['target']=='touch' and r['role']=='TEST_REUSED_HISTORY'],key=lambda r:r['date'])
        for typ in ('FALSE_ALERT','MISSED_TOUCH'):
            cases=[r for r in group if float(r['technical_plus_v3'])>=.5 and r['y']=='False'] if typ=='FALSE_ALERT' else [r for r in group if float(r['technical_plus_v3'])<.5 and r['y']=='True']
            r=cases[0] if cases else None
            examples.append(dict(symbol=symbol,horizon=h,threshold_pct=t,category=typ,qualifying_rows=len(cases),date=r['date'] if r else None,
                probability=r['technical_plus_v3'] if r else None,terminal_return_pct=r['terminal_return_pct'] if r else None,status='FIRST_CHRONOLOGICAL' if r else 'NONE_NO_EXAMPLE_FABRICATED'))
    write('error-examples.csv',examples)
    # Reliability curves use descriptive bin rates, not independent confidence bands.
    import matplotlib
    matplotlib.use('Agg');import matplotlib.pyplot as plt
    plt.rcParams['svg.hashsalt']='risk-forecast-validation-frozen'
    bins=list(csv.DictReader((OUT/'reliability.csv').open()))
    fig,axs=plt.subplots(3,3,figsize=(11,10))
    for i,h in enumerate(('5','10','20')):
      for j,t in enumerate(('5.0','10.0','15.0')):
        ax=axs[i,j];ax.plot([0,1],[0,1],'k--',linewidth=.5)
        for model in ('technical_plus_v3','historical','volatility','regime'):
            rr=[r for r in bins if r['symbol']=='ALL' and r['target']=='touch' and r['horizon']==h and r['threshold_pct']==t and r['model']==model and int(r['n'])>0]
            ax.plot([float(r['mean_probability']) for r in rr],[float(r['observed_rate']) for r in rr],'.-',label=model,linewidth=.7)
        ax.set(xlim=(0,1),ylim=(0,1),title=f'Down {t}% / {h} sessions',xlabel='Mean forecast',ylabel='Observed touch rate')
    axs[0,0].legend(fontsize=6);fig.suptitle('Reused history, dependent bins: descriptive reliability only');fig.tight_layout()
    fig.savefig(OUT/'calibration-curves.svg',metadata={'Date':None});plt.close(fig)
    svg=OUT/'calibration-curves.svg';svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')


if __name__=='__main__':main(Path(sys.argv[1]).resolve())
