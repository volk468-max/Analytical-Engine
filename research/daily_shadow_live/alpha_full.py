"""Alpha Full v1: shared, explicitly experimental multi-source research model.

Cold-start expert priors are hypotheses, not learned/calibrated probabilities.
Missing observations have masks/reasons; optional sources never block the model.
"""
import csv
import io
import math
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit, logit

from research.daily_shadow.core import future_sessions
from .context_factors import FACTORS, digest, number, source_url, utc
from .forecast_export import HEADER, MODELS
from .portfolio import SYMBOLS, UNIVERSE_REVISION

NAMES = ('rf_logit_difference', 'market_logit_difference') + FACTORS + (
    'sa_eps_revision', 'sa_revenue_revision', 'sa_revision_breadth',
    'sa_profitability', 'sa_valuation')
# Frozen engineering starting hypotheses; positive company/context scores lower DOWN risk.
EXPERT = np.array([.15, .20] + [-.05]*6 + [-.10, -.05, -.10, -.03, -.03])
MAX_DELTA = .6
GRADES = ('F','D-','D','D+','C-','C','C+','B-','B','B+','A-','A','A+')
FEATURE_SCHEMA = digest(dict(version='ALPHA_FULL_FEATURES_V1',names=NAMES,
    baseline_order=['VOL','RISK_FORECAST','MARKET_PRECURSORS'],probability_clip=1e-6,
    residual_clip=2,llm_scale=100,reliability=[.25,.5,1],revision_scale=20,grades=GRADES,
    freshness_hours=dict(llm=36,seeking=168),sa_revision_period='FY1',mask_order='VALUES_THEN_MISSING_MASKS'))
VERSION = 'ALPHA_FULL_V1-' + digest(dict(code=Path(__file__).read_text(),
            names=NAMES, prior=EXPERT.tolist(), delta_cap=MAX_DELTA))[:16]
MANIFEST = dict(model_name='ALPHA_FULL',model_version=VERSION,symbols=list(SYMBOLS),
                horizons=[10,30],thresholds=[5,10,15],labels=['LOW_INTRADAY','EOD_CLOSE'],
                row_count=120,universe_revision_sha256=UNIVERSE_REVISION,
                features=list(NAMES),feature_schema_sha256=FEATURE_SCHEMA,missing_masks=True,qualified=False)


def key(r):
    return (r['symbol'],int(r['horizon']),int(r['threshold_pct']),r['label_type'])


def parse_baseline(blob,session,issued):
    reader=csv.DictReader(io.StringIO(blob.decode('utf-8')))
    if tuple(reader.fieldnames or ())!=HEADER:raise ValueError('FULL_BASELINE_HEADER')
    rows=list(reader); bank={}
    from itertools import product
    expected={(s,m,h,t,l) for m in MODELS
              for s,h,t,l in product(SYMBOLS+(('SPY','QQQ','SOXX') if m=='MARKET_PRECURSORS' else ()),
                                     (10,30),(5,10,15),('LOW_INTRADAY','EOD_CLOSE'))}
    for r in rows:
        k=(r['symbol'],r['model'],int(r['horizon']),int(r['threshold_pct']),r['label_type'])
        if k in bank:raise ValueError('FULL_DUPLICATE_BASELINE')
        if r['session_date']!=session or utc(r['issued_at_utc'])>utc(issued):
            raise ValueError('FULL_BASELINE_NOT_AVAILABLE_ASOF')
        bank[k]=r
    if set(bank)!=expected or len(rows)!=516:raise ValueError('FULL_INCOMPLETE_BASELINE')
    return bank


