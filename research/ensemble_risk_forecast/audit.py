"""Verify frozen objects, reconstruct every label from actual source bars."""
import csv,hashlib,json,subprocess,sys,gzip
from pathlib import Path
from study import BASE,OUT,VOTES,read_forecasts,write

def main(source):
    sha='366f8cd00e8c228d4796d0abbe9997f717a3b6ad';base='7fe91ab87dcda3607863a19074e6d7b2400503e8'
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()==sha
    inputs=[]
    for root,commit,names in [(source,sha,['data/risk-signal-v3/bars.csv','data/risk-signal-v3/manifest.json']), (Path(__file__).resolve().parents[2],base,['reports/risk-forecast-v2-predictive-validation/'+n for n in ['forecast-daily.csv.gz.b64','source-manifest.json','fit-audit.csv','protocol.md']])]:
        for name in names:
            data=(root/name).read_bytes();frozen=subprocess.check_output(['git','show',commit+':'+name],cwd=root)
            assert data==frozen
            inputs.append(dict(path=name,commit=commit,sha256=hashlib.sha256(data).hexdigest()))
    bars=list(csv.DictReader((source/'data/risk-signal-v3/bars.csv').open()));stocks={s:sorted([b for b in bars if b['symbol']==s],key=lambda b:b['close_at']) for s in ('AMD','NVDA','MU')};look={s:{b['close_at'][:10]:i for i,b in enumerate(bs)} for s,bs in stocks.items()}
    rs=read_forecasts();aud=[]
    for r in rs:
        bs=stocks[r['symbol']];i=look[r['symbol']][r['date']];future=bs[i+1:i+r['horizon']+1];close=float(bs[i]['close']);barrier=close*(1-r['threshold_pct']/100)
        assert len(future)==r['horizon'];actual=min(float(b['low']) for b in future)<=barrier+close*1e-12 if r['target']=='touch' else float(future[-1]['close'])<=barrier+close*1e-12
        assert actual==bool(r['y']);assert r['decision_at']<future[0]['open_at'];assert r['label_available_at']==future[-1]['available_at']
    for s,bs in stocks.items():
        for role in ('CALIBRATION_DIAGNOSTIC_ONLY','TEST_REUSED_HISTORY'):
            x=[r for r in rs if r['symbol']==s and r['role']==role];aud.append(dict(symbol=s,role=role,task_rows=len(x),first_anchor=min(r['date'] for r in x),last_anchor=max(r['date'] for r in x),labels_recomputed=True,availability_before_first_open=True))
    write('label-audit.csv',aud)
    inventory=[]
    for m in VOTES+('v3_score','historical'):
        inventory.append(dict(model=m,source_pr=17,source_sha=base,architecture_pr=7,architecture_sha=sha,version='PR17 strict refit of unchanged PR7 ProbabilityBank; C/sensitive v3',forecast_available_at='per-row decision_at; assumed following UTC midnight',first_saved_anchor=min(r['date'] for r in rs),last_saved_anchor=max(r['date'] for r in rs),historical_status='RETROSPECTIVE_RECONSTRUCTION_NOT_PUBLISHED_PIT',limitations='provider vintage/availability unattested; not original production payload; shared price features'))
    inventory.append(dict(model='Breadth',source_pr=16,source_sha='848610ff46f125d5369f15852d5daceca53acafa',architecture_pr='',architecture_sha='',version='EXCLUDED',forecast_available_at='UNKNOWN',first_saved_anchor='',last_saved_anchor='',historical_status='NO_VERIFIED_PIT_HISTORY',limitations='no substitution of current membership or synthetic data'))
    write('model-inventory.csv',inventory)
    import numpy,scipy,sklearn,platform
    (OUT/'source-manifest.json').write_text(json.dumps(dict(repository='volk468-max/Analytical-Engine',base_commit=base,inputs=inputs,labels_checked=len(rs),PIT_verified=False,untouched_holdout=False,python=platform.python_version(),numpy=numpy.__version__,scipy=scipy.__version__,sklearn=sklearn.__version__,raw_pack_manifest=json.loads((source/'data/risk-signal-v3/manifest.json').read_text())),indent=2)+'\n')
    print('Frozen source bytes and',len(rs),'labels/timestamps verified')

if __name__=='__main__':main(Path(sys.argv[1]).resolve())
