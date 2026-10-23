"""Synchronous calendar-block uncertainty for dependent forecast windows."""
import numpy as np


def block_counts(n,resamples=399,length=40,seed=731):
    if min(n,resamples,length)<1:raise ValueError('Positive block dimensions required')
    rng=np.random.default_rng(seed)
    starts=rng.integers(0,n,size=(resamples,(n+length-1)//length))
    selected=(starts[:,:,None]+np.arange(length))%n
    selected=selected.reshape(resamples,-1)[:,:n]
    counts=np.zeros((resamples,n),dtype=np.int16)
    np.add.at(counts,(np.arange(resamples)[:,None],selected),1)
    return counts


def ci(values):
    values=np.asarray(values,float)
    finite=values[np.isfinite(values)]
    if len(finite)<max(20,.8*len(values)):return None,None
    return tuple(float(x) for x in np.quantile(finite,(.025,.975)))


def metric_samples(y,p,weights):
    """One row per resample, including an all-ones row for point metrics."""
    y=np.asarray(y,float);p=np.asarray(p,float);w=np.asarray(weights,float)
    if len(y)!=len(p) or w.shape[1]!=len(y) or np.any((p<0)|(p>1)) or np.any(~np.isfinite(p)):
        raise ValueError('Invalid probability/weight arrays')
    if np.any((y!=0)&(y!=1)) or np.any(w<0):raise ValueError('Invalid outcomes/weights')
    n=w.sum(axis=1);safe=np.where(n>0,n,np.nan)
    clipped=np.clip(p,1e-6,1-1e-6)
    out=dict(frequency=w@y/safe,brier=w@((p-y)**2)/safe,
        log_loss=w@(-y*np.log(clipped)-(1-y)*np.log1p(-clipped))/safe)
    order=np.argsort(-p,kind='stable');ys=y[order];ps=p[order]
    starts=np.r_[0,np.flatnonzero(np.diff(ps)!=0)+1]
    ws=w[:,order]
    pos=np.add.reduceat(ws*ys,starts,axis=1)
    neg=np.add.reduceat(ws*(1-ys),starts,axis=1)
    tp=np.cumsum(pos,axis=1);fp=np.cumsum(neg,axis=1)
    P=tp[:,-1];N=fp[:,-1];applicable=(P>0)&(N>0)
    with np.errstate(divide='ignore',invalid='ignore'):
        auc=(neg*(tp-pos/2)).sum(axis=1)/(P*N)
        ap=(pos/P[:,None]*np.divide(tp,tp+fp,out=np.zeros_like(tp),where=(tp+fp)>0)).sum(axis=1)
    out['roc_auc']=np.where(applicable,auc,np.nan)
    out['pr_auc_ap']=np.where(applicable,ap,np.nan)
    return out


def effective_n(y,date_indices,n_dates,lag=40):
    y=np.asarray(y,float);idx=np.asarray(date_indices,int)
    totals=np.bincount(idx,weights=y,minlength=n_dates)
    counts=np.bincount(idx,minlength=n_dates)
    if np.any(counts==0):return None  # never pretend irregular conditional dates are adjacent
    daily=totals/counts
    centered=daily-daily.mean();N=len(daily)
    gamma=float(centered@centered/N)
    if gamma==0:return None
    longrun=gamma
    for k in range(1,min(lag,N-1)+1):
        longrun+=2*(1-k/(lag+1))*float(centered[k:]@centered[:-k]/N)
    return float(min(N,max(1,N*gamma/max(longrun,1e-12))))


def paired_difference(y,p,q,date_indices,n_dates,counts):
    """Negative difference favors p; all symbols share the same sampled dates."""
    y=np.asarray(y,float);p=np.asarray(p,float);q=np.asarray(q,float)
    idx=np.asarray(date_indices,int)
    n=np.bincount(idx,minlength=n_dates)
    denominator=counts@n
    output={}
    for metric in ('brier','log_loss'):
        if metric=='brier':d=(p-y)**2-(q-y)**2
        else:
            a=np.clip(p,1e-6,1-1e-6);b=np.clip(q,1e-6,1-1e-6)
            d=-y*np.log(a)-(1-y)*np.log1p(-a)+y*np.log(b)+(1-y)*np.log1p(-b)
        sums=np.bincount(idx,weights=d,minlength=n_dates)
        boot=np.divide(counts@sums,denominator,out=np.full(len(counts),np.nan),where=denominator>0)
        point=float(d.mean());low,high=ci(boot)
        output.update({metric+'_difference':point,metric+'_difference_low':low,metric+'_difference_high':high})
        if metric=='brier':
            centered=boot-point
            output['brier_p_one_sided']=(1+int(np.sum(centered<=point)))/(len(boot)+1)
    return output


def holm(pvalues):
    values=np.asarray(pvalues,float);order=np.argsort(values)
    output=np.empty(len(values));running=0
    for rank,index in enumerate(order):
        running=max(running,(len(values)-rank)*values[index])
        output[index]=min(1,running)
    return output.tolist()


def score_slope(score,y,weights):
    score=np.asarray(score,float);y=np.asarray(y,float);w=np.asarray(weights,float)
    n=w.sum(axis=1);x=w@score/n;out=w@y/n
    covariance=w@(score*y)/n-x*out
    variance=w@(score*score)/n-x*x
    return np.divide(covariance,variance,out=np.full(len(w),np.nan),where=variance>1e-12)
