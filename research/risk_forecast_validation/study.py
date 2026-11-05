"""Independent historical diagnostics of frozen v1. Not a new trading signal."""
import argparse,csv,gzip,hashlib,io,json,os,sys
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime,timezone
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/risk-forecast-v2-predictive-validation'
SOURCE_SHA='366f8cd00e8c228d4796d0abbe9997f717a3b6ad'
PROTOCOL_SHA256='bbc48d756173712907bfac6bc0ac1db4f492c85a009213ef9341d2214a1fbdc0'
MODELS=('technical_plus_v3','historical','volatility','regime','technical_combined','v3_state','v3_score')
BASELINES=('historical','volatility','regime')


def write(name,rows):
    rows=list(rows)
    if not rows:raise ValueError('no rows for '+name)
    stream=io.StringIO(newline='');w=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
    data=stream.getvalue().encode()
    if name.endswith('.gz'):data=gzip.compress(data,mtime=0)
    (OUT/name).write_bytes(data)


@contextmanager
def working(path):
    old=Path.cwd();os.chdir(path)
    try:yield
    finally:os.chdir(old)


def split_allowed(anchor,maturity,cutoff,calendar_index,boundary,embargo=20):
    return maturity is not None and maturity<=cutoff and anchor<cutoff and calendar_index<boundary-embargo


def terminal_label(return_pct,threshold):
    return None if return_pct is None else bool(return_pct<=-threshold*100+1e-10)


def regime_at(bars,at):
    known=[b for b in bars if b.available_at<=at]
    if len(known)<200:return None
    close=known[-1].close;ma=sum(b.close for b in known[-200:])/200;ret=close/known[-21].close-1
    return 'UP' if close>=ma and ret>0 else ('DOWN' if close<ma and ret<=0 else 'MIXED')


def scores(y,p):
    y=np.asarray(y,float);p=np.asarray(p,float)
    if len(y)!=len(p) or np.any(~np.isfinite(p)) or np.any((p<0)|(p>1)):raise ValueError('probability')
    if np.any((y!=0)&(y!=1)):raise ValueError('labels')
    q=np.clip(p,1e-6,1-1e-6)
    return (p-y)**2,-y*np.log(q)-(1-y)*np.log1p(-q)


def confusion(y,p,cut):
    y=np.asarray(y,bool);warn=np.asarray(p)>=cut
    tp=int(np.sum(warn&y));fp=int(np.sum(warn&~y));fn=int(np.sum(~warn&y));tn=int(np.sum(~warn&~y))
    return dict(tp=tp,fp=fp,fn=fn,tn=tn,precision=tp/(tp+fp) if tp+fp else None,recall=tp/(tp+fn) if tp+fn else None,
        false_positive_rate=fp/(fp+tn) if fp+tn else None,false_discovery_fraction=fp/(tp+fp) if tp+fp else None)


def bootstrap_losses(y,p,idx,n,counts):
    a,b=scores(y,p);den=counts @ np.bincount(idx,minlength=n)
    return [np.divide(counts @ np.bincount(idx,weights=loss,minlength=n),den,out=np.full(len(counts),np.nan),where=den>0) for loss in (a,b)]


