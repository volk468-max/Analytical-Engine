"""Prespecified annual train/cal/test price-only probability evaluation."""
import argparse,json
import numpy as np
from scipy.special import expit,logit
from scipy.optimize import minimize_scalar
from sklearn.linear_model import LogisticRegression
from common import *

def loss(y,p):
    p=np.clip(p,1e-6,1-1e-6);return -y*np.log(p)-(1-y)*np.log1p(-p)

def fit_logit(X,y,Z,cy):
    mu=X.mean(axis=0);scale=X.std(axis=0);scale[scale<1e-12]=1
    if len(np.unique(y))<2:coef=np.zeros(X.shape[1]);inter=float(logit((y.sum()+1)/(len(y)+2)));status='CONSTANT_CLASS_BETA_BACKOFF'
    else:
        m=LogisticRegression(C=.1,max_iter=2000,tol=1e-9).fit((X-mu)/scale,y)
        if m.n_iter_[0]>=2000:raise ValueError('nonconverged training fit')
        coef=m.coef_[0];inter=float(m.intercept_[0]);status='CONVERGED'
    eta=(Z-mu)/scale@coef+inter
    res=minimize_scalar(lambda a:float(loss(cy,expit(eta+a)).sum()+.5*a*a),bounds=(-15,15),method='bounded',options={'xatol':1e-10})
    if not res.success:raise ValueError('nonconverged intercept calibration')
    return dict(mean=mu,scale=scale,coef=coef,intercept=inter,calibration_shift=float(res.x),status=status)

def predict(X,fit):
    z=(X-fit['mean'])/fit['scale']@fit['coef']+fit['intercept'];return expit(z),expit(z+fit['calibration_shift'])

def split_rows(rows,year,dates,horizon):
    purge=max(20,horizon);train_bound=next(i for i,d in enumerate(dates) if d>=f'{year-1}-01-01');test_bound=next(i for i,d in enumerate(dates) if d>=f'{year}-01-01');cutoff=f'{year-1}-01-01T00:00:00+00:00';cal_cut=dates[test_bound-purge]+'T00:00:00+00:00'
    tr=[r for r in rows if r['calendar_index']<train_bound-purge and r['label_available_at']<=cutoff]
    cal=[r for r in rows if int(r['date'][:4])==year-1 and r['calendar_index']>=train_bound+purge and r['label_available_at']<=cal_cut]
    test=[r for r in rows if int(r['date'][:4])==year and r['calendar_index']>=test_bound+purge]
    return tr,cal,test,cutoff,cal_cut

def task_rows(symbol,df,panel,threshold,horizon,target):
    values=df['low'][::-1].rolling(horizon).min()[::-1].shift(-1) if target=='TOUCH' else df['close'].shift(-horizon)
    maturity=df['available_at'].shift(-horizon);out=[]
    for r in panel:
        d=r['date']
        if pd.isna(maturity.loc[d]):continue
        y=float(values.loc[d]<=df.loc[d,'close']*(1-threshold/100)+df.loc[d,'close']*1e-12)
        out.append(dict(r,target=target,threshold_pct=threshold,horizon=horizon,y=y,label_available_at=maturity.loc[d],era=era(d)))
    return out

