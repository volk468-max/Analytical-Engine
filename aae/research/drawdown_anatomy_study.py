"""Event-first anatomy, deterministic controls and chronological hypothesis tests."""
import csv,gzip,hashlib,json
from collections import Counter,defaultdict
from datetime import datetime,timedelta,timezone
from pathlib import Path
import numpy as np
from aae.backtest.simulator import Bar,utc
from aae.backtest.cli import write_csv
from .risk_v3_features import load_pack
from .risk_signal_v3 import evaluate,catalogue as risk_catalogue
from .drawdown_anatomy import PRIMARY,EXTRA,SEMIS,OFFSETS,catalogue,build_features,sector_features,hypotheses,flags,future_label
from .drawdown_anatomy_models import MODELS,fit_predict
from .risk_forecast_statistics import block_counts,ci,paired_difference,holm,effective_n,metric_samples

ROOT=Path('reports/historical-drawdown-anatomy');DATA=Path('data/historical-drawdown-anatomy');SOURCE=Path('reports/risk-signal-v3')


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_inputs():
    bars,markets,old=load_pack();manifest=json.loads((DATA/'manifest.json').read_text())
    for name,h in manifest['artifact_sha256'].items():
        if sha(DATA/name)!=h:raise ValueError('Supplemental checksum: '+name)
    if sha('data/risk-signal-v3/manifest.json')!=manifest['inherited_manifest_sha256']:raise ValueError('Changed inherited manifest')
    source=json.loads((SOURCE/'run.json').read_text())
    for name,h in source['source_sha256'].items():
        p=Path(name)
        if not p.exists() and '/aae/' in name:p=Path('aae/'+name.split('/aae/',1)[1])
        if sha(p)!=h:raise ValueError('Changed v3 module/source')
    for name in ('daily-signals.jsonl.gz','fold-selection.csv'):
        if sha(SOURCE/name)!=source['output_sha256'][name]:raise ValueError('Changed frozen v3 output')
    volumes=defaultdict(dict)
    for path in (Path('data/risk-signal-v3/bars.csv'),DATA/'bars.csv'):
        for r in csv.DictReader(path.open()):
            if r['price_basis']!='provider_split_adjusted_ohlc':raise ValueError('Mixed price basis')
            volumes[r['symbol']][r['open_at'][:10]]=float(r['volume'])
            if path==DATA/'bars.csv':bars.append(Bar(r['symbol'],r['open_at'],r['close_at'],r['available_at'],*[float(r[k]) for k in ('open','high','low','close')],r['source'],False))
    stocks={s:sorted([b for b in bars if b.symbol==s],key=lambda b:b.close_at) for s in (*PRIMARY,*EXTRA)}
    qqq=sorted([b for b in bars if b.symbol=='QQQ'],key=lambda b:b.close_at);sox=sorted([b for b in bars if b.symbol=='^SOX'],key=lambda b:b.close_at)
    calendar=[b.close_at.date().isoformat() for b in qqq];rates=[]
    for row in json.loads((DATA/'rates.json').read_text()):
        after=[b for b in qqq if b.close_at.date().isoformat()>row['date']]
        if len(after)<2:continue
        rates.append(dict(row,observed_at=row['date']+'T20:00:00+00:00',available_at=after[1].available_at.isoformat()))
    quality=[]
    for symbol,series in stocks.items():
        entry=next((e for e in manifest['sources']+old['sources'] if e['symbol']==symbol),None)
        if not series:
            quality.append(dict(symbol=symbol,status='DATA_UNAVAILABLE',reason='Source unavailable'));continue
        if any(b.close_at.date().isoformat()>'2026-10-22' for b in series):raise ValueError('Future session')
        if len({b.close_at.date() for b in series})!=len(series):raise ValueError('Duplicate source session')
        actions=(entry or {}).get('corporate_actions',(entry or {}).get('reported_corporate_actions',{}))
        raw_path=(DATA if symbol in EXTRA else Path('data/risk-signal-v3'))/entry['raw_file']
        raw=json.loads(raw_path.read_text())['chart']['result'][0]
        if raw.get('events',{})!=actions:raise ValueError('Action metadata mismatch')
        by_date={datetime.fromtimestamp(t,timezone.utc).date().isoformat():i for i,t in enumerate(raw['timestamp'])}
        for b in series:
            i=by_date[b.close_at.date().isoformat()]
            if any(getattr(b,k)!=raw['indicators']['quote'][0][k][i] for k in ('open','high','low','close')):raise ValueError('Raw OHLC mismatch')
        splits=[]
        for split in actions.get('splits',{}).values():
            date=datetime.fromtimestamp(split['date'],timezone.utc).date().isoformat()
            i=next((i for i,b in enumerate(series) if b.close_at.date().isoformat()==date),None)
            if i is not None and i>0:
                ratio=series[i].open/series[i-1].close
                if not .4<ratio<2.5:raise ValueError('Possible unadjusted split jump: '+symbol)
                splits.append(dict(date=date,ratio=split['splitRatio'],adjusted_open_ratio=ratio,no_second_split_applied=True))
        dates={b.close_at.date().isoformat() for b in series}
        expected=[d for d in calendar if series[0].close_at.date().isoformat()<=d<=series[-1].close_at.date().isoformat()]
        quality.append(dict(symbol=symbol,status='RETROSPECTIVE_NOT_VERIFIED_PIT',source=entry['url'],retrieved_at=entry.get('retrieved_at',old['retrieved_at']),
            first=series[0].close_at.date().isoformat(),last=series[-1].close_at.date().isoformat(),bars=len(series),
            missing_vs_qqq=len(set(expected)-dates),short_initial_history=series[0].close_at.date().isoformat()>'2020-01-02',
            full200_first_date=series[199].close_at.date().isoformat() if len(series)>=200 else None,
            corporate_actions=json.dumps(splits,sort_keys=True),ohlc_raw_reconciled=True,
            price_basis='provider_split_adjusted_ohlc; price returns, not dividend total returns',
            availability='next UTC midnight assumed; early-close publications conservatively delayed',
            original_publication_archive=False,survivor_universe=True))
    for symbol in ('QQQ','^SOX','VIX','DGS10'):
        e=next((e for e in manifest['sources']+old['sources'] if e['symbol']==symbol),{})
        quality.append(dict(symbol=symbol,status=e.get('status','DATA_UNAVAILABLE'),source=e.get('url'),retrieved_at=e.get('retrieved_at',old['retrieved_at']),
            availability=e.get('publication_assumption','next UTC midnight assumed'),original_publication_archive=False))
    for symbol in ('EPS_REVISIONS','REVENUE_REVISIONS','EXPECTED_PE','GUIDANCE_VINTAGES','EARNINGS_NEWS_ARCHIVE','MARKET_WIDE_BREADTH','HISTORICAL_SECTOR_MEMBERSHIP'):
        quality.append(dict(symbol=symbol,status='DATA_UNAVAILABLE',reason='No original timestamped historical archive obtained; no present-day substitution'))
    folds={int(r['test_year']):r for r in csv.DictReader((SOURCE/'fold-selection.csv').open()) if r['variant']=='C'}
    archived={}
    with gzip.open(SOURCE/'daily-signals.jsonl.gz','rt') as stream:
        for line in stream:
            s=json.loads(line)
            if s['mode']=='walk_forward' and s['variant']=='C':archived[(s['symbol'],s['date'])]=s
    return stocks,volumes,qqq,sox,markets,rates,quality,folds,archived


