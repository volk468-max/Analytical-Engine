"""Preregistered secondary pure-market comparator for individual stock targets."""
from common import *
from study import task_rows,split_rows,fit_logit,predict,loss
from evaluate import group_metrics,bootstrap_daily,ci,holm

def run():
    reg=json.loads((OUT/'protocol-registration.json').read_text());assert hashlib.sha256((OUT/'protocol-market-baseline-addendum.md').read_bytes()).hexdigest()==reg['market_baseline_addendum_sha256']
    bars,dates,calendar=load_bars();panel=build_panel(bars,dates);keys=('qqq_log_rv20',)+BASE_KEYS[1:]+M_KEYS+S_KEYS
    output=[];weights=[];metrics=[];reliability=[];cases=[]
    for symbol in STOCK:
        old=[r for r in read('forecasts-'+symbol+'.csv.gz') if r['target']=='TOUCH' and r['threshold_pct']=='5' and r['horizon']=='10'];bydate={r['date']:r for r in old};rs=task_rows(symbol,bars[symbol],panel[symbol],5,10,'TOUCH');pred=[]
        for year in sorted({int(r['test_year']) for r in old}):
            tr,cal,test,cut,calcut=split_rows(rs,year,dates,10);X=np.array([[r[k] for k in keys] for r in tr]);Z=np.array([[r[k] for k in keys] for r in cal]);T=np.array([[r[k] for k in keys] for r in test]);fit=fit_logit(X,np.array([r['y'] for r in tr]),Z,np.array([r['y'] for r in cal]));raw,p=predict(T,fit)
            weights.append(dict(symbol=symbol,test_year=year,keys=json.dumps(keys),means=json.dumps(fit['mean'].tolist()),scales=json.dumps(fit['scale'].tolist()),coefficients=json.dumps(fit['coef'].tolist()),intercept=fit['intercept'],calibration_shift=fit['calibration_shift'],training_n=len(tr),calibration_n=len(cal),test_n=len(test)))
            for i,r in enumerate(test):
                src=bydate[r['date']];assert float(src['y'])==r['y'];r=dict(r,test_year=year,MARKET_ONLY=float(p[i]),MARKET_ONLY_raw=float(raw[i]),PLUS_X=float(src['PLUS_X']),PLUS_X_raw=float(src['PLUS_X_raw']));pred.append(r)
        write('market-only-forecasts-'+symbol+'.csv.gz',[{k:r[k] for k in ('symbol','date','decision_at','test_year','target','threshold_pct','horizon','y','label_available_at','MARKET_ONLY','MARKET_ONLY_raw','PLUS_X','PLUS_X_raw')} for r in pred]);output+=pred
        context=dict(symbol=symbol,population='STOCK',target='TOUCH',threshold_pct=5,horizon=10)
        groups=[('ALL','ALL',pred)]+[('market_regime',reg,[r for r in pred if r['market_regime']==reg]) for reg in ('UP','DOWN','MIXED')]
        for dim,val,sub in groups:
            if sub:
                m,rel=group_metrics(sub,dates,dict(context,dimension=dim,value=val),('MARKET_ONLY','PLUS_X'));metrics+=m;reliability+=rel
        y=np.array([r['y'] for r in pred]);p=np.array([r['PLUS_X'] for r in pred]);q=np.array([r['MARKET_ONLY'] for r in pred]);d=(p-y)**2-(q-y)**2;ll=loss(y,p)-loss(y,q);cases.append((dict(context,model='PLUS_X',baseline='MARKET_ONLY',n=len(pred),delta_brier=float(d.mean()),delta_log_loss=float(ll.mean()),inference='SECONDARY_EXPLORATORY_ADDENDUM_HOLM3'),pred,d,ll))
    lo=min(r['date'] for row,rs,d,ll in cases for r in rs);hi=max(r['date'] for row,rs,d,ll in cases for r in rs);ds=[d for d in dates if lo<=d<=hi];di={d:i for i,d in enumerate(ds)};num=np.zeros((len(ds),6));den=np.zeros_like(num)
    for j,(row,rs,d,ll) in enumerate(cases):
        idx=[di[r['date']] for r in rs];np.add.at(num[:,j],idx,d);np.add.at(num[:,j+3],idx,ll);np.add.at(den[:,j],idx,1);np.add.at(den[:,j+3],idx,1)
    for L in (20,40,60):
        b=bootstrap_daily(num,den,9999,L)
        for j,(row,rs,d,ll) in enumerate(cases):
            row[f'low{L}'],row[f'high{L}']=ci(b[:,j])
            if L==40:row['p_one_sided']=(1+int(np.sum(b[:,j]-row['delta_brier']<=row['delta_brier'])))/(len(b)+1);row['logloss_low'],row['logloss_high']=ci(b[:,j+3])
    for c,p in zip(cases,holm([c[0]['p_one_sided'] for c in cases])):c[0]['holm_p_secondary3']=float(p)
    write('stock-market-only-evaluation.csv',[c[0] for c in cases]);write('stock-market-only-metrics.csv',metrics);write('stock-market-only-reliability.csv',reliability);write('stock-market-only-weights.csv',weights)
    print('Secondary pure-market comparator completed')

if __name__=='__main__':run()
