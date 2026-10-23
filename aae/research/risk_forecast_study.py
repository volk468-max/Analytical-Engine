"""Frozen-signal risk forecasting, chronological probability fitting and evaluation."""
import csv
import gzip
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import numpy as np
from aae.backtest.cli import write_csv
from aae.backtest.simulator import utc
from .risk_v3_features import load_pack
from .risk_signal_v3 import catalogue,evaluate
from .risk_forecast import ForecastFeatures,ProbabilityBank,MODELS,barrier_label
from .risk_forecast_statistics import block_counts,ci,metric_samples,effective_n,paired_difference,holm,score_slope

ROOT=Path('reports/risk-forecast-v1')
SOURCE=Path('reports/risk-signal-v3')
SYMBOLS=('AMD','NVDA','MU')
HORIZONS=(5,10,20)
THRESHOLDS=(.05,.10,.15)
STATES=('HOLD','WATCH','REDUCE','CRITICAL')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_inputs():
    bars,_,manifest=load_pack()
    archive=json.loads((SOURCE/'run.json').read_text())
    for name,digest in archive['source_sha256'].items():
        p=Path(name)
        if not p.exists() and '/aae/' in name:p=Path('aae/'+name.split('/aae/',1)[1])
        if sha(p)!=digest:raise ValueError('Changed v3 source: '+name)
    for name in ('daily-signals.jsonl.gz','fold-selection.csv','events.csv'):
        if sha(SOURCE/name)!=archive['output_sha256'][name]:raise ValueError('Changed frozen output: '+name)
    folds={int(r['test_year']):r for r in csv.DictReader((SOURCE/'fold-selection.csv').open()) if r['variant']=='C'}
    if set(folds)!={2023,2024,2025,2026}:raise ValueError('Missing source folds')
    for year,r in folds.items():
        if r['training_end']>=f'{year}-01-01':raise ValueError('Future-selected source profile')
    if folds[2026]['configuration']!='sensitive':raise ValueError('Unexpected 2026 profile')
    raw={s:[] for s in SYMBOLS};walk={}
    with gzip.open(SOURCE/'daily-signals.jsonl.gz','rt') as stream:
        for line in stream:
            r=json.loads(line)
            if r['variant']!='C':continue
            if r['mode']=='fixed_balanced':raw[r['symbol']].append(r)
            elif r['mode']=='walk_forward':walk[(r['symbol'],r['date'])]=r
    profiles={c.name:c for c in catalogue()};replays={}
    for name in sorted({r['configuration'] for r in folds.values()}):
        for symbol in SYMBOLS:
            previous=None;series=[]
            for r in sorted(raw[symbol],key=lambda r:r['date']):
                signal=evaluate(symbol,r['decision_at'],r['indicators'],r['quality'],variant='C',config=profiles[name],previous=previous)
                signal.update(date=r['date']);series.append(signal);previous=signal
            replays[(name,symbol)]=series
    stocks={s:[b for b in bars if b.symbol==s] for s in SYMBOLS}
    labels={};features={};dates=sorted({r['date'] for rows in raw.values() for r in rows})
    date_index={date:i for i,date in enumerate(dates)}
    for symbol in SYMBOLS:
        by_date={b.close_at.date().isoformat():i for i,b in enumerate(stocks[symbol])}
        for name in {r['configuration'] for r in folds.values()}:
            for s in replays[(name,symbol)]:
                i=by_date[s['date']];b=stocks[symbol][i]
                if s['decision_at']!=b.available_at.isoformat() or s['indicators']['close']!=b.close:
                    raise ValueError('Signal/candle mismatch')
                if i+1<len(stocks[symbol]) and stocks[symbol][i+1].open_at<=b.available_at:
                    raise ValueError('Future-session barrier starts before anchor publication')
                f=None
                if s['data_status']=='OK':
                    v=s['indicators']
                    f=ForecastFeatures(s['risk_level'],int(s['score']),v['drawdown_20_pct'],v['rv20_pct'],v['close'],v['ma50'],v['rsi14'])
                features[(name,symbol,s['date'])]=dict(features=f,signal=s,calendar_index=date_index[s['date']])
                for h in HORIZONS:
                    for t in THRESHOLDS:
                        key=(symbol,s['date'],h,t)
                        if key not in labels:labels[key]=barrier_label(stocks[symbol],i,h,t)
        for s in raw[symbol]:
            year=int(s['date'][:4])
            if year<2023:continue
            replay=features[(folds[year]['configuration'],symbol,s['date'])]['signal']
            old=walk[(symbol,s['date'])]
            if replay['risk_level']!=old['risk_level'] or replay['score']!=old['score']:
                raise ValueError('Replay changed held-out source signal')
    return raw,features,labels,folds,manifest