def context(bundle,symbol,session,horizon,issued,*,fixture=False):
    values={}; reasons={k:'SOURCE_MISSING' for k in NAMES[2:]}; refs={}
    root=bundle if isinstance(bundle,dict) else {}
    by_horizon=root.get('coefficients_by_horizon',{})
    if not isinstance(by_horizon,dict):by_horizon={}
    c=by_horizon.get(str(horizon),root.get('coefficients',{}))
    if not isinstance(c,dict):c={}
    try:
        if c.get('fixture',False)!=fixture:raise ValueError('FIXTURE_MISMATCH')
        cutoff=utc(c['information_cutoff_utc']);created=utc(c['created_at_utc'])
        if not cutoff<=created<=utc(issued):raise ValueError('NOT_AVAILABLE_ASOF')
        if (utc(issued)-cutoff).total_seconds()>36*3600:raise ValueError('STALE')
        if (c['last_completed_session']!=session or c['horizon_sessions']!=horizon
                or c['forecast_sessions']!=future_sessions(session,horizon)):
            raise ValueError('SESSION_OR_HORIZON_MISMATCH')
        entries=[e for e in c['instruments'] if isinstance(e,dict) and e.get('symbol')==symbol]
        if len(entries)!=1:raise ValueError('SYMBOL_NOT_UNIQUE')
        e=entries[0]
        if e['data_status'] not in ('PARTIAL','SUFFICIENT'):raise ValueError('INSUFFICIENT')
        evidence=c.get('events',[])
        if not evidence:raise ValueError('EVIDENCE_MISSING')
        if any(not utc(x['published_at_utc'])<=utc(x['retrieved_at_utc'])<=cutoff for x in evidence):
            raise ValueError('FUTURE_EVIDENCE')
        reliability={'LOW':.25,'MEDIUM':.5,'HIGH':1.}[e['confidence_level']]
        for k in FACTORS:
            try:
                v=number(e['factor_scores'].get(k),-100,100)
                ref=dict(value=v,confidence=e['confidence_level'],cutoff_utc=c['information_cutoff_utc'],
                         source_record_sha256=digest(c),run_id=c['run_id'])
                values[k]=v/100*reliability;refs[k]=ref;reasons.pop(k,None)
            except (ValueError,KeyError,TypeError):reasons[k]='FACTOR_UNAVAILABLE'
    except (ValueError,KeyError,TypeError) as exc:
        why=str(exc) if isinstance(exc,ValueError) else 'COEFFICIENT_SCHEMA'
        reasons.update({k:why for k in FACTORS})
    s=root.get('seeking',{})
    if not isinstance(s,dict):s={}
    fields={}
    try:
        if s.get('fixture',False)!=fixture:raise ValueError('FIXTURE_MISMATCH')
        if s['schema_version']!='SA_CONTEXT_V1' or s['use_scope']!='PRIVATE_RESEARCH':
            raise ValueError('SEEKING_SCHEMA_OR_SCOPE')
        entries=[e for e in s['instruments'] if isinstance(e,dict) and e.get('symbol')==symbol]
        if len(entries)!=1:raise ValueError('SYMBOL_NOT_UNIQUE')
        if entries[0]['data_status']!='VERIFIED_OBSERVATION':raise ValueError('UNVERIFIED')
        fields=entries[0]['fields']
    except (ValueError,KeyError,TypeError):pass
    def observed(name,grade=False):
        o=fields[name];source_url(o['source_url'])
        if not utc(o['published_at_utc'])<=utc(o['retrieved_at_utc'])<=utc(issued):
            raise ValueError('NOT_AVAILABLE_ASOF')
        if (utc(issued)-utc(o['retrieved_at_utc'])).total_seconds()>7*86400:raise ValueError('STALE')
        if o['source_type'] not in ('MANUAL_VERIFIED','LICENSED_EXPORT'):raise ValueError('UNVERIFIED')
        if not o.get('fiscal_period') or o.get('accounting_basis') not in (('GAAP','NON_GAAP','PROVIDER_COMPOSITE') if grade else ('GAAP','NON_GAAP')):
            raise ValueError('FINANCIAL_PERIOD_MISSING')
        if not grade and o.get('forecast_period_role')!='FY1':raise ValueError('NEXT_FISCAL_YEAR_REQUIRED')
        if grade:
            value=(GRADES.index(o['value'])-6)/6
        else:value=number(o['value'],-1000,100000)
        safe={k:o[k] for k in ('value','fiscal_period','accounting_basis','source_url','source_type','published_at_utc','retrieved_at_utc')}
        if not grade:safe['forecast_period_role']='FY1'
        return value,safe
    for dest,field,grade,scale in (
            ('sa_eps_revision','eps_revision_30d_pct',False,20),
            ('sa_revenue_revision','revenue_revision_30d_pct',False,20),
            ('sa_profitability','profitability_grade',True,1),
            ('sa_valuation','valuation_grade',True,1)):
        try:
            v,o=observed(field,grade);values[dest]=float(np.clip(v/scale,-1,1));refs[dest]=o;reasons.pop(dest,None)
        except (KeyError,ValueError,TypeError):reasons[dest]='SEEKING_FIELD_UNAVAILABLE'
    try:
        up,u=observed('eps_up_revisions_90d');down,d=observed('eps_down_revisions_90d')
        if min(up,down)<0 or not up.is_integer() or not down.is_integer() or up+down==0:
            raise ValueError('NO_REVISION_SUPPORT')
        if (u['fiscal_period'],u['accounting_basis'])!=(d['fiscal_period'],d['accounting_basis']):
            raise ValueError('MIXED_PERIOD')
        values['sa_revision_breadth']=(up-down)/(up+down)
        refs['sa_revision_breadth']=dict(up=u,down=d);reasons.pop('sa_revision_breadth',None)
    except (KeyError,ValueError,TypeError):reasons['sa_revision_breadth']='SEEKING_REVISION_BREADTH_UNAVAILABLE'
    return values,reasons,refs