def add_v3(symbol,rows,folds,archived):
    configs={c.name:c for c in risk_catalogue()};previous=None
    for i,r in enumerate(rows):
        year=int(r['date'][:4]);name=folds[max(2023,year)]['configuration'] if year<=2026 else 'sensitive'
        values=dict(close=r['close'],ma20=r['ma20'],ma50=r['ma50'],ma200=r['ma200'],drawdown_20_pct=r['current_drawdown20'],drawdown_60_pct=r['current_drawdown60'],
            return_5_pct=r['return5'],return_10_pct=r['return10'],fall_acceleration_5_pp=r['fall_acceleration5'],
            ma20_slope_5_pct=r['ma20_slope5'],ma50_slope_5_pct=r['ma50_slope5'],ma20_slope_change_pp=r['ma20_slope_change5'],ma50_slope_change_pp=r['ma50_slope_change5'],
            rsi14=r['rsi14'],relative_return_qqq20_pp=r['relative_qqq20'],relative_return_sox20_pp=r['relative_sox20'],
            rv20_pct=r['rv20'],rv60_pct=r['rv60'],rv20_change_5_ratio=r['rv_change5'],vix=r['vix'],support=r['support120'])
        quality=dict(quote_observed_at=r['observed_at'],quote_available_at=r['decision_at'],qqq_observed_at=r['qqq_observed_at'],qqq_available_at=r['qqq_available_at'],
            sox_observed_at=r['sox_observed_at'],sox_available_at=r['sox_available_at'],vix_observed_at=r['vix_observed_at'],vix_available_at=r['vix_available_at'])
        signal=evaluate(symbol,r['decision_at'],values,quality,variant='C',config=configs[name],previous=previous);previous=signal
        r.update(v3_state=signal['risk_level'],v3_score=signal['score'],v3_profile=name,v3_data_status=signal['data_status'])
        old=archived.get((symbol,r['date']))
        if old and (old['risk_level']!=signal['risk_level'] or old['score']!=signal['score']):raise ValueError('v3 replay mismatch: '+symbol+' '+r['date'])