def forecasts(raw,features,labels,folds):
    daily=[];audit=[];banks={}
    for year,fold in sorted(folds.items()):
        cutoff=f'{year}-01-01T00:00:00+00:00';profile=fold['configuration']
        for symbol in SYMBOLS:
            anchors=[r for r in raw[symbol] if r['date']<f'{year}-01-01']
            for h in HORIZONS:
                for t in THRESHOLDS:
                    for direction in ('down','up'):
                        training=[];pending=0
                        for r in anchors:
                            f=features[(profile,symbol,r['date'])];label=labels[(symbol,r['date'],h,t)]
                            if not label['complete'] or utc(label['label_available_at'])>utc(cutoff):pending+=1
                            if f['features'] is not None:
                                training.append(dict(features=f['features'],decision_at=r['decision_at'],
                                    calendar_index=f['calendar_index'],target=label[direction+'_hit'],label_available_at=label['label_available_at']))
                        bank=ProbabilityBank(cutoff).fit(training)
                        banks[(year,symbol,h,t,direction)]=bank
                        audit.append(dict(test_year=year,symbol=symbol,horizon=h,threshold_pct=t*100,direction=direction,
                            v3_profile=profile,v3_profile_training_end=fold['training_end'],probability_cutoff=cutoff,
                            training_n=bank.n,training_positive=bank.positives,excluded_unmatured_anchors=pending,
                            last_anchor=bank.last_anchor.isoformat() if bank.last_anchor else None,
                            last_horizon_publication=bank.last_maturity.isoformat() if bank.last_maturity else None))
    for symbol in SYMBOLS:
        for r in sorted(raw[symbol],key=lambda r:r['date']):
            year=int(r['date'][:4]);test=year>=2023
            profile=folds[year]['configuration'] if test else folds[2023]['configuration']
            item=features[(profile,symbol,r['date'])];s=item['signal'];f=item['features']
            for h in HORIZONS:
                for t in THRESHOLDS:
                    label=labels[(symbol,r['date'],h,t)]
                    row=dict(symbol=symbol,date=r['date'],decision_at=r['decision_at'],
                        role='OUT_OF_SAMPLE' if test else 'TRAINING_DESCRIPTIVE_ONLY',
                        horizon=h,threshold_pct=t*100,v3_profile=profile,risk_level=s['risk_level'],risk_score=s['score'],
                        data_status=s['data_status'],close=s['indicators']['close'],
                        drawdown_20_pct=s['indicators']['drawdown_20_pct'],rv20_pct=s['indicators']['rv20_pct'],
                        rsi14=s['indicators']['rsi14'],ma50=s['indicators']['ma50'],
                        probability_cutoff=f'{year}-01-01T00:00:00+00:00' if test else None,
                        calendar_index=item['calendar_index'],**label)
                    for direction in ('down','up'):
                        p=banks[(year,symbol,h,t,direction)].predict(f) if test and f else {}
                        for model in MODELS:
                            values=p.get(model,{})
                            row[f'p_{direction}_{model}']=values.get('probability')
                            row[f'status_{direction}_{model}']=values.get('status','TRAINING_ONLY' if not test else 'DATA_UNAVAILABLE')
                            row[f'cell_n_{direction}_{model}']=values.get('cell_n')
                            row[f'cell_positive_{direction}_{model}']=values.get('cell_positive')
                            row[f'cell_blocks_{direction}_{model}']=values.get('cell_blocks')
                            row[f'backoff_{direction}_{model}']=values.get('backoff')
                    daily.append(row)
    return daily,audit


def as_number(x):return float(x) if np.isfinite(x) else None


