"""Matched cluster controls and synchronous calendar-block uncertainty."""
import collections,json,math,random,statistics
from research.signal_predictive_accuracy.io import R,STOCKS,MARKETS,load,rows,write
from research.signal_predictive_accuracy.engine import classify
SEED=20261103;REPS=1999
def quantile(xs,p):
    xs=sorted(xs);k=(len(xs)-1)*p;a=int(k);return xs[a]+(xs[min(a+1,len(xs)-1)]-xs[a])*(k-a)
def cell(x,model):return (x['quarter'],x['regime'],x['eligible_signature'])+((x['dd_bin'],) if model=='DRAWDOWN_MATCHED_RANDOM' else ())
def design(data,model,cohort):
    candidates={}
    for x in data:
        if not x['complete10'] or x['score'] is None:continue
        # Mechanical baseline retains natural overlaps with sector warnings; random dates exclude them.
        valid=x['mechanical'] if model=='MECHANICAL_QQQ_R5' else not x['sector_warning']
        if valid:candidates.setdefault(cell(x,model),[]).append(x['calendar_index'])
    pairs=[];unmatched=[]
    for x in data:
        if not x['sector_warning'] or not x['complete10'] or x['score'] is None:continue
        c=cell(x,model)
        if candidates.get(c):pairs.append((x['calendar_index'],c))
        else:unmatched.append(x['date'])
    return dict(model=model,cohort=cohort,candidates=candidates,pairs=pairs,unmatched=unmatched,data=data)
def estimate(d,weights):
    means={}
    for c,ids in d['candidates'].items():
        den=sum(weights[i] for i in ids)
        if den:means[c]=sum(weights[i]*d['data'][i]['score'] for i in ids)/den
    ps=[(i,c) for i,c in d['pairs'] if weights[i] and c in means];den=sum(weights[i] for i,c in ps)
    if not den:return None
    s=sum(weights[i]*d['data'][i]['score'] for i,c in ps)/den;b=sum(weights[i]*means[c] for i,c in ps)/den
    return s,b,s-b
def block_weights(n,length,rng):
    w=[0]*n;remaining=n
    while remaining:
        start=rng.randrange(0,n-length+1);size=min(length,remaining)
        for j in range(start,start+size):w[j]+=1
        remaining-=size
    return w
def weighted_values(values,w):
    ids=[i for i,x in enumerate(values) if x is not None and w[i]];den=sum(w[i] for i in ids)
    return sum(w[i]*values[i] for i in ids)/den if den else None
