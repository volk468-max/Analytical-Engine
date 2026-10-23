"""Fixed-ridge chronological probability baselines; no trade policy or signal edits."""
import numpy as np
from aae.backtest.simulator import utc

MODELS=('historical','volatility','drawdown','relative','v3','joint','joint_H1','joint_H2','joint_H3','joint_H5')


def predictors(row,model):
    values={'volatility':[row.get('rv20')],'drawdown':[row.get('current_drawdown60')],
        'relative':[row.get('relative_qqq20'),row.get('relative_sox20')]}
    state=row.get('v3_state')
    values['v3']=[float(state==s) for s in ('WATCH','REDUCE','CRITICAL')] if state in ('HOLD','WATCH','REDUCE','CRITICAL') else [None]*3
    joint=values['volatility']+values['drawdown']+values['relative']+values['v3']
    values['joint']=joint
    for h in ('H1','H2','H3','H5'):values['joint_'+h]=joint+[float(row[h]) if row.get(h) is not None else None]
    result=values.get(model,[])
    return result if all(x is not None and np.isfinite(x) for x in result) else None


class RidgeLogit:
    def __init__(self,ridge=1):
        if ridge<=0:raise ValueError('Positive ridge required')
        self.ridge=ridge;self.fitted=False

    @staticmethod
    def sigmoid(z):return 1/(1+np.exp(-np.clip(z,-40,40)))

    def fit(self,x,y):
        if self.fitted:raise ValueError('Model already frozen')
        self.fitted=True;x=np.asarray(x,float);y=np.asarray(y,float)
        if x.ndim!=2 or len(x)!=len(y) or len(y)==0 or not np.all(np.isfinite(x)) or not np.all((y==0)|(y==1)):
            raise ValueError('Invalid training matrices')
        self.mean=x.mean(axis=0);self.scale=x.std(axis=0);self.scale=np.where(self.scale>1e-10,self.scale,1)
        X=np.column_stack([np.ones(len(x)),(x-self.mean)/self.scale]);self.beta=np.zeros(X.shape[1])
        self.beta[0]=np.log((y.sum()+1)/(len(y)-y.sum()+1));self.converged=False
        penalty=np.r_[0,np.full(X.shape[1]-1,self.ridge)]
        def objective(beta):
            z=X@beta
            return float(np.logaddexp(0,z).sum()-y@z+.5*np.dot(penalty*beta,beta))
        for iteration in range(60):
            p=self.sigmoid(X@self.beta);gradient=X.T@(p-y)+penalty*self.beta
            hessian=(X.T*np.maximum(p*(1-p),1e-8))@X+np.diag(penalty)
            step=np.linalg.solve(hessian,gradient);loss=objective(self.beta);multiplier=1
            while multiplier>1/1024 and objective(self.beta-multiplier*step)>loss:multiplier/=2
            self.beta-=multiplier*step
            if np.max(np.abs(multiplier*step))<1e-7:self.converged=True;break
        self.iterations=iteration+1
        return self

    def predict(self,x):
        x=np.asarray(x,float)
        return self.sigmoid(np.column_stack([np.ones(len(x)),(x-self.mean)/self.scale])@self.beta)


def fit_predict(train,test,model,cutoff):
    cutoff=utc(cutoff)
    if any(r.get('target') is not None and r.get('label_available_at') and utc(r['label_available_at'])<=utc(r['decision_at']) for r in train):
        raise ValueError('Outcome publication must follow its anchor')
    eligible=[r for r in train if r.get('target') is not None and r.get('label_available_at') and utc(r['label_available_at'])<=cutoff and utc(r['decision_at'])<cutoff and predictors(r,model) is not None]
    audit=dict(model=model,training_n=len(eligible),training_positive=sum(r['target'] for r in eligible),
        cutoff=cutoff.isoformat(),last_horizon_available=max((r['label_available_at'] for r in eligible),default=None),
        last_anchor=max((r['decision_at'] for r in eligible),default=None),converged=None)
    if not eligible:return [None]*len(test),audit
    if model=='historical':return [(sum(r['target'] for r in eligible)+1)/(len(eligible)+2)]*len(test),audit
    if min(sum(r['target'] for r in eligible),sum(not r['target'] for r in eligible))==0:
        audit.update(converged=True,status='SINGLE_CLASS_SMOOTHED_BACKOFF')
        return [(sum(r['target'] for r in eligible)+1)/(len(eligible)+2)]*len(test),audit
    estimator=RidgeLogit().fit([predictors(r,model) for r in eligible],[r['target'] for r in eligible])
    audit.update(converged=estimator.converged,iterations=estimator.iterations)
    output=[None]*len(test);valid=[i for i,r in enumerate(test) if predictors(r,model) is not None]
    if not valid:return output,audit
    for index,p in zip(valid,estimator.predict([predictors(test[i],model) for i in valid])):output[index]=float(p)
    return output,audit