def conditioned(rows,indices,y,counts,mask,context):
    chosen=np.flatnonzero(mask)
    if not len(chosen):return None
    w=counts[:,indices[chosen]].astype(float);n=w.sum(axis=1)
    observed=np.divide(w@y[chosen],n,out=np.full(len(w),np.nan),where=n>0)
    lo,hi=ci(observed)
    dates={rows[i]['date'] for i in chosen}
    blocks={rows[i]['calendar_index']//40 for i in chosen}
    positive=int(y[chosen].sum());raw_n=len(chosen)
    return dict(context,n=raw_n,n_dates=len(dates),calendar_blocks_40=len(blocks),positive=positive,
        frequency=float(y[chosen].mean()),frequency_low=lo,frequency_high=hi,effective_n_hac=None,
        uncertainty_status='LOW_BLOCK_OR_CLASS_SUPPORT' if len(blocks)<5 or min(positive,raw_n-positive)<10 else 'DEPENDENT_RESEARCH_ESTIMATE')


def evaluate_forecasts(daily):
    metrics=[];comparisons=[];calibration=[];states=[];scores=[];monotonicity=[];annual=[];sensitivity=[]
    oos=[r for r in daily if r['role']=='OUT_OF_SAMPLE' and r['complete'] and all(r['p_down_'+m] is not None and r['p_up_'+m] is not None for m in MODELS)]
    for h in HORIZONS:
        for t in THRESHOLDS:
            for direction in ('down','up'):
                for symbol in ('ALL',*SYMBOLS):
                    rows=sorted([r for r in oos if r['horizon']==h and r['threshold_pct']==t*100 and (symbol=='ALL' or r['symbol']==symbol)],key=lambda r:(r['date'],r['symbol']))
                    if not rows:continue
                    dates=sorted({r['date'] for r in rows});lookup={d:i for i,d in enumerate(dates)}
                    index=np.array([lookup[r['date']] for r in rows]);N=len(dates)
                    counts=block_counts(N,399,40,731+h)
                    w=np.vstack([np.ones(len(rows)),counts[:,index]])
                    y=np.array([r[direction+'_hit'] for r in rows],float)
                    score=np.array([r['risk_score'] for r in rows],float)
                    context=dict(symbol=symbol,direction=direction,horizon=h,threshold_pct=t*100)
                    predictions={m:np.array([r[f'p_{direction}_{m}'] for r in rows],float) for m in MODELS}
                    neff=effective_n(y,index,N)
                    for model,p in predictions.items():
                        samples=metric_samples(y,p,w)
                        result=dict(context,model=model,n=len(rows),n_dates=N,calendar_blocks_40=N//40,
                            effective_n_hac=neff,positive=int(y.sum()),negative=int(len(y)-y.sum()),
                            mean_probability=float(p.mean()),low_support_forecast_pct=float(np.mean([r[f'status_{direction}_{model}']!='SUPPORTED_RESEARCH_ESTIMATE' for r in rows])*100),
                            inference_status='LOW_EFFECTIVE_SAMPLE' if neff is None or neff<30 or min(y.sum(),len(y)-y.sum())<10 or N//40<10 else 'DEPENDENT_RESEARCH_ESTIMATE')
                        for metric,array in samples.items():
                            lo,hi=ci(array[1:]);result.update({metric:as_number(array[0]),metric+'_low':lo,metric+'_high':hi})
                        metrics.append(result)
                        for b in range(10):
                            mask=(p>=b/10)&(p<(b+1)/10 if b<9 else p<=1)
                            rec=conditioned(rows,index,y,counts,mask,dict(context,model=model,bin_low=b/10,bin_high=(b+1)/10))
                            if rec:rec['mean_probability']=float(p[mask].mean());calibration.append(rec)
                        for year in (2023,2024,2025,2026):
                            take=np.array([r['date'].startswith(str(year)) for r in rows])
                            ys=y[take];ps=p[take]
                            vals=metric_samples(ys,ps,np.ones((1,len(ys))))
                            annual.append(dict(context,model=model,year=year,n=len(ys),**{k:as_number(v[0]) for k,v in vals.items()}))
                    for state in STATES:
                        rec=conditioned(rows,index,y,counts,np.array([r['risk_level']==state for r in rows]),dict(context,state=state))
                        if rec:states.append(rec)
                    rates=[]
                    for value in range(12):
                        rec=conditioned(rows,index,y,counts,score==value,dict(context,risk_score=value))
                        if rec:scores.append(rec);rates.append(rec['frequency'])
                    slopes=score_slope(score,y,w);lo,hi=ci(slopes[1:])
                    monotonicity.append(dict(context,slope_per_score_point=as_number(slopes[0]),slope_low=lo,slope_high=hi,
                        adjacent_frequency_reversals=sum(b<a for a,b in zip(rates,rates[1:])),
                        inference='EXPLORATORY_UNADJUSTED'))
                    for model in ('v3_state','v3_score','technical_plus_v3'):
                        for baseline in ('historical','drawdown','volatility','ma50_rsi','technical_combined'):
                            primary=symbol=='ALL' and model=='technical_plus_v3' and baseline=='technical_combined'
                            bootstrap=block_counts(N,1999,40,313+h) if primary else counts
                            rec=dict(context,model=model,baseline=baseline,n=len(y),primary=primary,
                                **paired_difference(y,predictions[model],predictions[baseline],index,N,bootstrap))
                            bs=float(np.mean((predictions[baseline]-y)**2))
                            rec['relative_brier_improvement_pct']=-rec['brier_difference']/bs*100 if bs else None
                            comparisons.append(rec)
                            if primary:
                                for length in (20,40,60):
                                    boot=bootstrap if length==40 else block_counts(N,399,length,313+h)
                                    sensitivity.append(dict(context,block_length=length,**paired_difference(y,predictions[model],predictions[baseline],index,N,boot)))
                print(json.dumps(dict(evaluated_horizon=h,threshold=t,direction=direction)),flush=True)
    primary=[r for r in comparisons if r['primary']]
    for row,adjusted in zip(primary,holm([r['brier_p_one_sided'] for r in primary])):
        row['holm_p_18']=adjusted
        blocks=[r for r in sensitivity if all(r[k]==row[k] for k in ('direction','horizon','threshold_pct'))]
        row['stable_block_20_40_60']=all(r['brier_difference_high'] is not None and r['brier_difference_high']<0 for r in blocks)
        row['incremental_evidence']=adjusted<.05 and row['brier_difference_high']<0 and row['relative_brier_improvement_pct']>=1 and row['stable_block_20_40_60']
    return dict(metrics=metrics,comparisons=comparisons,calibration=calibration,states=states,scores=scores,
                monotonicity=monotonicity,annual=annual,sensitivity=sensitivity)


def errors(daily,raw,features,folds):
    output=[]
    anchors=[r for r in daily if r['horizon']==20 and r['threshold_pct']==10]
    lookup={(r['symbol'],r['date']):r for r in anchors}
    for row in anchors:
        if not row['complete']:continue
        types=[]
        if row['risk_level'] in ('REDUCE','CRITICAL') and row['up_hit']:types.append('REDUCE_THEN_UP10_WITHIN20')
        if row['risk_level']=='HOLD' and row['down_hit']:types.append('HOLD_THEN_DOWN10_WITHIN20')
        for kind in types:
            output.append(dict(symbol=row['symbol'],date=row['date'],role=row['role'],category=kind,
                risk_level=row['risk_level'],risk_score=row['risk_score'],close=row['close'],
                down_hit_date=row['down_hit_date'],up_hit_date=row['up_hit_date'],hit_order=row['hit_order'],
                terminal_return_20_pct=row['terminal_return_pct'],p_down_v3=row['p_down_v3_state'],
                p_down_historical=row['p_down_historical'],p_down_technical=row['p_down_technical_combined'],
                p_down_technical_plus_v3=row['p_down_technical_plus_v3']))
    for row in csv.DictReader((SOURCE/'events.csv').open()):
        if row['mode']!='walk_forward' or row['variant']!='C' or not row['first_reduce']:continue
        fraction=float(row['observed_fall_fraction_before_reduce'])
        if fraction>.5 or row['reduce_after_observed_trough']=='True':
            output.append(dict(symbol=row['symbol'],date=row['first_reduce'],role='OUT_OF_SAMPLE',
                category='REDUCE_AFTER_HALF_OBSERVED_FALL',peak_date=row['peak_date'],
                trough_date=row['trough_date'],observed_fall_fraction_before_reduce=fraction,
                reduce_after_trough=row['reduce_after_observed_trough'],
                information_cutoff=row['information_cutoff'],episode_end=row['end_date']))
    for symbol in SYMBOLS:
        rows=sorted(raw[symbol],key=lambda r:r['date'])
        for i in range(5,len(rows)):
            row=lookup[(symbol,rows[i]['date'])]
            year=int(row['date'][:4]);name=folds[year]['configuration'] if year>=2023 else folds[2023]['configuration']
            current=features[(name,symbol,row['date'])]['signal']
            old=features[(name,symbol,rows[i-5]['date'])]['signal']
            recent=[features[(name,symbol,r['date'])]['signal'] for r in rows[i-2:i+1]]
            a=current['indicators'];b=old['indicators']
            if all(s['risk_level']=='HOLD' for s in recent) and a['drawdown_20_pct']<=b['drawdown_20_pct']-3 and (
                a['rv20_pct']>=b['rv20_pct']*1.10 or a['rsi14']<=b['rsi14']-10):
                output.append(dict(symbol=symbol,date=row['date'],role=row['role'],category='GRADUAL_DETERIORATION_STILL_HOLD',
                    risk_level='HOLD',risk_score=row['risk_score'],drawdown_20_pct=a['drawdown_20_pct'],
                    previous_dd20=b['drawdown_20_pct'],rv20_pct=a['rv20_pct'],previous_rv20=b['rv20_pct'],
                    rsi14=a['rsi14'],previous_rsi14=b['rsi14'],horizon_complete=row['complete'],
                    down_hit_20=row['down_hit'],terminal_return_20_pct=row['terminal_return_pct']))
    return sorted(output,key=lambda r:(r['symbol'],r['date'],r['category']))


def plots(evaluation,daily):
    import os
    os.environ.setdefault('MPLCONFIGDIR','/tmp/alpha-forecast-mpl')
    os.environ.setdefault('XDG_CACHE_HOME','/tmp/alpha-forecast-cache')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    for direction in ('down','up'):
        fig,axes=plt.subplots(3,3,figsize=(14,12),sharex=True,sharey=True)
        for i,t in enumerate(THRESHOLDS):
            for j,h in enumerate(HORIZONS):
                ax=axes[i,j];ax.plot([0,1],[0,1],'k--',lw=.8)
                for model in ('v3_state','v3_score','historical','technical_combined','technical_plus_v3'):
                    rows=[r for r in evaluation['calibration'] if r['symbol']=='ALL' and r['direction']==direction and r['horizon']==h and r['threshold_pct']==t*100 and r['model']==model]
                    line=ax.plot([r['mean_probability'] for r in rows],[r['frequency'] for r in rows],'.-',label=model,lw=1)[0]
                    if model in ('v3_state','technical_plus_v3'):
                        for r in rows:
                            if r['frequency_low'] is not None:
                                ax.plot([r['mean_probability']]*2,[r['frequency_low'],r['frequency_high']],alpha=.25,lw=2,color=line.get_color())
                ax.set_title(f'{direction.upper()} {t*100:g}% within {h} sessions')
                ax.set_xlim(0,1);ax.set_ylim(0,1);ax.grid(alpha=.2)
                if i==2:ax.set_xlabel('Frozen forecast probability')
                if j==0:ax.set_ylabel('Observed hit frequency')
        axes[0,0].legend(fontsize=7);fig.suptitle('Out-of-sample reliability; vertical bars: 95% calendar-block intervals')
        fig.tight_layout();fig.savefig(ROOT/f'reliability-{direction}.png',dpi=130);plt.close(fig)
    fig,axes=plt.subplots(3,2,figsize=(12,10))
    for i,symbol in enumerate(SYMBOLS):
        rows=[r for r in daily if r['role']=='OUT_OF_SAMPLE' and r['symbol']==symbol and r['horizon']==20 and r['threshold_pct']==10 and r['p_down_v3_state'] is not None]
        for j,direction in enumerate(('down','up')):
            for model in ('historical','v3_state','v3_score','technical_plus_v3'):
                axes[i,j].hist([r[f'p_{direction}_{model}'] for r in rows],bins=np.linspace(0,1,21),histtype='step',label=model)
            axes[i,j].set_title(f'{symbol}: {direction} 10% / 20 sessions');axes[i,j].legend(fontsize=7)
            axes[i,j].set_xlabel('Forecast probability');axes[i,j].set_ylabel('Daily forecasts (dependent)')
    fig.tight_layout();fig.savefig(ROOT/'forecast-distributions.png',dpi=130);plt.close(fig)


def fmt(value,places=3):return '—' if value is None else f'{value:.{places}f}'


def report(evaluation,event_rows,audit,daily):
    primary=[r for r in evaluation['comparisons'] if r['primary']]
    passed=[r for r in primary if r['incremental_evidence']]
    lines=['# Risk Forecast v1 — predictive information, not trading','',
        '**No trades, position-size policy, economic simulation or changes to REDUCE.** Protocol committed before results; compare all predeclared tasks, not a selected October result.','',
        '## Data and chronological design','',
        'Unchanged retrospective PR #5 pack inherited through PR #6: AMD/NVDA/MU, 2021–22 October 2026, with 2020 indicator warmup. No new or synthetic market data. 2021–2022 are training/descriptive only. Held-out probability predictions cover 2023–2026 using annual Jan 1 frozen estimators. For each fold replay its original C profile on earlier archived indicators; held-out states and scores are asserted identical to the original walk-forward outputs. 2026 remains C/sensitive; there is no new selection of REDUCE thresholds.','',
        'Each training anchor must have its **entire** forecast horizon published by the freeze timestamp. A hit that happened early does not authorize inclusion of an otherwise unfinished horizon. fit-audit.csv exports last anchor, last horizon publication, cutoff and excluded unmatured counts for every stock/task/fold. Daily predictors are immutable whitelisted feature objects; future labels reside in a separate evaluation function.','',
        '## Target and probability models','',
        'From the anchor Close, a DOWN hit uses any future Low <=95/90/85% and an UP hit any High >=105/110/115%, within 5/10/20 subsequent stock sessions. Anchor OHLC is excluded. Both labels can be true. First-hit dates establish ordering unless both barriers first occur in one daily bar; an opening gap beyond one barrier establishes that direction first, otherwise UNKNOWN_INTRADAY. Terminal close return is separate. Incomplete horizons have null full-horizon labels/returns, alongside observed-to-date hit bounds.','',
        'Eight transparent per-stock models: historical unconditional, matched dd20, matched RV20, MA50/RSI, v3 state, v3 score bin, joint technical cells, joint technical + v3 cells. Fixed bins and shrinkage=20 are in protocol.md; no test tuning. Incremental v3 cells shrink toward their identical technical parent, other cells toward stock training history. Unseen cells back off. LOW_SUPPORT flags cells with <60 anchors, <10 positives/negatives or occurrences in <5 calendar blocks. Numeric low-support values are auditable research point estimates, not reliable live probabilities; do not interpret extra decimal places as certainty.','',
        '## Confirmatory incremental comparison','',
        f'{len(passed)} of {len(primary)} predeclared tasks pass the combined criterion: Holm-adjusted p<0.05 across all 18 tasks, negative 95% paired Brier interval, >=1% relative Brier improvement and negative intervals for block20/40/60. '+('The protocol finds task-specific incremental evidence, subject to the limitations below; it does not establish general investment effectiveness.' if passed else '**An incremental predictive advantage of v3 beyond the joint technical baseline is not confirmed under the predefined criterion.**'),'','| Direction | Hit % | Sessions | Δ Brier [95% CI] | Relative improvement % | Holm p | Stable blocks | Criterion met |',
        '|---|---|---|---|---|---|---|---|']
    for r in primary:
        lines.append(f"| {r['direction']} | {r['threshold_pct']:g} | {r['horizon']} | {fmt(r['brier_difference'],4)} [{fmt(r['brier_difference_low'],4)}, {fmt(r['brier_difference_high'],4)}] | {fmt(r['relative_brier_improvement_pct'],2)} | {fmt(r['holm_p_18'],4)} | {r['stable_block_20_40_60']} | {r['incremental_evidence']} |")
    lines += ['', 'Negative Δ Brier/log loss favors added v3. Primary paired samples retain all stocks on the same calendar block; comparisons with standalone v3 state/score and each simple baseline are exploratory in baseline-comparison.csv. A failure to confirm is not proof that every possible estimator lacks signal. Strong state-frequency differences can reflect volatility, current drawdown or trend already captured by simpler models.','',
        '## Reference task: DOWN 10% within 20 sessions (all stocks)','',
        '| Model | N / effective N | Event rate [95% CI] | Mean forecast | Brier [95% CI] | Log loss | ROC-AUC | PR-AUC (AP) | Low-support forecasts % |',
        '|---|---|---|---|---|---|---|---|---|']
    for r in evaluation['metrics']:
        if r['symbol']=='ALL' and r['direction']=='down' and r['threshold_pct']==10 and r['horizon']==20:
            lines.append('| '+' | '.join([r['model'],str(r['n'])+' / '+fmt(r['effective_n_hac'],1),f"{fmt(r['frequency'])} [{fmt(r['frequency_low'])}, {fmt(r['frequency_high'])}]",fmt(r['mean_probability']),f"{fmt(r['brier'])} [{fmt(r['brier_low'])}, {fmt(r['brier_high'])}]",fmt(r['log_loss']),fmt(r['roc_auc']),fmt(r['pr_auc_ap']),fmt(r['low_support_forecast_pct'],1)])+' |')
    lines += ['', 'Full metrics.csv includes all tasks, stock-level estimates, confidence intervals, class counts, effective N, date/block counts and low-support status. PR-AUC is noninterpolated average precision with tied probabilities grouped; it is not trapezoidal PR area. ROC/AP are omitted if only one class occurs.','',
        '## State frequencies and numeric risk score','',
        '| Stock | State | N | DOWN10/20 frequency [95% CI] | Block/class support |',
        '|---|---|---|---|---|']
    for r in evaluation['states']:
        if r['direction']=='down' and r['threshold_pct']==10 and r['horizon']==20:
            lines.append(f"| {r['symbol']} | {r['state']} | {r['n']} | {fmt(r['frequency'])} [{fmt(r['frequency_low'])}, {fmt(r['frequency_high'])}] | {r['uncertainty_status']} |")
    slopes=[r for r in evaluation['monotonicity'] if r['symbol']=='ALL' and r['direction']=='down']
    positive=sum(r['slope_low'] is not None and r['slope_low']>0 for r in slopes)
    lines += ['', f'{positive}/9 DOWN tasks have a positive exploratory 95% interval for the score-frequency slope. score-probabilities.csv retains exact scores; score-monotonicity.csv includes slopes and adjacent frequency reversals, for UP as well as DOWN. These are unadjusted diagnostics, not independent confirmations or monotonicity guarantees. A score can predict wider fluctuations in both directions without a directional forecasting advantage.','',
        '## Historical error examples (first chronological held-out example)','',
        '| Stock | Category | Date | Observed outcome / context |',
        '|---|---|---|---|']
    categories=('REDUCE_THEN_UP10_WITHIN20','HOLD_THEN_DOWN10_WITHIN20','REDUCE_AFTER_HALF_OBSERVED_FALL','GRADUAL_DETERIORATION_STILL_HOLD')
    for symbol in SYMBOLS:
        for category in categories:
            matches=[r for r in event_rows if r['symbol']==symbol and r['category']==category and r['role']=='OUT_OF_SAMPLE']
            if matches:
                r=matches[0]
                detail=(f"UP {r.get('up_hit_date')}; DOWN {r.get('down_hit_date')}; order {r.get('hit_order')}; terminal20 {fmt(r.get('terminal_return_20_pct'),2)}%" if category in categories[:2] else f"Observed fall fraction {fmt(r.get('observed_fall_fraction_before_reduce'))}; trough {r.get('trough_date')}" if category==categories[2] else f"DD20 {fmt(r.get('drawdown_20_pct'))} vs {fmt(r.get('previous_dd20'))}; future DOWN10 {r.get('down_hit_20')}")
                lines.append(f"| {symbol} | {category} | {r['date']} | {detail} |")
            else:lines.append(f'| {symbol} | {category} | — | No episode meets the fixed definition; no example fabricated. |')
    lines += ['', 'All qualifying cases (including training/descriptive examples) are retained in event-analysis.csv. A UP hit after REDUCE is not a proof of an erroneous risk assessment, especially if DOWN also hit. Late-warning labels use retrospective original event troughs only for evaluation. Gradual-HOLD rule is fixed in protocol.md; absence of a qualifying example is explicitly allowed.','',
        '## Dependence, uncertainty and limitations','',
        '- Calendar moving blocks of 40 sessions, sampled synchronously across stocks, preserve much of the 5/10/20-window overlap and common stock shocks. 399 resamples for metric/calibration intervals; 1999 for confirmatory paired differences; fixed seeds. Blocks20/60 and yearly metrics are exported. Stationarity over years is imperfect; 40-session blocks do not solve every regime dependence.',
        '- Effective N uses capped Bartlett/Newey–West variance of daily panel means, lag40, and never exceeds the date count. It is a diagnostic, not a guarantee of independent trials. Irregular state/score/calibration subsets do not receive an invented effective N: they show raw counts, dates, calendar blocks and support warnings. Sparse events and wide intervals preclude precise reliable probabilities.',
        '- Bootstrap conditions on frozen fitted estimators and this historical vintage; it does not include all training/selection uncertainty, establish causality or remove retrospective model-design bias. Holm applies only to the 18 primary incremental tests. Other stock/bin/horizon analyses are exploratory.',
        '- Historical provider prices/corporate actions/publication times are not independently attested point-in-time vintages. A common split-adjusted OHLC basis and conservative next-midnight availability are inherited; dividend total returns are not targets here. No source revision or exchange-calendar completeness claim is made.',
        '- Late September/October20-session forecasts often have unfinished outcomes at October22. october-diagnostic.csv retains all such forecasts with censoring; the research never substitutes observed partial hits or terminal values for completed horizons.',
        '- The protocol and historical v3 design were specified after past outcomes became observable. Even an apparent positive task requires a fresh reserved future holdout and additional instruments. No conclusion of live-trading readiness or investment effectiveness is supported.','',
        '## Figures and reproduction','',
        '![Downside reliability](reliability-down.png)','', '![Upside reliability](reliability-up.png)','',
        '![Forecast distributions](forecast-distributions.png)','',
        '`OPENBLAS_NUM_THREADS=1 python -m aae.research.risk_forecast_study` runs offline. forecast-daily.csv has one anchor/horizon/threshold row with both directions, all model probabilities, raw training-cell support, hit chronology, terminal returns and maturity. Training-only rows contain no pseudo-held-out forecasts. calibration.csv and baseline-comparison.csv meet the requested formats; supplementary metrics/state/score/fit-audit/block/year tables make uncertainty and purging auditable. validation.md records tests and unresolved historical checks. run.json hashes inputs/code/outputs.']
    extra=['## Stock-level reference task: DOWN10 within20','',
        '| Stock | Historical Brier | RV20 Brier | v3-state Brier | Technical Brier | Technical + v3 Brier |',
        '|---|---|---|---|---|---|']
    for symbol in SYMBOLS:
        group={r['model']:r for r in evaluation['metrics'] if r['symbol']==symbol and r['direction']=='down' and r['horizon']==20 and r['threshold_pct']==10}
        extra.append('| '+symbol+' | '+' | '.join(fmt(group[m]['brier'],4) for m in ('historical','volatility','v3_state','technical_combined','technical_plus_v3'))+' |')
    extra += ['', 'Lower Brier is better. A modest individual improvement is exploratory and does not establish the primary incremental criterion. Joint technical cells are sparse: inspect LOW_SUPPORT rates in the main table (especially technical_plus_v3), not only point scores. This study cannot rule out every alternative estimator of the same information.', '']
    at=lines.index('## State frequencies and numeric risk score')
    lines[at:at]=extra
    complete=[r for r in daily if r['role']=='OUT_OF_SAMPLE' and r['horizon']==20 and r['threshold_pct']==10 and r['complete']]
    both=sum(r['down_hit'] and r['up_hit'] for r in complete)
    ambiguous=sum(r['hit_order']=='UNKNOWN_INTRADAY' for r in complete)
    extra=[f'In the held-out 10%/20-session reference task, {both}/{len(complete)} daily anchors hit both barriers; {ambiguous} have unresolved same-day first-hit order. outcome-summary.csv also separates all other barrier tasks and their mean terminal returns. Forecast rows across horizons/thresholds/directions are repeated questions about the same paths, not independent observations.','']
    at=lines.index('## Dependence, uncertainty and limitations')
    lines[at:at]=extra
    (ROOT/'report.md').write_text('\n'.join(lines)+'\n')


def outcome_summary(daily):
    output=[]
    for role in ('TRAINING_DESCRIPTIVE_ONLY','OUT_OF_SAMPLE'):
        for symbol in ('ALL',*SYMBOLS):
            for h in HORIZONS:
                for t in THRESHOLDS:
                    rows=[r for r in daily if r['role']==role and (symbol=='ALL' or r['symbol']==symbol) and r['horizon']==h and r['threshold_pct']==t*100]
                    complete=[r for r in rows if r['complete']]
                    output.append(dict(role=role,symbol=symbol,horizon=h,threshold_pct=t*100,
                        n=len(rows),complete=len(complete),censored=len(rows)-len(complete),
                        down_hits=sum(r['down_hit'] for r in complete),up_hits=sum(r['up_hit'] for r in complete),
                        both_hits=sum(r['down_hit'] and r['up_hit'] for r in complete),
                        unknown_intraday_order=sum(r['hit_order']=='UNKNOWN_INTRADAY' for r in complete),
                        mean_terminal_return_pct=float(np.mean([r['terminal_return_pct'] for r in complete])) if complete else None))
    return output


def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    raw,features,labels,folds,manifest=load_inputs()
    daily,audit=forecasts(raw,features,labels,folds)
    print(json.dumps(dict(forecast_rows=len(daily),frozen_fits=len(audit))),flush=True)
    result=evaluate_forecasts(daily)
    event_rows=errors(daily,raw,features,folds)
    outputs={'outcome-summary.csv':outcome_summary(daily),'forecast-daily.csv':daily,'fit-audit.csv':audit,'metrics.csv':result['metrics'],
        'calibration.csv':result['calibration'],'baseline-comparison.csv':result['comparisons'],
        'state-probabilities.csv':result['states'],'score-probabilities.csv':result['scores'],
        'score-monotonicity.csv':result['monotonicity'],'year-metrics.csv':result['annual'],
        'block-sensitivity.csv':result['sensitivity'],'event-analysis.csv':event_rows,
        'october-diagnostic.csv':[r for r in daily if r['date']>='2026-09-01']}
    for name,rows in outputs.items():write_csv(ROOT/name,rows)
    plots(result,daily);report(result,event_rows,audit,daily)
    primary=[r for r in result['comparisons'] if r['primary']]
    paths=[Path(__file__),Path('aae/research/risk_forecast.py'),Path('aae/research/risk_forecast_statistics.py'),
        ROOT/'protocol.md',Path('aae/research/requirements-forecast.txt'),SOURCE/'run.json',Path('data/risk-signal-v3/manifest.json')]
    if Path('tests/test_risk_forecast.py').exists():paths.append(Path('tests/test_risk_forecast.py'))
    metadata=dict(schema_version=1,cutoff='2026-10-22',numpy_version=np.__version__,
        protocol_commit='8b22cf4',source_sha256={str(p):sha(p) for p in paths},
        frozen_v3_signal_sha256=sha(SOURCE/'daily-signals.jsonl.gz'),
        output_sha256={p.name:sha(p) for p in ROOT.iterdir() if p.name not in ('run.json','protocol.md')},
        counts={name:len(rows) for name,rows in outputs.items()},
        confirmatory_tasks=len(primary),tasks_meeting_incremental_criterion=sum(r['incremental_evidence'] for r in primary),
        historical_vintage_verified=False,signal_rules_changed=False,trades_simulated=False)
    (ROOT/'run.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(json.dumps(dict(counts=metadata['counts'],confirmed=metadata['tasks_meeting_incremental_criterion'])),flush=True)


if __name__=='__main__':main()
