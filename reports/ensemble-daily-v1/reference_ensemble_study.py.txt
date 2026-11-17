"""Frozen exploratory ensemble evaluation. No production imports or network I/O."""
import base64,csv,gzip,hashlib,io,json,sys
from pathlib import Path
import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import expit,logit
from sklearn.linear_model import LogisticRegression
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/ensemble-risk-forecast-v1'
BASE=ROOT/'reports/risk-forecast-v2-predictive-validation'
SOURCE=Path('/workspace/forecast-source')
VOTES=('technical_combined','v3_state','technical_plus_v3','volatility','regime')
BASELINES=('historical','volatility','regime')
ENSEMBLES=('A2','A3','A4','A5','B','C')
MODELS=VOTES+('v3_score','historical')+ENSEMBLES
PRIMARY_REPS=9999

def write(name,rows):
    rows=list(rows)
    if not rows:return
    f=io.StringIO(newline='');w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
    data=f.getvalue().encode()
    if name.endswith('.gz'):data=gzip.compress(data,mtime=0)
    (OUT/name).write_bytes(data)

def read_forecasts():
    data=gzip.decompress(base64.b64decode((BASE/'forecast-daily.csv.gz.b64').read_bytes()))
    rs=list(csv.DictReader(io.StringIO(data.decode())))
    for r in rs:
        for k in VOTES+('historical','v3_score'):r[k]=float(r[k])
        r['y']=float(r['y']=='True');r['horizon']=int(r['horizon']);r['threshold_pct']=float(r['threshold_pct']);r['test_year']=int(r['test_year'])
    return rs

def assign_market_regimes(raw,source):
    with (source/'data/risk-signal-v3/bars.csv').open() as f:
        qqq=sorted([r for r in csv.DictReader(f) if r['symbol']=='QQQ'],key=lambda r:r['close_at'])
    mapping={}
    for at in sorted({r['decision_at'] for r in raw}):
        known=[r for r in qqq if r['available_at']<=at]
        if len(known)<200:raise ValueError('missing regime warmup')
        close=float(known[-1]['close']);ma=np.mean([float(r['close']) for r in known[-200:]]);ret=close/float(known[-21]['close'])-1
        mapping[at]='UP' if close>=ma and ret>0 else ('DOWN' if close<ma and ret<=0 else 'MIXED')
    for r in raw:r['market_regime']=mapping[r['decision_at']]
    return raw