def run():
    bars,dates,calendar=load_bars();panel=build_panel(bars,dates)
    from anatomy import run as anatomy
    catalogue,clusters=anatomy(bars,dates,panel)
    outputs=[];audits=[];weights=[];censor=[];prevalence_inputs=[];caldiagnostics=[]
    first_test=2010 if min(df.index[0] for df in bars.values())<'2001-01-01' else 2024
    for symbol in SYMBOLS:
      symbol_out=[]
      models=('HIST','REGIME','VOL','SIMPLE','PLUS_M','PLUS_S','MINIMAL')+(('PLUS_X',) if symbol in STOCK else ())
      for target in ('TOUCH','TERMINAL'):
       for threshold,horizon in TASKS:
        rows=task_rows(symbol,bars[symbol],panel[symbol],threshold,horizon,target);prevalence_inputs+=rows
        censor.append(dict(symbol=symbol,target=target,threshold_pct=threshold,horizon=horizon,feature_eligible=len(panel[symbol]),mature_labels=len(rows),censored=len(panel[symbol])-len(rows),earliest_feature=panel[symbol][0]['date'],last_feature=panel[symbol][-1]['date']))
        for year in range(first_test,2027):
            tr,cal,test,cutoff,cal_cut=split_rows(rows,year,dates,horizon);ctx=dict(symbol=symbol,population='MARKET' if symbol in MARKET else 'STOCK',target=target,threshold_pct=threshold,horizon=horizon,test_year=year)
            if len(tr)<200 or len(cal)<60 or not test:
                audits.append(dict(ctx,status='NO_FIT',training_n=len(tr),calibration_n=len(cal),test_n=len(test),training_cutoff=cutoff,last_training_anchor=None,last_training_maturity=None,calibration_first=None,calibration_last_maturity=None,calibration_cutoff=cal_cut,test_first=None,purge=max(20,horizon)));continue
            assert max(r['label_available_at'] for r in tr)<=cutoff;assert max(r['decision_at'] for r in tr)<min(r['decision_at'] for r in cal);assert max(r['label_available_at'] for r in cal)<min(r['decision_at'] for r in test)
            audits.append(dict(ctx,status='FIT',training_n=len(tr),calibration_n=len(cal),test_n=len(test),training_cutoff=cutoff,last_training_anchor=max(r['date'] for r in tr),last_training_maturity=max(r['label_available_at'] for r in tr),calibration_first=min(r['decision_at'] for r in cal),calibration_last_maturity=max(r['label_available_at'] for r in cal),calibration_cutoff=cal_cut,test_first=min(r['decision_at'] for r in test),purge=max(20,horizon)))
            y=np.array([r['y'] for r in tr]);cy=np.array([r['y'] for r in cal]);hist=float((y.sum()+1)/(len(y)+2));pred={m:None for m in models};raw={m:None for m in models}
            pred['HIST']=raw['HIST']=np.full(len(test),hist)
            regime_rates={reg:(sum(r['y'] for r in tr if r['market_regime']==reg)+20*hist)/(sum(r['market_regime']==reg for r in tr)+20) for reg in ('UP','DOWN','MIXED')}
            pred['REGIME']=raw['REGIME']=np.array([regime_rates[r['market_regime']] for r in test])
            for model in models:
                if model in ('HIST','REGIME'):continue
                keys=MODEL_KEYS[model];X=np.array([[r[k] for k in keys] for r in tr]);Z=np.array([[r[k] for k in keys] for r in cal]);T=np.array([[r[k] for k in keys] for r in test]);fit=fit_logit(X,y,Z,cy);raw[model],pred[model]=predict(T,fit);cr,cp=predict(Z,fit)
                weights.append(dict(ctx,model=model,status=fit['status'],keys=json.dumps(keys),means=json.dumps(fit['mean'].tolist()),scales=json.dumps(fit['scale'].tolist()),coefficients=json.dumps(fit['coef'].tolist()),intercept=fit['intercept'],calibration_shift=fit['calibration_shift'],ridge_C=.1))
                caldiagnostics.append(dict(ctx,model=model,calibration_n=len(cal),raw_brier=float(np.mean((cr-cy)**2)),calibrated_brier=float(np.mean((cp-cy)**2)),used_to_fit_intercept=True,used_to_fit_slopes=False))
            for i,r in enumerate(test):
                item={k:r[k] for k in ('symbol','population','date','decision_at','calendar_index','market_regime','near_high','era','target','threshold_pct','horizon','y','label_available_at')};item['test_year']=year
                for flag in M_FLAGS+X_FLAGS:item[flag]=r[flag]
                for model in models:item[model]=float(pred[model][i]);item[model+'_raw']=float(raw[model][i])
                # Common schema across populations, PLUS_X is undefined for MARKET.
                if symbol in MARKET:item['PLUS_X']=None;item['PLUS_X_raw']=None
                symbol_out.append(item)
        print('forecast',symbol,target,threshold,horizon,flush=True)
      write('forecasts-'+symbol+'.csv.gz',symbol_out);outputs+=symbol_out
    write('fit-audit.csv',audits);write('weights.csv.gz',weights);write('censoring.csv',censor);write('calibration-period.csv',caldiagnostics)
    from evaluate import evaluate,prevalence
    evaluate(outputs,dates);prevalence(prevalence_inputs,dates)
    (OUT/'run-summary.json').write_text(json.dumps(dict(forecast_rows=len(outputs),market_episode_count=len(catalogue),market_overlap_clusters=clusters,independent_events='UNKNOWN',first_test_year=first_test,PIT_certified=False,untouched_holdout=False),indent=2)+'\n')

if __name__=='__main__':run()
