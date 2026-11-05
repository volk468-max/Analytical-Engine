"""Exploratory dependent intervals for correlations and ablations by strata."""
import csv,gzip
import numpy as np
import study

def main(source):
    bars=list(csv.DictReader((source/'data/risk-signal-v3/bars.csv').open()));study.CALENDAR=sorted({r['close_at'][:10] for r in bars if r['symbol']=='AMD'})
    with gzip.open(study.OUT/'predictions.csv.gz','rt') as f:pred=list(csv.DictReader(f))
    for r in pred:
        r['y']=float(r['y']);r['test_year']=int(r['test_year'])
        for k in study.VOTES+tuple('without_'+m for m in study.VOTES)+('C',):r[k]=float(r[k])
    correlations=[];added=[]
    for target in ('touch','terminal'):
     for h in ('5','10','20'):
      for t in ('5.0','10.0','15.0'):
       task=[r for r in pred if r['target']==target and r['horizon']==h and r['threshold_pct']==t]
       for dim,vs in (('ALL',('ALL',)),('symbol',('AMD','NVDA','MU')),('test_year',(2024,2025,2026)),('regime',('UP','DOWN','MIXED'))):
        for val in vs:
            rs=[r for r in task if dim=='ALL' or r['market_regime' if dim=='regime' else dim]==val]
            if not rs:continue
            ds=[d for d in study.CALENDAR if min(r['date'] for r in rs)<=d<=max(r['date'] for r in rs)];idx=np.array([ds.index(r['date']) for r in rs]);w=np.vstack([np.ones(len(rs)),study.counts(len(ds),399)[:,idx]]);den=w.sum(axis=1)
            mean=lambda x:study.ratio(w@x,den)
            y=np.array([r['y'] for r in rs]);ctx=dict(target=target,horizon=h,threshold_pct=t,dimension=dim,value=val,n=len(rs))
            errors={m:np.array([r[m] for r in rs])-y for m in study.VOTES}
            for m,a in errors.items():
                for b,z in errors.items():
                    cov=mean(a*z)-mean(a)*mean(z);va=np.maximum(0,mean(a*a)-mean(a)**2);vb=np.maximum(0,mean(z*z)-mean(z)**2);c=study.ratio(cov,np.sqrt(va*vb));lo,hi=study.interval(c[1:]);correlations.append(dict(ctx,model=m,other=b,error_correlation=c[0],low=lo,high=hi))
                d=(np.array([r['without_'+m] for r in rs])-y)**2-(np.array([r['C'] for r in rs])-y)**2;b=mean(d);lo,hi=study.interval(b[1:]);added.append(dict(ctx,model=m,delta_brier_without_minus_full=b[0],low=lo,high=hi))
    study.write('error-correlation-strata.csv',correlations);study.write('added-value-strata.csv',added)

if __name__=='__main__':
    import sys
    from pathlib import Path
    main(Path(sys.argv[1]))