def feature_vector(values):
    # Zero is an internal placeholder only; the separately stored mask distinguishes unknown from neutral.
    return [float(values.get(k,0)) for k in NAMES]+[float(k not in values) for k in NAMES]


def train(records,target,fit_at):
    """One shared head across symbols; synchronous dates have total weight one.
    No label is reconstructed from price data here: only archived matured outcomes.
    """
    target=tuple(target); rows=[]; seen=set()
    for r in records:
        if tuple(r['target'])!=target:continue
        ident=(r['session'],r['symbol'])
        if ident in seen:raise ValueError('FULL_DUPLICATE_TRAINING_KEY')
        seen.add(ident)
        if not utc(r['issued_at'])<utc(r['maturity_at'])<=utc(r['outcome_available_at'])<utc(fit_at):
            raise ValueError('FULL_TRAINING_TIME_TRAVEL')
        if r.get('feature_schema_sha256')!=FEATURE_SCHEMA or r['feature_names']!=list(NAMES) or len(r['x'])!=2*len(NAMES):raise ValueError('FULL_FEATURE_VERSION')
        if r.get('fixture',False):raise ValueError('FULL_FIXTURE_TRAINING_FORBIDDEN')
        if not all(math.isfinite(v) for v in r['x']) or r['y'] not in (0,1):raise ValueError('FULL_INVALID_TRAINING')
        number(r['offset'],-40,40);rows.append(r)
    dates=Counter(r['session'] for r in rows)
    if len(dates)<20 or min(len({r['session'] for r in rows if r['y']==label}) for label in (0,1))<5:
        return None
    x=np.asarray([[1]+r['x'] for r in rows]);y=np.array([r['y'] for r in rows]);offset=np.array([r['offset'] for r in rows])
    w=np.array([1/dates[r['session']] for r in rows])
    prior=np.r_[0,EXPERT,np.zeros(len(NAMES))]
    def loss(beta):
        z=offset+x@beta;diff=beta-prior
        return float(np.sum(w*(np.logaddexp(0,z)-y*z))+5*(diff@diff)),x.T@(w*(expit(z)-y))+10*diff
    fit=minimize(loss,prior,jac=True,method='L-BFGS-B')
    if not fit.success:raise ValueError('FULL_FIT_NOT_CONVERGED')
    result=dict(kind='LEARNED_POOLED_EXPERIMENTAL',qualified=False,target=list(target),
                fitted_at=fit_at,n=len(rows),distinct_sessions=len(dates),
                effective_independent_samples='UNKNOWN_CORRELATED_DATES',
                feature_names=list(NAMES),feature_schema_sha256=FEATURE_SCHEMA,beta=fit.x.tolist(),training_sha256=digest(rows))
    result['artifact_sha256']=digest(result)
    return result


def repair_coherence(rows):
    """Explicit deterministic feasibility repair, not calibration or evidence of accuracy."""
    numeric={key(r):r for r in rows if r['probability_raw'] is not None}
    edges=[]
    for k in numeric:
        s,h,t,l=k
        for other in ((s,h,t+5,l) if t<15 else None,
                      (s,10,t,l) if h==30 else None,
                      (s,h,t,'EOD_CLOSE') if l=='LOW_INTRADAY' else None):
            if other in numeric:edges.append((k,other)) # p(k) >= p(other)
    for _ in range(1000):
        violation=0.
        for a,b in edges:
            left,right=numeric[a],numeric[b];gap=right['probability_raw']-left['probability_raw']
            if gap>0:
                violation=max(violation,gap);mean=(left['probability_raw']+right['probability_raw'])/2
                left['probability_raw']=right['probability_raw']=mean
        if violation<1e-12:break
    else:raise ValueError('FULL_COHERENCE_DID_NOT_CONVERGE')
    for r in rows:
        r['coherence_adjustment']=None if r['probability_raw'] is None else r['probability_raw']-r['probability_before_coherence']


