"""Synchronous date-block inference, distinct market and stock comparisons."""
import numpy as np
from common import *

PRIMARY_REPS=9999

def ratio(a,b):
    a,b=np.broadcast_arrays(np.asarray(a,float),np.asarray(b,float));return np.divide(a,b,out=np.full(a.shape,np.nan),where=b>0)
def ci(a):
    v=np.asarray(a);v=v[np.isfinite(v)]
    return tuple(map(float,np.quantile(v,[.025,.975]))) if len(v)>=max(20,.8*len(a)) else (None,None)
def holm(p):
    order=np.argsort(p);out=np.zeros(len(p));running=0.
    for rank,i in enumerate(order):running=max(running,(len(p)-rank)*p[i]);out[i]=min(1.,running)
    return out

def bootstrap_daily(numerator,denominator,reps=399,length=40):
    """Columns retain every instrument/contrast together on each sampled date."""
    num=np.asarray(numerator,float);den=np.asarray(denominator,float)
    if num.ndim==1:num=num[:,None]
    if den.ndim==1:den=den[:,None]
    N=len(num);rng=np.random.default_rng(19319);result=[]
    for first in range(0,reps,256):
        batch=min(256,reps-first);starts=rng.integers(0,N,(batch,(N+length-1)//length));idx=((starts[:,:,None]+np.arange(length))%N).reshape(batch,-1)[:,:N]
        weights=np.zeros((batch,N),dtype=np.int16);np.add.at(weights,(np.arange(batch)[:,None],idx),1)
        result.append(ratio(weights@num,weights@den))
    return np.vstack(result)

def daily_sum(x,idx,n):
    x=np.asarray(x,float)
    if x.ndim==1:x=x[:,None]
    out=np.zeros((n,x.shape[1]));np.add.at(out,idx,x);return out

def effective_n(y,idx,n,lag):
    count=np.bincount(idx,minlength=n)
    if np.any(count==0):return None
    z=np.bincount(idx,weights=y,minlength=n)/count;z-=z.mean();g=float(z@z/n)
    if not g:return None
    lr=g+2*sum((1-k/(lag+1))*float(z[k:]@z[:-k]/n) for k in range(1,min(lag,n-1)+1))
    return min(n,max(1.,n*g/max(lr,1e-12)))

def group_metrics(rs,dates,ctx,model_names=None):
    names=model_names or ('HIST','REGIME','VOL','SIMPLE','PLUS_M','PLUS_S','MINIMAL')+(('PLUS_X',) if rs[0]['population']=='STOCK' else ())
    lo=min(r['date'] for r in rs);hi=max(r['date'] for r in rs);ds=[d for d in dates if lo<=d<=hi];di={d:i for i,d in enumerate(ds)};idx=np.array([di[r['date']] for r in rs]);n=len(ds)
    y=np.array([r['y'] for r in rs]);p=np.array([[r[m] for m in names] for r in rs]);pr=np.array([[r[m+'_raw'] for m in names] for r in rs]);cl=np.clip(p,1e-6,1-1e-6);yy=y[:,None];ones=np.ones((len(rs),1));parts=[(p-yy)**2,-yy*np.log(cl)-(1-yy)*np.log1p(-cl),p-yy]
    for cut in (.2,.5):
        a=(p>=cut).astype(float);parts += [a*yy,a*(1-yy),a]
    parts+=[(pr-yy)**2];values=np.hstack(parts+[yy,ones]);sums=daily_sum(values,idx,n);boot=bootstrap_daily(sums,np.bincount(idx,minlength=n),399,max(40,int(ctx['horizon'])));point=values.mean(axis=0);M=len(names);out=[];rel=[]
    for i,m in enumerate(names):
        for cut,offset in ((.2,3*M),(.5,6*M)):
            tp=point[offset+i];fp=point[offset+M+i];warn=point[offset+2*M+i];freq=float(y.mean());btp=boot[:,offset+i];bfp=boot[:,offset+M+i];bw=boot[:,offset+2*M+i];bf=boot[:,-2]
            quantities={'brier':(point[i],boot[:,i]),'log_loss':(point[M+i],boot[:,M+i]),'calibration_bias':(point[2*M+i],boot[:,2*M+i]),'precision':(ratio(tp,tp+fp),ratio(btp,btp+bfp)),'recall':(ratio(tp,freq),ratio(btp,bf)),'false_positive_rate':(ratio(fp,1-freq),ratio(bfp,1-bf)),'warning_frequency':(warn,bw),'base_rate':(freq,bf),'base_rate_lift':(ratio(ratio(tp,warn),freq),ratio(ratio(btp,bw),bf))}
            row=dict(ctx,model=m,operating_threshold=cut,n=len(rs),positive=int(y.sum()),calendar_dates=n,calendar_blocks40=n//40,effective_n_HAC=effective_n(y,idx,n,max(40,int(ctx['horizon']))),independent_events='UNKNOWN',raw_brier=point[9*M+i])
            for key,(a,b) in quantities.items():row[key]=float(a) if np.isfinite(a) else None;row[key+'_low'],row[key+'_high']=ci(b)
            out.append(row)
        ece=0.
        for b in range(10):
            mask=(p[:,i]>=b/10)&((p[:,i]<(b+1)/10) if b<9 else (p[:,i]<=1));count=int(mask.sum());rate=float(y[mask].mean()) if count else None;mean=float(p[mask,i].mean()) if count else None
            # Descriptive bins; no invented narrow IID intervals.
            if count:ece+=count/len(y)*abs(mean-rate)
            rel.append(dict(ctx,model=m,bin=b,n=count,mean_probability=mean,observed_rate=rate,interval='POINTWISE_MODEL_METRICS_ONLY_BIN_DESCRIPTIVE'))
        out[-1]['ece_descriptive']=ece;out[-2]['ece_descriptive']=ece
    return out,rel

def pairs(population):
    candidates=('PLUS_M','PLUS_S','MINIMAL')+(('PLUS_X',) if population=='STOCK' else ())
    result=[(m,b) for m in candidates for b in ('HIST','VOL','REGIME','SIMPLE')]
    if population=='STOCK':result.append(('PLUS_X','MINIMAL'))
    return result

def primary_pair(pop,m,b):
    return ((pop=='MARKET' and ((m in ('PLUS_M','PLUS_S') and b=='SIMPLE') or (m=='MINIMAL' and b in ('SIMPLE','HIST','VOL','REGIME')))) or (pop=='STOCK' and m=='PLUS_X' and b in ('MINIMAL','HIST','VOL','REGIME','SIMPLE')))

def evaluate(pred,dates):
    metrics=[];reliability=[];comparisons=[]
    for target in ('TOUCH','TERMINAL'):
     for threshold,horizon in TASKS:
        task=[r for r in pred if r['target']==target and r['threshold_pct']==threshold and r['horizon']==horizon];cases=[]
        for symbol in SYMBOLS:
            rs=[r for r in task if r['symbol']==symbol]
            if not rs:continue
            ctx=dict(symbol=symbol,population=rs[0]['population'],target=target,threshold_pct=threshold,horizon=horizon)
            groups=[('ALL','ALL',rs)]
            for dim in ('test_year','market_regime','era'):
                groups += [(dim,str(v),[r for r in rs if r[dim]==v]) for v in sorted({r[dim] for r in rs})]
            near=[r for r in rs if r['near_high']]
            if near:groups.append(('near_high','DD>=-2%',near))
            for dim,val,sub in groups:
                m,rel=group_metrics(sub,dates,dict(ctx,dimension=dim,value=val));metrics+=m;reliability+=rel
            y=np.array([r['y'] for r in rs]);Ndates=sum(min(r['date'] for r in rs)<=d<=max(r['date'] for r in rs) for d in dates)
            for model,base in pairs(ctx['population']):
                p=np.array([r[model] for r in rs]);q=np.array([r[base] for r in rs]);diff=(p-y)**2-(q-y)**2;pc=np.clip(p,1e-6,1-1e-6);qc=np.clip(q,1e-6,1-1e-6);lld=-y*np.log(pc)-(1-y)*np.log1p(-pc)+y*np.log(qc)+(1-y)*np.log1p(-qc)
                primary=target=='TOUCH' and threshold==5 and horizon==10 and primary_pair(ctx['population'],model,base)
                yearly=[]
                for year in sorted({r['test_year'] for r in rs}):
                    mask=np.array([r['test_year']==year for r in rs]);yy=y[mask]
                    if mask.sum()>=60 and min(yy.sum(),len(yy)-yy.sum())>=10:yearly.append(float(diff[mask].mean()))
                row=dict(ctx,model=model,baseline=base,n=len(rs),delta_brier=float(diff.mean()),relative_brier_improvement=float(-diff.mean()/np.mean((q-y)**2)),delta_log_loss=float(lld.mean()),primary=primary,holm_p=None,support=Ndates//40>=10 and min(y.sum(),len(y)-y.sum())>=10,eligible_years=len(yearly),stable_years=len(yearly)>=2 and all(d<0 for d in yearly),criteria_pass=False,p_one_sided=None,low20=None,high20=None,low40=None,high40=None,low60=None,high60=None,delta_log_loss_low=None,delta_log_loss_high=None)
                cases.append((row,rs,diff,lld))
        for is_primary in (True,False):
            selected=[c for c in cases if c[0]['primary']==is_primary]
            if not selected:continue
            lo=min(r['date'] for c,rs,d,l in selected for r in rs);hi=max(r['date'] for c,rs,d,l in selected for r in rs);ds=[d for d in dates if lo<=d<=hi];di={d:i for i,d in enumerate(ds)};num=np.zeros((len(ds),len(selected)*2));den=np.zeros_like(num)
            for j,(row,rs,d,ll) in enumerate(selected):
                idx=np.array([di[r['date']] for r in rs]);np.add.at(num[:,j],idx,d);np.add.at(num[:,j+len(selected)],idx,ll);np.add.at(den[:,j],idx,1);np.add.at(den[:,j+len(selected)],idx,1)
            for length in ((20,40,60) if is_primary else (max(40,horizon),)):
                boot=bootstrap_daily(num,den,PRIMARY_REPS if is_primary else 999,length)
                for j,(row,rs,d,ll) in enumerate(selected):
                    key=length if is_primary else 40;row[f'low{key}'],row[f'high{key}']=ci(boot[:,j])
                    if length==(40 if is_primary else max(40,horizon)):
                        row['p_one_sided']=(1+int(np.sum(boot[:,j]-row['delta_brier']<=row['delta_brier'])))/(len(boot)+1);row['delta_log_loss_low'],row['delta_log_loss_high']=ci(boot[:,j+len(selected)])
            comparisons += [c[0] for c in selected]
        print('evaluated',target,threshold,horizon,flush=True)
    primary=[r for r in comparisons if r['primary']]
    # Missing tests remain in the preregistered family as p=1.
    assert len(primary)<=33
    adjusted=holm([r['p_one_sided'] for r in primary]+[1.]*(33-len(primary)))
    for row,p in zip(primary,adjusted):
        row['holm_p']=float(p);row['criteria_pass']=bool(p<.05 and row['relative_brier_improvement']>=.01 and all(row[f'high{k}'] is not None and row[f'high{k}']<0 for k in (20,40,60)) and row['support'] and row['stable_years'] and row['delta_log_loss']<=0)
    write('metrics.csv.gz',metrics);write('reliability.csv.gz',reliability);write('predictive-evaluation.csv',comparisons)
    (OUT/'predictive-summary.json').write_text(json.dumps(dict(primary_family=33,testable_primary=len(primary),primary_pass=sum(r['criteria_pass'] for r in primary),conclusion='RESEARCH-ONLY',PIT_core_gate='NO-GO',independent_holdout=False),indent=2)+'\n')

def prevalence(rows,dates):
    result=[]
    for symbol in SYMBOLS:
     for target in ('TOUCH','TERMINAL'):
      for threshold,horizon in TASKS:
        task=[r for r in rows if r['symbol']==symbol and r['target']==target and r['threshold_pct']==threshold and r['horizon']==horizon]
        if not task:continue
        flags=M_FLAGS+(X_FLAGS if symbol in STOCK else ())
        for dim,val,rs in [('ALL','ALL',task)]+[('market_regime',reg,[r for r in task if r['market_regime']==reg]) for reg in ('UP','DOWN','MIXED')]:
            if not rs:continue
            lo=min(r['date'] for r in rs);hi=max(r['date'] for r in rs);ds=[d for d in dates if lo<=d<=hi];di={d:i for i,d in enumerate(ds)};idx=np.array([di[r['date']] for r in rs]);y=np.array([r['y'] for r in rs]);f=np.array([[r[k] for k in flags] for r in rs],float);yy=y[:,None]
            values=np.hstack([f,yy*f,yy,np.ones((len(rs),1))]);points=values.sum(axis=0);boot=bootstrap_daily(daily_sum(values,idx,len(ds)),np.ones(len(ds)),399,max(40,horizon));F=len(flags)
            for j,flag in enumerate(flags):
                exp=points[j];tp=points[F+j];pos=points[-2];N=len(rs);bexp=boot[:,j];btp=boot[:,F+j];bpos=boot[:,-2];bn=boot[:,-1]
                quantities={'P_feature_given_crash':(ratio(tp,pos),ratio(btp,bpos)),'P_feature_given_no_crash':(ratio(exp-tp,N-pos),ratio(bexp-btp,bn-bpos)),'P_crash_given_feature':(ratio(tp,exp),ratio(btp,bexp)),'base_rate':(pos/N,ratio(bpos,bn)),'false_alarm_fraction':(ratio(exp-tp,exp),ratio(bexp-btp,bexp)),'recall':(ratio(tp,pos),ratio(btp,bpos)),'lift':(ratio(ratio(tp,exp),pos/N),ratio(ratio(btp,bexp),ratio(bpos,bn)))}
                row=dict(symbol=symbol,population='MARKET' if symbol in MARKET else 'STOCK',target=target,threshold_pct=threshold,horizon=horizon,dimension=dim,value=val,flag=flag,n=N,positive=int(pos),exposed=int(exp),true_positive=int(tp),calendar_dates=len(ds),effective_n_HAC=effective_n(y,idx,len(ds),max(40,horizon)),independent_events='UNKNOWN',inference='EXPLORATORY_ALL_ELIGIBLE_DATES_NOT_MATCHED_CASE_SAMPLE')
                for key,(p,b) in quantities.items():row[key]=float(p) if np.isfinite(p) else None;row[key+'_low'],row[key+'_high']=ci(b)
                result.append(row)
    write('factor-prevalence.csv',result)