def main():
    cache=json.loads((R/'control-cache.json').read_text());p=load();n=len(cache);data_by_cohort={'STOCK':cache}
    markets=[];indices={s:{x['date']:i for i,x in enumerate(p['bars'][s])} for s in MARKETS}
    for x in cache:
        z=dict(x);scores={}
        for s in MARKETS:
            a=p['bars'][s];i=indices[s][x['date']];future=a[i+1:i+11];c=classify(future,future[0]['open'] if future else None);scores[s]=1 if c['complete'] and c['classification']=='TRUE_POSITIVE' else 0 if c['complete'] and c['classification']=='FALSE_POSITIVE' else None
        vs=[v for v in scores.values() if v is not None];z.update(score=statistics.mean(vs) if vs else None,stock_scores=scores,eligible_signature=';'.join(MARKETS));markets.append(z)
    data_by_cohort['MARKET']=markets
    designs=[]
    for cohort,data in data_by_cohort.items():
        for model in ['RANDOM_MATCHED','MECHANICAL_QQQ_R5']+(['DRAWDOWN_MATCHED_RANDOM'] if cohort=='STOCK' else []):designs.append(design(data,model,cohort))
    result=[];cells=[];panels=[];panelstats=[]
    for k,d in enumerate(designs):
        e=estimate(d,[1]*n)
        result.append(dict(cohort=d['cohort'],model=d['model'],matched_warning_dates=len(d['pairs']),unmatched_warning_dates=len(d['unmatched']),unmatched_dates=';'.join(d['unmatched']),signal_precision=e[0] if e else None,control_precision=e[1] if e else None,lift_pp=e[2]*100 if e else None,primary=d['cohort']=='STOCK' and d['model']!='DRAWDOWN_MATCHED_RANDOM'))
        for c,ids in d['candidates'].items():cells.append(dict(cohort=d['cohort'],model=d['model'],cell='|'.join(c),candidate_count=len(ids),dates=';'.join(d['data'][i]['date'] for i in ids),matched_signal_count=sum(cc==c for i,cc in d['pairs']),control_reuse_possible=True))
        if d['cohort']=='STOCK':
            rng=random.Random(SEED+k)
            for panel in range(500):
                selected=[(i,rng.choice(d['candidates'][c]),c) for i,c in d['pairs']]
                score=statistics.mean(d['data'][j]['score'] for i,j,c in selected) if selected else None
                panelstats.append(dict(model=d['model'],panel=panel,matched_count=len(selected),unique_control_dates=len({j for i,j,c in selected}),control_precision=score))
                panels.extend(dict(model=d['model'],panel=panel,warning_date=d['data'][i]['date'],control_date=d['data'][j]['date'],cell='|'.join(c)) for i,j,c in selected)
    write('control-cells.csv',cells);write('matched-control-panels.csv.gz',panels);write('control-panel-summary.csv',panelstats)
    # All assets on the same warning day are kept in the same bootstrap calendar weight.
    assets={}
    for cohort,data in data_by_cohort.items():
        for s in STOCKS if cohort=='STOCK' else MARKETS:assets[cohort,s]=[x['stock_scores'].get(s) if x['sector_warning'] and x['complete10'] else None for x in data]
    source_values={cohort:[x['score'] if x['sector_warning'] and x['complete10'] else None for x in data] for cohort,data in data_by_cohort.items()}
    missed=rows(R/'missed-falls.csv');eventsets={}
    for cohort in ['STOCK','MARKET']:
        for threshold in [5,10,15]:
            for h in [5,10,20]:
                xs=[x for x in missed if x['cohort']==cohort and int(x['threshold_pct'])==threshold and int(x['lookback'])==h and x['lookback_complete']=='True'];counts=collections.Counter();hits=collections.Counter()
                for x in xs:
                    i=next(i for i,c in enumerate(cache) if c['date']==x['threshold_date']);counts[i]+=1;hits[i]+=x['warning_present']=='True'
                eventsets[cohort,threshold,h]=(xs,counts,hits)
    intervals=[];assetci=[];dateci=[];recallci=[]
    for length in [20,60,120]:
        rng=random.Random(SEED+length);boot=[[] for _ in designs];ab={k:[] for k in assets};sb={k:[] for k in source_values};fb={k:[] for k in eventsets}
        for rep in range(REPS):
            w=block_weights(n,length,rng)
            for j,d in enumerate(designs):
                e=estimate(d,w)
                if e:boot[j].append(e)
            if length==60:
                for k,v in assets.items():
                    e=weighted_values(v,w)
                    if e is not None:ab[k].append(e)
                for k,v in source_values.items():
                    e=weighted_values(v,w)
                    if e is not None:sb[k].append(e)
                for k,(xs,counts,hits) in eventsets.items():
                    den=sum(w[i]*v for i,v in counts.items())
                    if den:fb[k].append(sum(w[i]*v for i,v in hits.items())/den)
        for j,(d,values) in enumerate(zip(designs,boot)):
            primary=d['cohort']=='STOCK' and d['model']!='DRAWDOWN_MATCHED_RANDOM';alpha=.025 if primary else .05;lifts=[x[2]*100 for x in values]
            intervals.append(dict(cohort=d['cohort'],model=d['model'],block_length=length,resamples=len(values),familywise_primary_confidence=.95 if primary else None,marginal_confidence=1-alpha,ci_low_pp=quantile(lifts,alpha/2),ci_high_pp=quantile(lifts,1-alpha/2),signal_low=quantile([x[0] for x in values],.025),signal_high=quantile([x[0] for x in values],.975),control_low=quantile([x[1] for x in values],.025),control_high=quantile([x[1] for x in values],.975)))
        if length==60:
            for (cohort,s),v in ab.items():assetci.append(dict(cohort=cohort,symbol=s,block_length=60,ci_low=quantile(v,.025),ci_high=quantile(v,.975),resamples=len(v)))
            for cohort,v in sb.items():dateci.append(dict(cohort=cohort,precision_date_weighted=weighted_values(source_values[cohort],[1]*n),ci_low=quantile(v,.025),ci_high=quantile(v,.975),block_length=60,resamples=len(v)))
            for k,v in fb.items():
                xs,counts,hits=eventsets[k];total=sum(counts.values());covered=sum(hits.values());recallci.append(dict(cohort=k[0],threshold_pct=k[1],lookback=k[2],events=total,threshold_date_clusters=len(counts),covered=covered,missed=total-covered,recall=covered/total if total else None,ci_low=quantile(v,.025) if v else None,ci_high=quantile(v,.975) if v else None,block_length=60))
        print('bootstrap finished',length,flush=True)
    write('baseline-comparison.csv',result);write('baseline-confidence.csv',intervals);write('asset-confidence.csv',assetci);write('date-confidence.csv',dateci);write('false-negative-summary.csv',recallci)
    (R/'bootstrap.json').write_text(json.dumps(dict(seed=SEED,replicates=REPS,primary_block=60,sensitivity_blocks=[20,120],stocks_resampled_synchronously=True,controls_and_signals_reweighted_together=True,primary_marginal_confidence=.975,primary_familywise_confidence=.95,secondary_exploratory=True),indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