def forecast(blob,session,issued,*,bundle=None,artifacts=None,fixture=False):
    bank=parse_baseline(blob,session,issued);artifacts=artifacts or {};result=[];context_cache={}
    for symbol in SYMBOLS:
        for h in (10,30):
            context_cache[symbol,h]=context(bundle,symbol,session,h,issued,fixture=fixture)
            for t in (5,10,15):
                for label in ('LOW_INTRADAY','EOD_CLOSE'):
                    components={};warnings=[]
                    for name in ('VOL','RISK_FORECAST','MARKET_PRECURSORS'):
                        r=bank[symbol,name,h,t,label]
                        if r['status']=='RESEARCH_FORECAST' and r['probability_raw']!='':
                            p=number(float(r['probability_raw']),0,1);components[name]=float(np.clip(p,1e-6,1-1e-6))
                            if r['reason']:warnings.append(name+':'+r['reason'])
                    values,reasons,refs=context_cache[symbol,h];values=dict(values);reasons=dict(reasons)
                    base_name=next((n for n in ('VOL','RISK_FORECAST','MARKET_PRECURSORS') if n in components),None)
                    offset=float(logit(components[base_name])) if base_name else None
                    for dest,name in (('rf_logit_difference','RISK_FORECAST'),('market_logit_difference','MARKET_PRECURSORS')):
                        if name in components and base_name:
                            values[dest]=float(np.clip(logit(components[name])-offset,-2,2));reasons.pop(dest,None)
                        else:reasons[dest]='BASELINE_COMPONENT_UNAVAILABLE'
                    x=feature_vector(values);a=artifacts.get((h,t,label));mode='EXPERT_PRIOR_UNTRAINED'
                    beta=np.r_[0,EXPERT,np.zeros(len(NAMES))];model_hash=digest(beta.tolist())
                    if a is not None:
                        if (a['artifact_sha256']!=digest({k:v for k,v in a.items() if k!='artifact_sha256'})
                                or a['target']!=[h,t,label] or a['feature_names']!=list(NAMES) or a.get('feature_schema_sha256')!=FEATURE_SCHEMA
                                or utc(a['fitted_at'])>utc(issued) or a['qualified'] is not False
                                or len(a['beta'])!=len(beta) or not all(math.isfinite(v) for v in a['beta'])):
                            raise ValueError('FULL_INVALID_LEARNED_ARTIFACT')
                        beta=np.array(a['beta']);mode=a['kind'];model_hash=a['artifact_sha256']
                    delta=float(np.clip(beta[0]+np.asarray(x)@beta[1:],-MAX_DELTA,MAX_DELTA))
                    p=float(expit(offset+delta)) if offset is not None else None
                    result.append(dict(symbol=symbol,horizon=h,threshold_pct=t,label_type=label,
                        model_name='ALPHA_FULL',model_version=VERSION,session=session,issued_at=issued,
                        horizon_sessions=future_sessions(session,h),qualified=False,calibrated=False,
                        probability_raw=p,probability_before_coherence=p,baseline_probability=components.get(base_name),
                        baseline_model=base_name,baseline_issued_at=bank[symbol,base_name,h,t,label]['issued_at_utc'] if base_name else None,
                        offset=offset,weights_mode=mode,weights_sha256=model_hash,
                        status='EXPERIMENTAL_FORECAST' if p is not None else 'STATUS_BLOCKED',
                        reason='NO_NUMERIC_BASELINE' if p is None else ('PARTIAL_INPUTS' if reasons else 'EXPERIMENTAL_UNVALIDATED'),
                        feature_names=list(NAMES),features=values,feature_vector=x,missing_features=reasons,
                        context_provenance=refs,baseline_warnings=warnings))
    repair_coherence(result)
    return dict(schema_version='ALPHA_FULL_RUN_V1',model_name='ALPHA_FULL',model_version=VERSION,
                manifest=MANIFEST,session=session,issued_at=issued,fixture=fixture,qualified=False,
                baseline_csv_sha256=__import__('hashlib').sha256(blob).hexdigest(),
                context_bundle_sha256=digest(bundle) if bundle else None,artifacts=list(artifacts.values()),rows=result)