def run(source):
    if hashlib.sha256((OUT/'protocol.md').read_bytes()).hexdigest()!=PROTOCOL_SHA256:raise ValueError('protocol changed')
    import subprocess
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()!=SOURCE_SHA:raise ValueError('source version')
    if subprocess.check_output(['git','diff','--name-only','HEAD','--','aae'],cwd=source,text=True).strip():raise ValueError('source code changed')
    sys.path.insert(0,str(source))
    from aae.research.risk_forecast_study import load_inputs
    from aae.research.risk_forecast import ProbabilityBank
    from aae.research.risk_v3_features import load_pack
    from aae.research.risk_forecast_statistics import block_counts,ci,holm,effective_n
    from aae.backtest.simulator import utc
    with working(source):
        raw,features,labels,folds,manifest=load_inputs();bars,markets,manifest=load_pack()
    profile=folds[2023]['configuration']
    if any(f['configuration']!=profile for f in folds.values()):raise ValueError('changed profile')
    dates=sorted({r['date'] for rs in raw.values() for r in rs});di={d:i for i,d in enumerate(dates)}
    qqq=sorted([b for b in bars if b.symbol=='QQQ'],key=lambda b:b.close_at)
    regimes={d:regime_at(qqq,utc(next(r['decision_at'] for r in raw['AMD'] if r['date']==d))) for d in dates}
    inventories=[]
    original_rows=list(csv.DictReader((source/'data/risk-signal-v3/bars.csv').open()))
    for symbol in ('AMD','NVDA','MU','QQQ','^SOX'):
        rs=[r for r in original_rows if r['symbol']==symbol];keys=[r['close_at'] for r in rs]
        bad=sum(not(0<float(r['low'])<=min(float(r['open']),float(r['close']))<=max(float(r['open']),float(r['close']))<=float(r['high']) and float(r['volume'])>=0) for r in rs)
        inventories.append(dict(symbol=symbol,rows=len(rs),first=min(keys),last=max(keys),duplicate_timestamps=len(keys)-len(set(keys)),invalid_ohlcv=bad,
            source_kind='REAL_PROVIDER_OBSERVATION_RETROSPECTIVE_VINTAGE',availability_kind='RECONSTRUCTED_NEXT_MIDNIGHT',verified_pit=False))
        if bad or len(keys)!=len(set(keys)):raise ValueError('bad observations')
    write('data-inventory.csv',inventories)
    daily=[];audits=[]
    for year in (2024,2025,2026):
        cutoff=f'{year-1}-01-01T00:00:00+00:00';boundary=next(i for i,d in enumerate(dates) if d>=f'{year-1}-01-01')
        test_boundary=next(i for i,d in enumerate(dates) if d>=f'{year}-01-01');cal_maturity=dates[test_boundary-20]
        for symbol,series in raw.items():
            for h in (5,10,20):
                for t in (.05,.10,.15):
                    for target in ('touch','terminal'):
                        training=[];regstats=defaultdict(lambda:[0,0])
                        for r in series:
                            f=features[profile,symbol,r['date']];lab=labels[symbol,r['date'],h,t]
                            y=lab['down_hit'] if target=='touch' else terminal_label(lab['terminal_return_pct'],t)
                            if f['features'] is None or not split_allowed(r['decision_at'],lab['label_available_at'],cutoff,di[r['date']],boundary):continue
                            training.append(dict(features=f['features'],decision_at=r['decision_at'],calendar_index=di[r['date']],target=y,label_available_at=lab['label_available_at']))
                            reg=regimes[r['date']]
                            if reg is not None:regstats[reg][0]+=1;regstats[reg][1]+=y
                        bank=ProbabilityBank(cutoff).fit(training)
                        if not bank.n:raise ValueError('empty training')
                        audit=dict(test_year=year,symbol=symbol,horizon=h,threshold_pct=t*100,target=target,cutoff=cutoff,embargo=20,
                            training_n=bank.n,last_training_anchor=bank.last_anchor.isoformat(),last_training_maturity=bank.last_maturity.isoformat(),
                            calibration_year=year-1,calibration_maturity_max=cal_maturity,test_first_allowed=dates[test_boundary+20],source_profile=profile)
                        audits.append(audit)
                        for r in series:
                            d=r['date'];yyear=int(d[:4]);lab=labels[symbol,d,h,t];item=features[profile,symbol,d];reg=regimes[d]
                            if item['features'] is None or not lab['complete'] or reg is None:continue
                            if yyear==year and di[d]>=test_boundary+20:role='TEST_REUSED_HISTORY'
                            elif yyear==year-1 and di[d]>=boundary+20 and lab['label_available_at'][:10]<=cal_maturity:role='CALIBRATION_DIAGNOSTIC_ONLY'
                            else:continue
                            y=lab['down_hit'] if target=='touch' else terminal_label(lab['terminal_return_pct'],t)
                            pred=bank.predict(item['features']);base=pred['historical']['probability'];n,pos=regstats[reg]
                            row=dict(symbol=symbol,date=d,decision_at=r['decision_at'],test_year=year,role=role,horizon=h,threshold_pct=t*100,target=target,
                                y=bool(y),regime=reg,close=r['indicators']['close'],terminal_return_pct=lab['terminal_return_pct'],up_hit=lab['up_hit'],label_available_at=lab['label_available_at'],
                                v1_low_support=pred['technical_plus_v3']['status'],vintage_verified=False)
                            for model in MODELS:row[model]=(pos+20*base)/(n+20) if model=='regime' else pred[model]['probability']
                            daily.append(row)
    write('fit-audit.csv',audits);write('forecast-daily.csv.gz',daily)
    selected=[r for r in daily if r['role']=='TEST_REUSED_HISTORY'];metrics=[];comparisons=[];calibration=[];alerts=[];stability=[]
    for target in ('touch','terminal'):
      for h in (5,10,20):
       for t in (5.,10.,15.):
        task=[r for r in selected if r['target']==target and r['horizon']==h and r['threshold_pct']==t]
        for symbol in ('ALL','AMD','NVDA','MU'):
            rs=sorted([r for r in task if symbol=='ALL' or r['symbol']==symbol],key=lambda r:(r['date'],r['symbol']))
            if not rs:continue
            full=dates[di[min(r['date'] for r in rs)]:di[max(r['date'] for r in rs)]+1];lookup={d:i for i,d in enumerate(full)}
            idx=np.array([lookup[r['date']] for r in rs]);y=np.array([r['y'] for r in rs],float);N=len(full)
            counts=block_counts(N,1999,40,17031+h*100+round(t*10));context=dict(symbol=symbol,target=target,horizon=h,threshold_pct=t)
            boots={};points={}
            for model in MODELS:
                p=np.array([r[model] for r in rs]);loss=scores(y,p);points[model]=[float(z.mean()) for z in loss];boot=bootstrap_losses(y,p,idx,N,counts);boots[model]=boot
                bl,bh=ci(boot[0]);ll,lh=ci(boot[1])
                metrics.append(dict(context,model=model,n=len(rs),positive=int(y.sum()),calendar_dates=len(full),observed_dates=len(set(r['date'] for r in rs)),calendar_blocks40=N//40,
                    effective_n=effective_n(y,idx,N),brier=points[model][0],brier_low=bl,brier_high=bh,log_loss=points[model][1],log_loss_low=ll,log_loss_high=lh,
                    mean_probability=float(p.mean()),observed_rate=float(y.mean()),low_support_fraction=float(np.mean([r['v1_low_support']=='LOW_SUPPORT' for r in rs])) if model=='technical_plus_v3' else None))
                for cut in (.5,.7):alerts.append(dict(context,model=model,cutoff=cut,**confusion(y,p,cut)))
                for b in range(10):
                    chosen=(p>=b/10)&((p<(b+1)/10) if b<9 else (p<=1));n=int(chosen.sum())
                    calibration.append(dict(context,role='TEST_REUSED_HISTORY',model=model,bin=b,n=n,mean_probability=float(p[chosen].mean()) if n else None,observed_rate=float(y[chosen].mean()) if n else None,uncertainty='DESCRIPTIVE_DEPENDENT_BIN'))
                for dim in ('test_year','regime'):
                    for val in sorted({r[dim] for r in rs}):
                        mask=np.array([r[dim]==val for r in rs]);a,b=scores(y[mask],p[mask]);stability.append(dict(context,model=model,dimension=dim,value=val,n=int(mask.sum()),positive=int(y[mask].sum()),brier=float(a.mean()),log_loss=float(b.mean()),inference='EXPLORATORY_STRATUM'))
            for baseline in BASELINES:
                diff=boots['technical_plus_v3'][0]-boots[baseline][0];point=points['technical_plus_v3'][0]-points[baseline][0];low,high=ci(diff)
                centered=diff-point;pvalue=(1+int(np.sum(centered<=point)))/(len(diff)+1)
                signs=[]
                for L in (20,60):
                    bc=block_counts(N,1999,L,17031+h*100+round(t*10));a=bootstrap_losses(y,np.array([r['technical_plus_v3'] for r in rs]),idx,N,bc)[0];b=bootstrap_losses(y,np.array([r[baseline] for r in rs]),idx,N,bc)[0];lo,hi=ci(a-b);signs.append((lo,hi))
                ld=boots['technical_plus_v3'][1]-boots[baseline][1];lolo,hihi=ci(ld)
                support=bool(len(set((idx[y==1]//40).tolist()))>=5 and len(set((idx[y==0]//40).tolist()))>=5 and min(y.sum(),len(y)-y.sum())>=10 and N//40>=10)
                comparisons.append(dict(context,baseline=baseline,n=len(rs),delta_brier=point,ci_low=low,ci_high=high,relative_brier_improvement=-point/points[baseline][0],p_one_sided=pvalue,support_adequate=support,
                    holm_p=None,delta_logloss=points['technical_plus_v3'][1]-points[baseline][1],delta_logloss_low=lolo,delta_logloss_high=hihi,
                    block20_low=signs[0][0],block20_high=signs[0][1],block60_low=signs[1][0],block60_high=signs[1][1],primary=target=='touch' and symbol=='ALL',criteria_pass=False))
    primary=[r for r in comparisons if r['primary']]
    for r,pvalue in zip(primary,holm([r['p_one_sided'] for r in primary])):
        r['holm_p']=pvalue
        stable=True
        for dimension,values in [('test_year',(2024,2025,2026))]:
            for val in values:
                a=next(z for z in stability if z['symbol']=='ALL' and z['target']=='touch' and z['horizon']==r['horizon'] and z['threshold_pct']==r['threshold_pct'] and z['model']=='technical_plus_v3' and z['dimension']==dimension and z['value']==val)
                b=next(z for z in stability if z['symbol']=='ALL' and z['target']=='touch' and z['horizon']==r['horizon'] and z['threshold_pct']==r['threshold_pct'] and z['model']==r['baseline'] and z['dimension']==dimension and z['value']==val)
                stable &= a['brier']<b['brier']
        for sym in ('AMD','NVDA','MU'):
            z=next(z for z in comparisons if z['symbol']==sym and z['target']=='touch' and z['horizon']==r['horizon'] and z['threshold_pct']==r['threshold_pct'] and z['baseline']==r['baseline']);stable &= z['delta_brier']<0
        r['criteria_pass']=bool(r['support_adequate'] and pvalue<.05 and r['relative_brier_improvement']>=.01 and r['ci_high']<0 and r['block20_high']<0 and r['block60_high']<0 and stable)
    write('metrics.csv',metrics);write('baseline-comparison.csv',comparisons);write('reliability.csv',calibration);write('alerts.csv',alerts);write('stability.csv',stability)
    # Calibration year is never fitted; export it independently of test metrics.
    cal=[]
    for year in (2024,2025,2026):
      for symbol in ('AMD','NVDA','MU'):
       for h in (5,10,20):
        for t in (5.,10.,15.):
         for target in ('touch','terminal'):
          rs=[r for r in daily if r['test_year']==year and r['symbol']==symbol and r['horizon']==h and r['threshold_pct']==t and r['target']==target and r['role']=='CALIBRATION_DIAGNOSTIC_ONLY']
          for model in MODELS:
            a,b=scores([r['y'] for r in rs],[r[model] for r in rs]);cal.append(dict(test_year=year,calibration_year=year-1,symbol=symbol,horizon=h,threshold_pct=t,target=target,model=model,n=len(rs),brier=float(a.mean()),log_loss=float(b.mean()),used_to_fit=False))
    write('calibration-period.csv',cal)
    economics(selected,bars)
    summary=dict(source_sha=SOURCE_SHA,protocol_sha256=PROTOCOL_SHA256,rows=len(daily),test_rows=len(selected),primary_comparisons=len(primary),primary_comparisons_pass=sum(r['criteria_pass'] for r in primary),
        touch_tasks_meeting_all_baselines=sum(all(r['criteria_pass'] for r in primary if r['horizon']==h and r['threshold_pct']==t) for h in (5,10,20) for t in (5.,10.,15.)),
        source_vintage_verified=False,independent_untouched_holdout=False,overall_conclusion='RESEARCH ONLY',new_model_proposed=False,synthetic_market_observations_used=False)
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');return summary


def lot(sale_open,buy_open):
    cash=sale_open*(1-.0005)*(1-.0005);cost=buy_open*(1+.0005)*(1+.0005);qty=min(1.,cash/cost);left=cash-qty*cost
    return dict(sale_net=cash,buy_unit_cost=cost,restored_qty=qty,cash_left=left,relative_mark=left+qty*buy_open-buy_open)


def economics(selected,bars):
    output=[];summary=[]
    stocks={s:sorted([b for b in bars if b.symbol==s],key=lambda b:b.close_at) for s in ('AMD','NVDA','MU')}
    for s,bs in stocks.items():
     lookup={b.close_at.date().isoformat():i for i,b in enumerate(bs)}
     for h in (5,10,20):
      for t in (5.,10.,15.):
       rs=sorted([r for r in selected if r['symbol']==s and r['target']=='touch' and r['horizon']==h and r['threshold_pct']==t],key=lambda r:r['date'])
       for delay in (1,2):
        until=-1;executed=0;unfilled=0;marks=[]
        for r in rs:
            if r['technical_plus_v3']<.5:continue
            i=lookup[r['date']]
            if i<=until:continue
            sale=i+delay;buy=sale+h
            if buy>=len(bs):unfilled+=1;continue
            if bs[sale].open_at<=datetime.fromisoformat(r['decision_at']):raise ValueError('early fill')
            z=lot(bs[sale].open,bs[buy].open);until=buy;executed+=1;marks.append(z['relative_mark']/bs[sale].open*100)
            output.append(dict(symbol=s,horizon=h,threshold_pct=t,delay=delay,signal_date=r['date'],sale_date=bs[sale].close_at.date().isoformat(),buy_date=bs[buy].close_at.date().isoformat(),sale_open=bs[sale].open,buy_open=bs[buy].open,
                buy_above_sale=bs[buy].open>bs[sale].open,warning_target_hit=r['y'],price_only=True,**z))
        summary.append(dict(symbol=s,horizon=h,threshold_pct=t,delay=delay,executed_lots=executed,cutoff_unfilled=unfilled,mean_relative_mark_pct=float(np.mean(marks)) if marks else None,
            interpretation='NONOVERLAPPING_ONE_UNIT_RESTORATION_DIAGNOSTIC_NOT_PORTFOLIO_RETURN'))
    write('economic-lots.csv',output);write('economic-summary.csv',summary)


if __name__=='__main__':
    ap=argparse.ArgumentParser(__doc__);ap.add_argument('--source',type=Path,required=True);a=ap.parse_args();print(json.dumps(run(a.source.resolve()),indent=2))