def controls_and_snapshots(events,features,bars):
    cohort=[];snapshots=[];matches=[]
    for symbol,rows in features.items():
        dates=[r for r in rows if r['date']>='2021-01-01']
        for j,r in enumerate(dates):
            if j%20:continue
            cohort.append(dict(r,**future_label(bars[symbol],r['index'],60),cohort_id=symbol+'-'+r['date'],calendar_block=(int(r['date'][:4])-2021)//2))
    for event in events:
        rows=features[event['symbol']]
        for offset in OFFSETS:
            index=event['onset_index']-offset
            if index<0:
                snapshots.append(dict(episode_id=event['episode_id'],symbol=event['symbol'],offset=offset,status='PREHISTORY_UNAVAILABLE'));continue
            r=rows[index]
            snap=dict(r,episode_id=event['episode_id'],event_onset=event['onset_date'],event_depth=event['depth_pct'],event_severity=event['severity'],offset=offset,status='OBSERVED_CAUSAL_SNAPSHOT')
            snapshots.append(snap)
            block=(int(r['date'][:4])-2021)//2
            for group in ('LARGE_CORRECTION','SMALL_CORRECTION','GROWTH','SIDEWAYS'):
                candidates=[c for c in cohort if c['symbol']==r['symbol'] and c['market_regime']==r['market_regime'] and c['calendar_block']==block and c['control_class']==group and (block!=0 or (c['label_available_at'] and utc(c['label_available_at'])<=utc('2023-01-01T00:00:00+00:00'))) and abs(c['index']-index)>20]
                candidates.sort(key=lambda c:(abs((datetime.fromisoformat(c['date'])-datetime.fromisoformat(r['date'])).days),c['date']))
                if not candidates:matches.append(dict(episode_id=event['episode_id'],symbol=r['symbol'],offset=offset,snapshot_date=r['date'],control_class=group,match_status='NO_MATCH'))
                for c in candidates[:3]:matches.append(dict(c,episode_id=event['episode_id'],offset=offset,snapshot_date=r['date'],match_status='MATCHED'))
    reuse=Counter(c['cohort_id'] for c in matches if c['match_status']=='MATCHED')
    for c in matches:
        if c['match_status']=='MATCHED':c.update(reuse_count=reuse[c['cohort_id']],inverse_reuse_weight=1/reuse[c['cohort_id']])
    return cohort,snapshots,matches


def forecast(features,bars,folds,*,path_target=False):
    predictions=[];audit=[]
    for symbol,rows in features.items():
        eligible=[r for r in rows if r['date']>='2021-01-01']
        for h in (20,60):
            labelled=[dict(r,**future_label(bars[symbol],r['index'],h),horizon=h) for r in eligible]
            if path_target and h!=60:continue
            for r in labelled:
                r['target_kind']='FORWARD_PATH_DRAWDOWN' if path_target else 'ANCHOR_DOWNSIDE'
                if path_target:r['target']=r['path_target']
            for year in (2023,2024,2025,2026):
                cutoff=f'{year}-01-01T00:00:00+00:00'
                train=[r for r in labelled if r['date']<str(year)+'-01-01']
                test=[dict(r) for r in labelled if r['date'].startswith(str(year))]
                for model in MODELS:
                    p,fit=fit_predict(train,test,model,cutoff)
                    audit.append(dict(fit,target_kind='FORWARD_PATH_DRAWDOWN' if path_target else 'ANCHOR_DOWNSIDE',symbol=symbol,horizon=h,test_year=year,profile=folds[year]['configuration'],
                        excluded_unmatured=sum(r['target'] is None or utc(r['label_available_at'])>utc(cutoff) for r in train)))
                    for r,value in zip(test,p):r['p_'+model]=value
                predictions.extend(test)
    return predictions,audit


def sample_panel(rows,calendar,length=120,resamples=399,seed=818):
    first=min(r['date'] for r in rows);last=max(r['date'] for r in rows)
    dates=[d for d in calendar if first<=d<=last]
    lookup={d:i for i,d in enumerate(dates)};index=np.array([lookup[r['date']] for r in rows])
    counts=block_counts(len(dates),resamples,length,seed)
    return index,counts,len(dates)


def association(rows,feature,calendar):
    rows=[r for r in rows if r.get('target') is not None and r.get(feature) is not None]
    if not rows:return dict(n=0,status='DATA_UNAVAILABLE')
    index,counts,N=sample_panel(rows,calendar)
    w=np.vstack([np.ones(len(rows)),counts[:,index]])
    y=np.array([r['target'] for r in rows],float);x=np.array([bool(r[feature]) for r in rows],float)
    n1=w@x;n0=w@(1-x);a=w@(x*y);b=w@((1-x)*y);total=w@y
    with np.errstate(divide='ignore',invalid='ignore'):
        p1=a/n1;p0=b/n0;rr=p1/p0;recall=a/total;false=1-p1;logrr=np.log(rr)
    low,high=ci(rr[1:]);rlo,rhi=ci(p1[1:]);rl,ru=ci(recall[1:])
    p=(1+int(np.sum(logrr[1:]-logrr[0]>=logrr[0])))/(len(counts)+1) if np.isfinite(logrr[0]) else None
    meaningful=int(x.sum())>=20 and int((x*y).sum())>=10 and int(((1-x)*y).sum())>=10 and N//120>=5
    return dict(n=len(y),n_dates=len(set(r['date'] for r in rows)),calendar_blocks_120=N//120,
        effective_n_hac=effective_n(y,index,N,lag=120),exposed_n=int(x.sum()),exposed_events=int((x*y).sum()),
        event_rate=float(y.mean()),risk_exposed=float(p1[0]) if np.isfinite(p1[0]) else None,
        risk_unexposed=float(p0[0]) if np.isfinite(p0[0]) else None,
        risk_exposed_low=rlo,risk_exposed_high=rhi,risk_ratio=float(rr[0]) if np.isfinite(rr[0]) else None,
        risk_ratio_low=low,risk_ratio_high=high,recall=float(recall[0]) if np.isfinite(recall[0]) else None,
        recall_low=rl,recall_high=ru,false_warning_share=float(false[0]) if np.isfinite(false[0]) else None,
        p_exploratory_risk_increase=p,status='RESEARCH_DEPENDENT_ESTIMATE' if meaningful else 'LOW_SUPPORT')


def event_coverage(events,features,hypothesis):
    found=[];eligible=0;covered=0;left=0;major=0;major_found=0
    for e in events:
        if e['onset_date']<'2021-01-01':continue
        prior=features[e['symbol']][max(0,e['onset_index']-60):e['onset_index']]
        known=[r for r in prior if r.get(hypothesis) is not None]
        if not known:continue
        eligible+=1;active=[r for r in known if r[hypothesis]]
        if e['depth_pct']>25:major+=1;major_found+=bool(active)
        if active:
            covered+=1;lead=e['onset_index']-active[0]['index'];found.append(lead);left+=lead==60
    return dict(catalog_events_with_feature=eligible,catalog_events_preceded=covered,
        catalog_coverage=covered/eligible if eligible else None,major_gt25_events=major,
        major_gt25_preceded=major_found,median_observed_lead_sessions=float(np.median(found)) if found else None,
        lead_left_censored_at_60=left)


def evaluate_study(predictions,cohort,events,features,calendar,discovery_events):
    comparisons=[];metrics=[];cross=[];sensitivity=[];hypothesis_rows=[];single=[]
    groups={'PRIMARY':PRIMARY,'EXPANDED':EXTRA,'ALL':(*PRIMARY,*EXTRA)}
    for group,symbols in groups.items():
        for h in ('H1','H2','H3','H4','H5'):
            for period,start,end in (('DISCOVERY','2021-01-01','2022-12-31'),('RESEARCH_OOS','2023-01-01','2026-10-22')):
                period_cutoff='2023-01-01T00:00:00+00:00' if period=='DISCOVERY' else '2026-10-23T00:00:00+00:00'
                rows=[r for r in cohort if r['symbol'] in symbols and start<=r['date']<=end and r['label_available_at'] and utc(r['label_available_at'])<=utc(period_cutoff)]
                period_events=discovery_events if period=='DISCOVERY' else events
                ev=[e for e in period_events if e['symbol'] in symbols and start<=e['onset_date']<=end]
                hypothesis_rows.append(dict(hypothesis=h,group=group,period=period,
                    **association(rows,h,calendar),**event_coverage(ev,features,h)))
    for flag in next(iter(features.values()))[-1]['flags']:
        rows=[dict(r,value=r['flags'][flag]) for r in cohort if r['symbol'] in PRIMARY and r['date']>='2023-01-01']
        single.append(dict(feature=flag,**association(rows,'value',calendar)))
    available=[r for r in single if r.get('p_exploratory_risk_increase') is not None]
    for r,p in zip(available,holm([r['p_exploratory_risk_increase'] for r in available])):r['holm_exploratory']=p
    for group,symbols in [*groups.items(),*((s,(s,)) for s in features)]:
        for horizon in (20,60):
            base=[r for r in predictions if r['symbol'] in symbols and r['horizon']==horizon and r['target'] is not None]
            for model in MODELS:
                rows=[r for r in base if r.get('p_'+model) is not None]
                if not rows:continue
                y=np.array([r['target'] for r in rows]);p=np.array([r['p_'+model] for r in rows])
                vals=metric_samples(y,p,np.ones((1,len(y))))
                index,counts,N=sample_panel(rows,calendar)
                metrics.append(dict(group=group,horizon=horizon,model=model,n=len(rows),n_dates=len(set(r['date'] for r in rows)),
                    effective_n_hac=effective_n(y,index,N,lag=120),calendar_blocks_120=N//120,
                    **{k:float(v[0]) if np.isfinite(v[0]) else None for k,v in vals.items()}))
            for hypothesis in ('H1','H2','H3','H5'):
                model='joint_'+hypothesis;rows=[r for r in base if r.get('p_'+model) is not None and r.get('p_joint') is not None]
                if not rows:continue
                primary=group=='PRIMARY' and horizon==60
                index,counts,N=sample_panel(rows,calendar,resamples=1999 if primary else 399)
                y=np.array([r['target'] for r in rows],float);p=np.array([r['p_'+model] for r in rows]);q=np.array([r['p_joint'] for r in rows])
                rec=dict(group=group,horizon=horizon,hypothesis=hypothesis,n=len(rows),primary=primary,
                    **paired_difference(y,p,q,index,N,counts),relative_brier_improvement_pct=(np.mean((q-y)**2)-np.mean((p-y)**2))/np.mean((q-y)**2)*100)
                comparisons.append(rec)
                if primary:
                    for length in (60,120,180):
                        block=counts if length==120 else block_counts(N,399,length,seed=818)
                        sensitivity.append(dict(hypothesis=hypothesis,block_length=length,**paired_difference(y,p,q,index,N,block)))
                for year in (2023,2024,2025,2026):
                    take=[r for r in rows if r['date'].startswith(str(year))]
                    if take:
                        yy=np.array([r['target'] for r in take]);pp=np.array([r['p_'+model] for r in take]);qq=np.array([r['p_joint'] for r in take])
                        exposed=[r for r in take if r[hypothesis]];unexposed=[r for r in take if not r[hypothesis]]
                        pe=float(np.mean([r['target'] for r in exposed])) if exposed else None
                        pu=float(np.mean([r['target'] for r in unexposed])) if unexposed else None
                        cross.append(dict(group=group,horizon=horizon,hypothesis=hypothesis,year=year,n=len(take),
                            exposed_n=len(exposed),exposed_events=sum(r['target'] for r in exposed),
                            risk_ratio=pe/pu if pe is not None and pu else None,
                            false_warning_share=1-pe if pe is not None else None,
                            recall=sum(r['target'] for r in exposed)/sum(r['target'] for r in take) if any(r['target'] for r in take) else None,
                            inference='YEAR_DESCRIPTIVE_FEW_BLOCKS',
                            **event_coverage([e for e in events if e['symbol'] in symbols and e['onset_date'].startswith(str(year))],features,hypothesis),
                            brier_difference=float(np.mean((pp-yy)**2-(qq-yy)**2)),risk_exposed=float(np.mean([r['target'] for r in take if r[hypothesis]])) if any(r[hypothesis] for r in take) else None))
                shallow=[r for r in rows if r['expanding_drawdown']>=-5]
                if shallow:
                    yy=np.array([r['target'] for r in shallow]);pp=np.array([r['p_'+model] for r in shallow]);qq=np.array([r['p_joint'] for r in shallow])
                    comparisons.append(dict(group=group,horizon=horizon,hypothesis=hypothesis,n=len(shallow),primary=False,
                        subset='NEAR_HIGH_DD_LE5',brier_difference=float(np.mean((pp-yy)**2-(qq-yy)**2))))
    primary=[r for r in comparisons if r.get('primary')]
    for r,p in zip(primary,holm([r['brier_p_one_sided'] for r in primary])):
        blocks=[b for b in sensitivity if b['hypothesis']==r['hypothesis']]
        others=[x for x in comparisons if x['group'] in PRIMARY and x['horizon']==60 and x['hypothesis']==r['hypothesis'] and not x.get('subset')]
        expanded=next((x for x in comparisons if x['group']=='EXPANDED' and x['horizon']==60 and x['hypothesis']==r['hypothesis'] and not x.get('subset')),None)
        stable=all(b['brier_difference_high'] is not None and b['brier_difference_high']<0 for b in blocks)
        r.update(holm_primary=p,stable_blocks=stable,primary_stocks_improved=sum(x['brier_difference']<0 for x in others),
            expanded_direction_matches=bool(expanded and expanded['brier_difference']<0))
        r['provisionally_supported']=p<.05 and r['brier_difference_high']<0 and r['relative_brier_improvement_pct']>=1 and stable and r['primary_stocks_improved']>=2 and r['expanded_direction_matches']
    return dict(hypotheses=hypothesis_rows,comparisons=comparisons,metrics=metrics,cross=cross,sensitivity=sensitivity,single=single)


def matched_summary(snapshots,matches):
    output=[]
    for group,symbols in (('ALL',(*PRIMARY,*EXTRA)),('PRIMARY',PRIMARY),*((s,(s,)) for s in PRIMARY)):
        for name in ('H1','H2','H3','H4','H5'):
            for offset in OFFSETS:
                cases=[r for r in snapshots if r['symbol'] in symbols and r.get(name) is not None and r['offset']==offset]
                for category in ('LARGE_CORRECTION','SMALL_CORRECTION','GROWTH','SIDEWAYS'):
                    controls=[r for r in matches if r['symbol'] in symbols and r['match_status']=='MATCHED' and r['offset']==offset and r['control_class']==category and r.get(name) is not None]
                    w=sum(r['inverse_reuse_weight'] for r in controls)
                    output.append(dict(group=group,hypothesis=name,offset=offset,control_class=category,
                        case_n=len(cases),case_prevalence=sum(r[name] for r in cases)/len(cases) if cases else None,
                        matched_n=len(controls),unique_controls=len({r['cohort_id'] for r in controls}),
                        weighted_control_prevalence=sum(r[name]*r['inverse_reuse_weight'] for r in controls)/w if w else None,
                        inference='DESCRIPTIVE_REUSED_CONTROLS_NOT_INDEPENDENT'))
    return output


def path_comparison(predictions,calendar):
    output=[]
    for group,symbols in (('PRIMARY',PRIMARY),('EXPANDED',EXTRA),*((s,(s,)) for s in (*PRIMARY,*EXTRA))):
        for h in ('H1','H2','H3','H5'):
            rows=[r for r in predictions if r['symbol'] in symbols and r['target'] is not None and r.get('p_joint_'+h) is not None and r.get('p_joint') is not None]
            if not rows:continue
            index,counts,N=sample_panel(rows,calendar)
            y=np.array([r['target'] for r in rows]);p=np.array([r['p_joint_'+h] for r in rows]);q=np.array([r['p_joint'] for r in rows])
            output.append(dict(group=group,hypothesis=h,target_kind='FORWARD_PATH_DRAWDOWN',n=len(rows),
                event_rate=float(y.mean()),**paired_difference(y,p,q,index,N,counts),
                relative_brier_improvement_pct=(np.mean((q-y)**2)-np.mean((p-y)**2))/np.mean((q-y)**2)*100,
                inference='POST_PRIMARY_EXPLORATORY_TARGET_SENSITIVITY'))
    primary=[r for r in output if r['group']=='PRIMARY']
    for row,p in zip(primary,holm([r['brier_p_one_sided'] for r in primary])):row['holm_exploratory']=p
    return output


def flatten(rows):
    output=[]
    for row in rows:
        r={k:v for k,v in row.items() if k!='flags'}
        r.update({'flag_'+k:v for k,v in row.get('flags',{}).items()});output.append(r)
    return output


def plots(features,snapshots,matches,result):
    import os
    os.environ.setdefault('MPLCONFIGDIR','/tmp/alpha-anatomy-mpl');os.environ.setdefault('XDG_CACHE_HOME','/tmp/alpha-anatomy-cache')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(3,1,figsize=(12,10))
    for ax,symbol in zip(axes,PRIMARY):
        rows=[r for r in features[symbol] if r['date']>='2021-01-01']
        ax.fill_between([datetime.fromisoformat(r['date']) for r in rows],[r['expanding_drawdown'] for r in rows],0,alpha=.5)
        ax.set_title(symbol+' drawdown from observed-history closing high');ax.set_ylabel('%');ax.grid(alpha=.2)
    fig.autofmt_xdate();fig.tight_layout();fig.savefig(ROOT/'historical-drawdowns.png',dpi=130);plt.close(fig)
    keys=('return60','distance_ma50','relative_qqq20','rv20','rsi14','sector_weak_fraction')
    fig,axes=plt.subplots(2,3,figsize=(14,8))
    for ax,key in zip(axes.flat,keys):
        cases=[r[key] for r in snapshots if r['symbol'] in PRIMARY and r.get(key) is not None and r['offset']==20]
        ax.hist(cases,bins=15,density=True,histtype='step',label='Event -20 sessions',lw=2)
        for group in ('SMALL_CORRECTION','GROWTH','SIDEWAYS'):
            controls=[r for r in matches if r['symbol'] in PRIMARY and r['match_status']=='MATCHED' and r.get(key) is not None and r['offset']==20 and r['control_class']==group]
            if controls:ax.hist([r[key] for r in controls],weights=[r['inverse_reuse_weight'] for r in controls],bins=15,density=True,histtype='step',label=group)
        ax.set_title(key);ax.legend(fontsize=7);ax.grid(alpha=.2)
    fig.suptitle('Retrospective distributions; reused controls are descriptive, not independent trials')
    fig.tight_layout();fig.savefig(ROOT/'feature-control-distributions.png',dpi=130);plt.close(fig)
    rows=[r for r in result['comparisons'] if r.get('primary')]
    fig,ax=plt.subplots(figsize=(9,5))
    for i,r in enumerate(rows):
        point=r['brier_difference'];lo=r['brier_difference_low'];hi=r['brier_difference_high']
        ax.errorbar(point,i,xerr=[[max(0,point-lo)],[max(0,hi-point)]],fmt='o',label=r['hypothesis'])
    ax.axvline(0,color='black',ls='--');ax.set_yticks(range(len(rows)),[r['hypothesis'] for r in rows]);ax.set_xlabel('Added-hypothesis Brier minus joint baseline (negative better)')
    ax.set_title('Primary60-session target; paired120-session block95% intervals');ax.grid(alpha=.2)
    fig.tight_layout();fig.savefig(ROOT/'hypothesis-incremental.png',dpi=130);plt.close(fig)


def fmt(x,n=3):return '—' if x is None else f'{x:.{n}f}'


def report(events,snapshots,matches,result,coverage,robustness,path_results,episode_hypotheses):
    primary=[r for r in result['comparisons'] if r.get('primary')]
    supported=[r for r in primary if r['provisionally_supported']]
    lines=['# Historical Drawdown Anatomy v1','',
        '**Research only: no trades, position sizing, signal edits or production integration.** Event definitions and H1–H5 were frozen before association tests (protocol commit c8d0b6f). Catalogue construction precedes feature associations.','',
        '## Data and limits of historical interpretation','',
        'Primary AMD/NVDA/MU plus15 requested additional survivors,2021–22 October2026,2020 warmup. Frozen primary/QQQ/SOX/CBOE VIX data from PR#5 are unchanged. Additional Yahoo OHLCV/action responses and FRED DGS10 were retrieved for this study; sources, retrieval times, completeness, corporate actions, publication assumptions and SHA-256 are in data-coverage.csv and data/historical-drawdown-anatomy/manifest.json. Prices are one provider split-adjusted basis, not dividend total returns; splits are never applied twice.','',
        'Every feature uses a published prefix. Price availability is assumed next UTC midnight (early closes delayed); DGS10 is assumed known only after two subsequent QQQ sessions and next midnight. These are conservative scheduling assumptions, NOT independently attested original publication vintages. No present-day EPS/PE/guidance substitutes are used. Market-wide breadth, revision vintages and historical sector membership remain unavailable (missing-data.md).','',
        'PLTR begins September2020 and lacks early200-session warmup; long-window features stay missing until observable. Missing-control matches stay NO_MATCH. The selected names all survived to2026, so cross-stock findings are conditional on a survivor basket and cannot establish a survivorship-free sector law. Sector concentration is a fixed11-semiconductor peer proxy, excluding the target, not whole-market breadth.','',
        '2021–2022 are discovery/training; annual2023–2026 probabilities use only fully matured outcomes at each Jan1 cutoff. The same2021–2026 history has already been studied repeatedly: chronological testing prevents computational look-ahead but is not pristine independent confirmation. Newly added stocks check transport of a frozen specification, not historically blind hypothesis discovery.','',
        '## Catalogue and nested episodes','',
        'Closing high-water mark starts at the first available2020 observation. It is an observable-history high, not a verified lifetime ATH. A decline starts on the first lower close after that peak; all nested falls belong to the same episode until the old peak is genuinely recovered. Threshold dates use closes. Severity buckets are[10,15),[15,25],>25%. Open and left-censored events remain. Peaks/troughs describe labels only, never predictor inputs.','',
        '| Stock | Events | 10–15% | 15–25% | >25% | Open |', '|---|---|---|---|---|---|']
    for symbol in (*PRIMARY,*EXTRA):
        rows=[e for e in events if e['symbol']==symbol]
        lines.append(f"| {symbol} | {len(rows)} | {sum(e['severity']=='10-15' for e in rows)} | {sum(e['severity']=='15-25' for e in rows)} | {sum(e['severity']=='>25' for e in rows)} | {sum(e['status']=='OPEN_AT_CUTOFF' for e in rows)} |")
    lines += ['', 'Catalogue sensitivities use high/low extrema,98% recovery or12% inclusion instead of10%. All variants are exported; no definition is selected for a favorable result. high/low is a daily descriptive sensitivity with close-confirmed recovery, not an assumed intraday path. See episode-sensitivity.csv; differences in count/duration warn against treating one segmentation as ground truth.','',
        '## Presnapshots and mandatory controls','',
        'Each event has60/40/20/10/5-session causal snapshots before the first declining session. Confirmed significant lows require five already-observed sessions on each side and a preceding20-session decline of at least5%; an eventual event trough is never reused as an earlier feature. Features include growth/MA distances, relative strength/change, RV/RSI/slopes/volume/negative sessions/acceleration/correlation, lagged VIX/yields and peer deterioration.','',
        'Controls come from a fixed every20th-session cohort, classified using a complete60-session future into large/small correction, continuing growth, sideways or mixed. Matching is same stock, causal QQQ regime and two-year block, nearest dates excluding20 sessions around the snapshot, up to3 per category. Selection never ranks feature values. Reuse is explicit and inverse-weighted; controls are descriptive, not population probabilities or independent trial counts. Cohort-all.csv preserves mixed/censored dates too.','',
        f"Snapshots: {len(snapshots)}; matched/control records: {len(matches)}, of which {sum(r['match_status']=='NO_MATCH' for r in matches)} explicitly unmatched. Matched rates by offset/category are in matched-control-comparison.csv; population risk/false-warning rates use the whole predeclared cohort, never case-enriched matches.",'',
        '## Five prespecified candidate patterns','',
        '| Hypothesis | Exact definition | Status |', '|---|---|---|']
    definitions={'H1':'ret60>=20%, MA50 extension>=10%, RV20/RV60>=1.10',
        'H2':'20-session relative weakness<=-5pp versus a still-rising QQQ or SOX',
        'H3':'>=50% peers falling over10 sessions and underperforming QQQ by>=3pp;>=5 peers',
        'H4':'Original historical EPS/guidance downgrades',
        'H5':'QQQ belowMA50, rising market RV, VIX stress/change and abs lagged yield20 change>=25bp'}
    for h in ('H1','H2','H3','H4','H5'):
        r=next((r for r in primary if r['hypothesis']==h),None)
        status='CANNOT_TEST: no original fundamental expectation vintages' if h=='H4' else 'DATA_UNAVAILABLE' if not r else 'PROVISIONAL_RESEARCH_SUPPORT' if r['provisionally_supported'] else 'INCREMENTAL_ADVANTAGE_NOT_CONFIRMED'
        lines.append(f'| {h} | {definitions[h]} | {status} |')
    lines += ['', 'These five are the user-specified candidates, not a post-hoc ranking of winners. All18 single flags are also retained with exploratory multiplicity adjustment. Descriptive recurrence before a handful of falls is not confirmation.','',
        '## Primary incremental probability test','',
        'Target: any future close>=10% below current close within60 subsequent sessions; secondary20. This measures anchor-price risk, not a future peak known in advance. Near-high/DD<=5% subsets distinguish precursors from ongoing declines. Baselines: historical probability, RV20, currentDD60, relativeQQQ/SOX, unchanged v3 state, and their joint fixed-ridge logistic model. Add exactly one H1/H2/H3/H5 flag, with training-only standardization and ridge1.','',
        '| Pattern | Δ Brier [95% blockCI] | Relative improvement % | Holm p | Improved primary stocks | Same direction expanded | Stable blocks |',
        '|---|---|---|---|---|---|---|']
    for r in primary:
        lines.append(f"| {r['hypothesis']} | {fmt(r['brier_difference'],4)} [{fmt(r['brier_difference_low'],4)}, {fmt(r['brier_difference_high'],4)}] | {fmt(r['relative_brier_improvement_pct'],2)} | {fmt(r['holm_primary'],4)} | {r['primary_stocks_improved']}/3 | {r['expanded_direction_matches']} | {r['stable_blocks']} |")
    lines += ['', f"**{len(supported)}/{len(primary)} testable patterns meet the full predefined support criterion.** "+('Any positive finding is provisional and requires a fresh future holdout.' if supported else 'No tested combination establishes statistically and practically significant incremental prediction under this specification.'),'',
        'Primary criterion: Holm p<.05 across testable hypotheses, negative95% paired Brier interval,>=1% relative improvement, negative intervals at60/120/180-session blocks, improvement in>=2/3 primary stocks and matching expanded direction. All shocks on a sampled date stay together across stocks.1999 primary resamples,399 association/exploratory resamples. There are few120-session blocks in four test years: effective N and broad intervals matter more than raw daily counts. Bootstrap conditions on fitted models; it does not remove research/design bias or include all training uncertainty.','',
        '## Frequency, false warnings and lead time: primary stocks','',
        '| Pattern | Exposed anchors / hits | Preceded catalogue events | >25% events preceded | Observed median lead | Cohort observed hit fraction | Risk ratio [95%CI] | False warnings | Support |',
        '|---|---|---|---|---|---|---|---|---|']
    for r in result['hypotheses']:
        if r['group']=='PRIMARY' and r['period']=='RESEARCH_OOS':
            lines.append('| '+' | '.join([r['hypothesis'],str(r.get('exposed_n',0))+' / '+str(r.get('exposed_events',0)),f"{r['catalog_events_preceded']}/{r['catalog_events_with_feature']}",f"{r['major_gt25_preceded']}/{r['major_gt25_events']}",fmt(r['median_observed_lead_sessions'],1),fmt(r.get('risk_exposed')),f"{fmt(r.get('risk_ratio'))} [{fmt(r.get('risk_ratio_low'))}, {fmt(r.get('risk_ratio_high'))}]",fmt(r.get('false_warning_share')),r['status']])+' |')
    lines += ['', 'Event coverage counts each main episode once; exposures strictly precede onset. Leads are among detected events and are left-censored when already active at the60-session window boundary. They describe warning opportunities, not proof the exact onset was forecast. Cohort risk ratios/recall/false warnings use fully observed60-session labels. Sparse conditions or zero denominators are unavailable/LOW_SUPPORT, never replaced by a confident exact probability.','']
    for symbol in PRIMARY:
        rows=[e for e in events if e['symbol']==symbol]
        lines += [f'## {symbol}: event anatomy','', '| Peak | Onset | First-5 / -10 / -15 / -20 | Trough / depth | Prior-peak recovery |','|---|---|---|---|---|']
        for e in rows:
            dates=' / '.join(e[f'minus_{n}_date'] or '—' for n in (5,10,15,20))
            lines.append(f"| {e['peak_date']} | {e['onset_date']} | {dates} | {e['trough_date']} / {fmt(e['depth_pct'],1)}% | {e['recovery_date'] or 'OPEN'} |")
        direction=[r for r in result['comparisons'] if r['group']==symbol and r['horizon']==60 and not r.get('subset')]
        lines += ['', 'Incremental Brier versus joint baseline: '+', '.join(r['hypothesis']+' '+fmt(r['brier_difference'],4) for r in direction)+'. Stock/year/subgroup tables retain contrary results as well as favorable ones.','']
    lines += ['## Interpretation and missing evidence','',
        'A factor can recur before a large episode and be common in healthy growth too. Calendar-regime matching, all-cohort denominators, joint baselines, expanded stocks and chronological horizon purging reduce specific biases but cannot eliminate reverse timing, confounding, survivor selection or the repeated reuse of this historical sample. Current deterioration can predict continuation without anticipating a new decline: inspect near-high subsets.','',
        'Missing fundamentals (H4) are not evidence of no fundamental relationship. Retrospective yield history supports a conditional H5 research test but not verified original-publication correctness. Whole-market breadth and historical sector membership are absent; H3 is conditional on the explicitly listed fixed peer basket. No candidate is ready for live recommendations, and no trading strategy or investment effectiveness claim follows.','',
        '## Figures and reproduction','',
        '![Historical drawdowns](historical-drawdowns.png)','', '![Feature versus controls](feature-control-distributions.png)','',
        '![Incremental hypothesis comparison](hypothesis-incremental.png)','',
        '`OPENBLAS_NUM_THREADS=1 python -m aae.research.drawdown_anatomy_study` reproduces offline from frozen packs. Source refresh is separate: scripts/fetch_drawdown_anatomy_data.py. Required CSVs accompany daily forecast, all-cohort, matched-control, single-feature, probability, maturity and episode-sensitivity audit tables. Hypothesis tables include missing H4 rows explicitly. validation.md and missing-data.md list failed/unavailable historical checks; run.json contains code/data/output hashes.']
    comparisons=matched_summary(snapshots,matches)
    extra=['## Matched control frequencies: primary stocks,20-session presnapshot','',
        '| Pattern | Event prevalence (N) | Small correction | Continuing growth | Sideways |',
        '|---|---|---|---|---|']
    for h in ('H1','H2','H3','H4','H5'):
        group=[r for r in comparisons if r['group']=='PRIMARY' and r['hypothesis']==h and r['offset']==20]
        first=group[0]
        cells=[]
        for category in ('SMALL_CORRECTION','GROWTH','SIDEWAYS'):
            r=next(r for r in group if r['control_class']==category)
            cells.append(fmt(r['weighted_control_prevalence'])+' (unique='+str(r['unique_controls'])+')')
        extra.append('| '+h+' | '+fmt(first['case_prevalence'])+' ('+str(first['case_n'])+') | '+' | '.join(cells)+' |')
    extra += ['', 'These are matched descriptive frequencies with reused controls, not prospective probabilities. Unmatched category cells remain unavailable. Discovery cohort outcomes and discovery episode labels are explicitly truncated at December2022; incomplete boundary horizons never borrow2023 labels.', '']
    at=lines.index('## Primary incremental probability test');lines[at:at]=extra
    singles=['## Individual features before combinations (exploratory)','',
        '| Flag | Exposed anchors / hits | Risk ratio [95%CI] | False warnings | Holm p | Support |',
        '|---|---|---|---|---|---|']
    for r in result['single']:
        singles.append(f"| {r['feature']} | {r.get('exposed_n',0)} / {r.get('exposed_events',0)} | {fmt(r.get('risk_ratio'))} [{fmt(r.get('risk_ratio_low'))}, {fmt(r.get('risk_ratio_high'))}] | {fmt(r.get('false_warning_share'))} | {fmt(r.get('holm_exploratory'))} | {r['status']} |")
    singles += ['', 'All18 flags are shown; cohort risk associations are not evidence of added predictive information. The full fixed family receives exploratory Holm adjustment. Sparse exposures remain LOW_SUPPORT.', '']
    at=lines.index('## Five prespecified candidate patterns');lines[at:at]=singles
    target=['## Exploratory forward-path target sensitivity','',
        'A pre-peak rally can precede a large peak-to-trough decline without a10% loss from the earlier anchor. Catalogue event coverage and anchor-price forecast recall therefore answer different questions. The additional target starts a running peak at the anchor and asks whether the next60 closes ever fall10% from an evolving future peak. The peak enters labels only, not features. Full-horizon purging is unchanged.', '',
        'This sensitivity was introduced AFTER the first primary results (protocol commit3d53761), before its own calculation. It is exploratory and cannot replace a failed primary result or become independent confirmation. Hypotheses, parameters and baselines were unchanged.', '',
        '| Group | Pattern | Δ Brier [95%CI] | Relative improvement % | Exploratory Holm p |',
        '|---|---|---|---|---|']
    for r in path_results:
        if r['group'] in ('PRIMARY','EXPANDED'):
            target.append(f"| {r['group']} | {r['hypothesis']} | {fmt(r['brier_difference'],4)} [{fmt(r['brier_difference_low'],4)}, {fmt(r['brier_difference_high'],4)}] | {fmt(r['relative_brier_improvement_pct'],2)} | {fmt(r.get('holm_exploratory'),4)} |")
    target.append('')
    at=lines.index('## Interpretation and missing evidence');lines[at:at]=target
    baseline=['## Probability baselines: primary stocks,60-session anchor loss','',
        '| Model | N | Effective N (HAC) | Brier | Log loss |', '|---|---|---|---|---|']
    for r in result['metrics']:
        if r['group']=='PRIMARY' and r['horizon']==60 and r['model'] in ('historical','volatility','drawdown','relative','v3','joint'):
            baseline.append(f"| {r['model']} | {r['n']} | {fmt(r['effective_n_hac'],1)} | {fmt(r['brier'],4)} | {fmt(r['log_loss'],4)} |")
    baseline += ['', 'These are conditional retrospective forecasts, not independent daily trials. Joint comparison requires the same valid inputs and matched outcomes; absent predictors suppress a comparison.', '']
    at=lines.index('## Primary incremental probability test');lines[at:at]=baseline
    sensitivity=['## Catalogue-definition robustness','',
        '| Stock | Definition | Events | H1 coverage | H2 coverage | H3 coverage | H5 coverage |',
        '|---|---|---|---|---|---|---|']
    for r in robustness:
        if r['symbol'] not in PRIMARY:continue
        values={x['hypothesis']:x for x in episode_hypotheses if x['symbol']==r['symbol'] and x['definition']==r['definition']}
        sensitivity.append('| '+r['symbol']+' | '+r['definition']+' | '+str(r['events'])+' | '+' | '.join(fmt(values[h]['catalog_coverage']) for h in ('H1','H2','H3','H5'))+' |')
    sensitivity += ['', 'Counts and descriptive coverage change with segmentation. No favorable definition replaces the principal closing100%-recovery catalogue. The forward anchor/path targets do not consume catalogue peaks; their reported probability tests are separate from this segmentation sensitivity.', '']
    at=lines.index('## Interpretation and missing evidence');lines[at:at]=sensitivity
    (ROOT/'report.md').write_text('\n'.join(lines)+'\n')


def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    stocks,volumes,qqq,sox,markets,rates,coverage,folds,archived=load_inputs()
    # Event-first: no hypotheses/features have been calculated at this point.
    events=[e for series in stocks.values() for e in catalogue(series)]
    write_csv(ROOT/'drawdown-catalog.csv',events)
    print(json.dumps(dict(catalogue_events=len(events),primary_events=sum(e['symbol'] in PRIMARY for e in events))),flush=True)
    robustness=[]
    for name,kwargs in (('close100',{}),('high_low',{'extrema':'high_low'}),('recovery98',{'recovery':.98}),('minimum12',{'minimum':.12})):
        for symbol,series in stocks.items():
            rows=catalogue(series,**kwargs)
            robustness.append(dict(definition=name,symbol=symbol,events=len(rows),open=sum(r['status']=='OPEN_AT_CUTOFF' for r in rows),
                mean_depth=float(np.mean([r['depth_pct'] for r in rows])) if rows else None))
    features={}
    for symbol,series in stocks.items():
        if not series:continue
        features[symbol]=build_features(series,volumes[symbol],qqq,sox,markets,rates)
        add_v3(symbol,features[symbol],folds,archived)
        print(json.dumps(dict(features_built=symbol,rows=len(features[symbol]))),flush=True)
    sector_features(features)
    for rows in features.values():
        for row in rows:row.update(hypotheses(row));row['flags']=flags(row)
    cohort,snapshots,matches=controls_and_snapshots(events,features,stocks)
    predictions,audit=forecast(features,stocks,folds)
    path_predictions,path_audit=forecast(features,stocks,folds,path_target=True)
    calendar=[b.close_at.date().isoformat() for b in qqq]
    discovery_events=[e for series in stocks.values() for e in catalogue(series,end='2022-12-31')]
    result=evaluate_study(predictions,cohort,events,features,calendar,discovery_events)
    path_results=path_comparison(path_predictions,calendar)
    episode_hypotheses=[]
    options={'close100':{},'high_low':{'extrema':'high_low'},'recovery98':{'recovery':.98},'minimum12':{'minimum':.12}}
    for r in robustness:
        selected=catalogue(stocks[r['symbol']],**options[r['definition']])
        for h in ('H1','H2','H3','H4','H5'):
            episode_hypotheses.append(dict(symbol=r['symbol'],definition=r['definition'],hypothesis=h,**event_coverage(selected,features,h)))
    outputs={'episode-hypothesis-sensitivity.csv':episode_hypotheses,'target-sensitivity.csv':path_results,'path-forecast-daily.csv.gz':flatten(path_predictions),'path-fit-audit.csv':path_audit,'drawdown-catalog.csv':events,'pre-drawdown-features.csv':flatten(snapshots),'control-periods.csv':flatten(matches),
        'hypothesis-comparison.csv':result['hypotheses'],'cross-stock-validation.csv':result['cross'],
        'data-coverage.csv':coverage,'episode-sensitivity.csv':robustness,'cohort-all.csv':flatten(cohort),
        'matched-control-comparison.csv':matched_summary(snapshots,matches),'forecast-daily.csv.gz':flatten(predictions),
        'fit-audit.csv':audit,'baseline-metrics.csv':result['metrics'],'incremental-comparison.csv':result['comparisons'],
        'block-sensitivity.csv':result['sensitivity'],'single-feature-comparison.csv':result['single']}
    for name,rows in outputs.items():
        if name.endswith('.gz'):
            temporary=ROOT/name[:-3];write_csv(temporary,rows)
            (ROOT/name).write_bytes(gzip.compress(temporary.read_bytes(),mtime=0));temporary.unlink()
        else:write_csv(ROOT/name,rows)
    plots(features,snapshots,matches,result);report(events,snapshots,matches,result,coverage,robustness,path_results,episode_hypotheses)
    primary=[r for r in result['comparisons'] if r.get('primary')]
    paths=[Path(__file__),Path('aae/research/drawdown_anatomy.py'),Path('aae/research/drawdown_anatomy_models.py'),
        Path('scripts/fetch_drawdown_anatomy_data.py'),DATA/'manifest.json',Path('data/risk-signal-v3/manifest.json'),ROOT/'protocol.md',ROOT/'target-sensitivity-protocol.md']
    if Path('tests/test_drawdown_anatomy.py').exists():paths.append(Path('tests/test_drawdown_anatomy.py'))
    metadata=dict(schema_version=1,cutoff='2026-10-22',protocol_commit='c8d0b6f',
        source_sha256={str(p):sha(p) for p in paths},output_sha256={p.name:sha(p) for p in ROOT.iterdir() if p.name not in ('protocol.md','run.json')},
        counts={name:len(rows) for name,rows in outputs.items()},
        testable_primary_hypotheses=len(primary),provisionally_supported=sum(r['provisionally_supported'] for r in primary),
        historical_vintage_verified=False,survivorship_free=False,signals_changed=False,trades_simulated=False)
    (ROOT/'run.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(json.dumps(dict(counts=metadata['counts'],supported=metadata['provisionally_supported'])),flush=True)


if __name__=='__main__':main()