def counts(n,reps=999,length=40):
    rng=np.random.default_rng(42117);starts=rng.integers(0,n,(reps,(n+length-1)//length))
    idx=((starts[:,:,None]+np.arange(length))%n).reshape(reps,-1)[:,:n]
    c=np.zeros((reps,n));np.add.at(c,(np.arange(reps)[:,None],idx),1);return c

def interval(v):
    a=np.asarray(v);a=a[np.isfinite(a)]
    return tuple(float(x) for x in np.quantile(a,[.025,.975])) if len(a)>=.8*len(v) and len(a)>=20 else (None,None)

def ratio(a,b):
    return np.divide(a,b,out=np.full(np.broadcast_shapes(np.shape(a),np.shape(b)),np.nan),where=b>0)

def logloss(y,p):
    p=np.clip(p,1e-6,1-1e-6);return -y*np.log(p)-(1-y)*np.log1p(-p)

def fit_stack(train,cal,keys=VOTES):
    X=np.array([[r[k] for k in keys] for r in train]);y=np.array([r['y'] for r in train]);Z=logit(np.clip(X,1e-6,1-1e-6))
    if len(set(y))<2:
        coef=np.zeros(len(keys));inter=logit((y.sum()+1)/(len(y)+2))
    else:
        model=LogisticRegression(C=.1,max_iter=2000,solver='lbfgs',tol=1e-9).fit(Z,y)
        if model.n_iter_[0]>=2000:raise ValueError('nonconverged meta model')
        coef=model.coef_[0];inter=model.intercept_[0]
    z=np.array([[r[k] for k in keys] for r in cal]);cy=np.array([r['y'] for r in cal]);eta=logit(np.clip(z,1e-6,1-1e-6))@coef+inter
    fun=lambda a:float(np.sum(logloss(cy,expit(eta+a)))+.5*a*a)
    res=minimize_scalar(fun,bounds=(-15,15),method='bounded',options={'xatol':1e-10})
    if not res.success:raise ValueError('calibration convergence')
    return coef,float(inter),float(res.x)

def predict_stack(rs,fit,keys=VOTES):
    coef,inter,shift=fit
    return expit(logit(np.clip(np.array([[r[k] for k in keys] for r in rs]),1e-6,1-1e-6))@coef+inter+shift)

def meta_split(rs):
    dates=sorted({r['date'] for r in rs});mid=len(dates)//2;start=dates[mid+20]
    train=[r for r in rs if r['date']<dates[mid] and r['label_available_at']<start]
    cal=[r for r in rs if r['date']>=start]
    if not train or not cal:raise ValueError('empty meta/cal')
    assert max(r['label_available_at'] for r in train)<min(r['decision_at'] for r in cal)
    return train,cal

def make_predictions(raw):
    output=[];audit=[];weights=[]
    for year in (2024,2025,2026):
      for target in ('touch','terminal'):
       for h in (5,10,20):
        for t in (5.,10.,15.):
            context=dict(test_year=year,target=target,horizon=h,threshold_pct=t)
            task=[r for r in raw if all(r[k]==v for k,v in context.items())]
            tr,cal=meta_split([r for r in task if r['role']=='CALIBRATION_DIAGNOSTIC_ONLY'])
            test=[dict(r) for r in task if r['role']=='TEST_REUSED_HISTORY'];assert test
            assert max(r['label_available_at'] for r in cal)<min(r['decision_at'] for r in test)
            audit.append(dict(context,meta_n=len(tr),cal_n=len(cal),test_n=len(test),meta_first=min(r['date'] for r in tr),meta_last=max(r['date'] for r in tr),meta_maturity_max=max(r['label_available_at'] for r in tr),cal_first=min(r['decision_at'] for r in cal),cal_last=max(r['date'] for r in cal),cal_maturity_max=max(r['label_available_at'] for r in cal),test_first=min(r['decision_at'] for r in test),base_fit_cutoff=f'{year-1}-01-01',purge_sessions=20))
            for drop in (None,)+VOTES:
                keys=tuple(k for k in VOTES if k!=drop);fit=fit_stack(tr,cal,keys);p=predict_stack(test,fit,keys)
                weights.append(dict(context,omitted=drop or 'NONE',coefficients=json.dumps(dict(zip(keys,map(float,fit[0]))),sort_keys=True),intercept=fit[1],calibration_intercept=fit[2],ridge_C=.1))
                for r,x in zip(test,p):r['C' if drop is None else 'without_'+drop]=float(x)
            prior=(sum(r['y'] for r in tr)+1)/(len(tr)+2)
            for k in (2,3,4,5):
                rates={}
                for flag in (False,True):
                    subset=[r for r in tr if (sum(r[m]>=.5 for m in VOTES)>=k)==flag]
                    rates[flag]=(sum(r['y'] for r in subset)+20*prior)/(len(subset)+20)
                for r in test:r['A'+str(k)]=rates[sum(r[m]>=.5 for m in VOTES)>=k]
            for r in test:
                r['B']=float(np.mean([r[m] for m in VOTES]));r['votes']=sum(r[m]>=.5 for m in VOTES);r['pattern']=''.join('1' if r[m]>=.5 else '0' for m in VOTES)
            output+=test
    write('fit-audit.csv',audit);write('weights.csv',weights);write('predictions.csv.gz',output)
    return output

def alert(rs,model):return np.array([r['votes']>=int(model[1:]) if model.startswith('A') else r[model]>=.5 for r in rs],float)

def metric_arrays(y,p,a,w):
    n=w@np.ones(len(y));tp=w@(a*y);fp=w@(a*(1-y));pos=w@y;neg=n-pos
    return dict(brier=ratio(w@((p-y)**2),n),log_loss=ratio(w@logloss(y,p),n),precision=ratio(tp,tp+fp),recall=ratio(tp,pos),false_positive_rate=ratio(fp,neg),warning_frequency=ratio(tp+fp,n),observed_rate=ratio(pos,n),calibration_bias=ratio(w@(p-y),n))

def summarize(rs,context,reps=399):
    rs=sorted(rs,key=lambda r:(r['date'],r['symbol']));lo,hi=min(r['date'] for r in rs),max(r['date'] for r in rs)
    dates=[d for d in CALENDAR if lo<=d<=hi];idx=np.array([dates.index(r['date']) for r in rs]);bc=counts(len(dates),reps);w=np.vstack([np.ones(len(rs)),bc[:,idx]])
    y=np.array([r['y'] for r in rs]);out=[];reliability=[]
    for model in MODELS:
        p=np.array([r[model] for r in rs]);a=alert(rs,model);m=metric_arrays(y,p,a,w)
        row=dict(context,model=model,n=len(rs),positive=int(y.sum()),calendar_dates=len(dates),calendar_blocks40=len(dates)//40)
        for k,v in m.items():row[k]=float(v[0]) if np.isfinite(v[0]) else None;row[k+'_low'],row[k+'_high']=interval(v[1:])
        ece=0.
        for b in range(10):
            mask=(p>=b/10)&((p<(b+1)/10) if b<9 else (p<=1))
            nn=int(mask.sum());rate=float(y[mask].mean()) if nn else None;mean=float(p[mask].mean()) if nn else None
            low,high=interval(ratio(w[1:]@(y*mask),w[1:]@mask.astype(float)))
            if nn:ece+=nn/len(y)*abs(rate-mean)
            reliability.append(dict(context,model=model,bin=b,n=nn,mean_probability=mean,observed_rate=rate,observed_low=low,observed_high=high))
        row['ece_descriptive']=ece;out.append(row)
    return out,reliability

def pooled_boot(rs,L=40,reps=999):
    lo,hi=min(r['date'] for r in rs),max(r['date'] for r in rs);dates=[d for d in CALENDAR if lo<=d<=hi];idx=np.array([dates.index(r['date']) for r in rs]);bc=counts(len(dates),reps,L)
    def mean(values,mask=None):
        mask=np.ones(len(rs)) if mask is None else np.asarray(mask,float);values=np.asarray(values)
        den=bc@np.bincount(idx,weights=mask,minlength=len(dates));num=bc@np.bincount(idx,weights=values*mask,minlength=len(dates));return ratio(num,den)
    return mean,len(dates)

def clusters(rs,mask):
    # De-overlap across ALL three stocks; independence is still not established.
    intervals=sorted((CALENDAR.index(r['date'])+1,CALENDAR.index(r['date'])+r['horizon']) for r,m in zip(rs,mask) if m and r['y'])
    total=0;end=-1
    for a,b in intervals:
        if a>end:total+=1
        end=max(end,b)
    return total

def agreement(rs,context):
    y=np.array([r['y'] for r in rs]);boot,N=pooled_boot(rs);overall=float(y.mean());out=[]
    buckets=[('count',v,np.array([min(r['votes'],3)==v for r in rs])) for v in range(4)]
    buckets += [('pattern',f'{v:05b}',np.array([r['pattern']==f'{v:05b}' for r in rs])) for v in range(32)]
    for typ,val,mask in buckets:
        n=int(mask.sum());ds={r['date'] for r,m in zip(rs,mask) if m};matched=np.array([r['date'] in ds for r in rs]);rate=float(y[mask].mean()) if n else None;base=float(y[matched].mean()) if n else None
        br=boot(y,mask);bm=boot(y,matched);low,high=interval(br);dl,dh=interval(br-bm)
        ol,oh=interval(br-boot(y))
        out.append(dict(context,kind=typ,bucket=val,n=n,event_rate=rate,rate_low=low,rate_high=high,overall_rate=overall,matched_date_rate=base,uplift_matched=rate-base if n else None,uplift_low=dl,uplift_high=dh,uplift_overall=rate-overall if n else None,uplift_overall_low=ol,uplift_overall_high=oh,lift_matched=rate/base if n and base else None,nonoverlap_positive_clusters=clusters(rs,mask),independent_events='UNKNOWN',calendar_blocks40=N//40,selection='EXPLORATORY_POST_SELECTION_FOR_PATTERNS'))
    return out

def holm(ps):
    order=np.argsort(ps);out=np.zeros(len(ps));running=0
    for rank,i in enumerate(order):running=max(running,(len(ps)-rank)*ps[i]);out[i]=min(1,running)
    return out

def evaluate(pred):
    metrics=[];reliability=[];comparisons=[];agree=[];corr=[];added=[]
    for target in ('touch','terminal'):
     for h in (5,10,20):
      for t in (5.,10.,15.):
        context=dict(target=target,horizon=h,threshold_pct=t)
        rs=[r for r in pred if all(r[k]==v for k,v in context.items())];y=np.array([r['y'] for r in rs]);boots={L:pooled_boot(rs,L,PRIMARY_REPS if target=='touch' else 999)[0] for L in (20,40,60)}
        for dimension,values in (('ALL',('ALL',)),('symbol',('AMD','NVDA','MU')),('test_year',(2024,2025,2026)),('regime',('UP','DOWN','MIXED'))):
            for value in values:
                subset=[r for r in rs if dimension=='ALL' or r['market_regime' if dimension=='regime' else dimension]==value]
                if not subset:continue
                ctx=dict(context,dimension=dimension,value=value);m,rel=summarize(subset,ctx);metrics+=m;reliability+=rel
                agree+=agreement(subset,ctx)
        for m in ENSEMBLES:
         for b in BASELINES:
            diff=(np.array([r[m] for r in rs])-y)**2-(np.array([r[b] for r in rs])-y)**2;point=float(diff.mean());row=dict(context,model=m,baseline=b,n=len(rs),delta_brier=point,relative_improvement=-point/np.mean((np.array([r[b] for r in rs])-y)**2),primary=target=='touch')
            for L,boot in boots.items():row[f'low{L}'],row[f'high{L}']=interval(boot(diff))
            boot=boots[40](diff);row['p_one_sided']=(1+int(np.sum(boot-point<=point)))/(len(boot)+1)
            row['stable_stock_year']=all(np.mean([d for r,d in zip(rs,diff) if r[k]==v])<0 for k,vs in [('symbol',('AMD','NVDA','MU')),('test_year',(2024,2025,2026))] for v in vs)
            row['support']=len({r['date'] for r in rs})//40>=10 and min(y.sum(),len(y)-y.sum())>=10
            row['holm_p']=None;row['criteria_pass']=False;comparisons.append(row)
        errors=np.array([[r[m]-r['y'] for m in VOTES] for r in rs]);cc=np.corrcoef(errors.T)
        for i,m in enumerate(VOTES):
            for j,b in enumerate(VOTES):corr.append(dict(context,model=m,other=b,error_correlation=float(cc[i,j]),n=len(rs),interpretation='EXPLORATORY_CORRELATED_RESIDUALS'))
            d=(np.array([r['without_'+m] for r in rs])-y)**2-(np.array([r['C'] for r in rs])-y)**2;low,high=interval(boots[40](d));added.append(dict(context,model=m,delta_brier_without_minus_full=float(d.mean()),low=low,high=high,interpretation='EXPLORATORY_REFIT_ABLATION_POSITIVE_HELPS'))
        print(target,h,t,flush=True)
    primary=[r for r in comparisons if r['primary']]
    for r,p in zip(primary,holm([r['p_one_sided'] for r in primary])):
        r['holm_p']=float(p);r['criteria_pass']=bool(p<.05 and r['relative_improvement']>=.01 and all(r[f'high{L}'] is not None and r[f'high{L}']<0 for L in (20,40,60)) and r['stable_stock_year'] and r['support'])
    write('metrics.csv',metrics);write('reliability.csv',reliability);write('comparisons.csv',comparisons);write('agreement.csv',agree);write('error-correlation.csv',corr);write('added-value.csv',added)
    return comparisons

CALENDAR=[]
if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);args=ap.parse_args();SOURCE=args.source.resolve()
    registration=json.loads((OUT/'protocol-registration.json').read_text());assert hashlib.sha256((OUT/'protocol.md').read_bytes()).hexdigest()==registration['sha256']
    assert hashlib.sha256((OUT/'protocol-numerical-addendum.md').read_bytes()).hexdigest()==registration['addendum_sha256']
    raw=assign_market_regimes(read_forecasts(),SOURCE);CALENDAR=sorted({r['close_at'][:10] for r in csv.DictReader((SOURCE/'data/risk-signal-v3/bars.csv').open()) if r['symbol']=='AMD'})
    pred=make_predictions(raw);comp=evaluate(pred)
    from economics import run
    run(pred,SOURCE,CALENDAR,OUT,write)
    (OUT/'summary.json').write_text(json.dumps(dict(test_rows=len(pred),primary_contrasts=sum(r['primary'] for r in comp),primary_pass=sum(r['criteria_pass'] for r in comp),conclusion='RESEARCH ONLY',independent_holdout=False,verified_PIT=False),indent=2)+'\n')
