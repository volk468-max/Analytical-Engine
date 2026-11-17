"""Frozen PR20 price feature function; raw ridge fit matches original pre-calibration fit."""
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from scipy.special import logit
def feature_frame(df):
    c=df['close'];r=np.log(c).diff();rv20=r.rolling(20).std(ddof=1)*np.sqrt(252);rv60=r.rolling(60).std(ddof=1)*np.sqrt(252)
    return pd.DataFrame(dict(r20=c/c.shift(20)-1,r60=c/c.shift(60)-1,ma50=c/c.rolling(50).mean()-1,ma200=c/c.rolling(200).mean()-1,rv20=rv20,vol_ratio=rv20/rv60,drawdown=c/c.cummax()-1,warm=c.rolling(252).count()==252))

def fit_raw(X,y):
    mu=X.mean(axis=0);scale=X.std(axis=0);scale[scale<1e-12]=1
    if len(np.unique(y))<2:coef=np.zeros(X.shape[1]);inter=float(logit((y.sum()+1)/(len(y)+2)));status='CONSTANT_CLASS_BETA_BACKOFF'
    else:
        m=LogisticRegression(C=.1,max_iter=2000,tol=1e-9).fit((X-mu)/scale,y)
        if m.n_iter_[0]>=2000:raise ValueError('MDP_FIT_DID_NOT_CONVERGE')
        coef=m.coef_[0];inter=float(m.intercept_[0]);status='CONVERGED'
    return dict(mean=mu.tolist(),scale=scale.tolist(),coef=coef.tolist(),intercept=inter,status=status)
