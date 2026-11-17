"""Explainable research signals only: no sizing, orders or production entry points."""
from dataclasses import dataclass,asdict,replace
from math import isfinite
from aae.backtest.simulator import utc

LEVELS={'HOLD':0,'WATCH':1,'REDUCE':2,'CRITICAL':3}
REQUIRED=('close','ma20','ma50','ma200','drawdown_20_pct','drawdown_60_pct',
    'return_5_pct','return_10_pct','fall_acceleration_5_pp','ma20_slope_5_pct','ma50_slope_5_pct',
    'ma20_slope_change_pp','ma50_slope_change_pp','rsi14','relative_return_qqq20_pp',
    'rv20_pct','rv60_pct')
OPTIONAL=('relative_return_sox20_pp','vix','support','rv20_change_5_ratio')


@dataclass(frozen=True)
class RiskV3Config:
    name:str='balanced'
    watch_dd:float=5
    reduce_dd:float=8
    critical_dd:float=20
    fast_drop:float=7
    relative_weak:float=3
    rsi_weak:float=45
    rv_ratio:float=1.25
    vix_stress:float=25
    score_watch:int=3
    score_reduce:int=6
    score_critical:int=9
    max_quote_age_hours:float=96
    max_benchmark_age_hours:float=96
    max_vix_age_hours:float=36

    def __post_init__(self):
        values=asdict(self)
        if any(isinstance(v,bool) or not isinstance(v,(float,int)) or not isfinite(v) or v<=0 for k,v in values.items() if k!='name'):
            raise ValueError('Configuration values must be finite positive numbers')
        if not self.watch_dd<self.reduce_dd<self.critical_dd<100 or not self.score_watch<self.score_reduce<self.score_critical<=11:
            raise ValueError('Thresholds must be ordered')
        if any(type(getattr(self,k)) is not int for k in ('score_watch','score_reduce','score_critical')):
            raise ValueError('Score thresholds must be integers')


def catalogue():
    base=RiskV3Config()
    return (replace(base,name='sensitive',watch_dd=4,reduce_dd=6,critical_dd=18,fast_drop=5,score_watch=2,score_reduce=5,score_critical=8),
            base,replace(base,name='conservative',watch_dd=6,reduce_dd=10,critical_dd=25,fast_drop=9,score_watch=4,score_reduce=7,score_critical=10))


def finite(value):
    return not isinstance(value,bool) and isinstance(value,(float,int)) and isfinite(value)


def evaluate(symbol,decision_at,indicators,quality,*,variant='B',config=None,previous=None):
    if variant not in ('A','B','C'):raise ValueError('Unknown signal variant')
    config=config or RiskV3Config(); at=utc(decision_at)
    indicators=indicators if isinstance(indicators,dict) else {}
    quality=quality if isinstance(quality,dict) else {}
    unknown=set(indicators)-set(REQUIRED+OPTIONAL)
    if unknown:raise ValueError('Unknown/possibly forward-looking indicators: '+str(sorted(unknown)))
    values=dict(indicators); issues=[]; statuses={}
    for label,limit in (('quote',config.max_quote_age_hours),('qqq',config.max_benchmark_age_hours)):
        try:
            observed=utc(quality[label+'_observed_at']); available=utc(quality[label+'_available_at'])
            if observed>available or available>at:status='DATA_UNAVAILABLE'
            elif not 0<=(at-observed).total_seconds()/3600<=limit:status='STALE'
            else:status='OK'
        except (KeyError,ValueError,TypeError):status='DATA_UNAVAILABLE'
        statuses[label]=status
        if status!='OK':issues.append(label+': '+status)
    missing=[k for k in REQUIRED if not finite(values.get(k))]
    if missing:issues.append('Missing/nonfinite required indicators: '+', '.join(missing))
    if missing or 'DATA_UNAVAILABLE' in statuses.values():data_status='DATA_UNAVAILABLE'
    elif 'STALE' in statuses.values():data_status='STALE'
    else:data_status='OK'
    if any(finite(values.get(k)) and values[k]<=0 for k in ('close','ma20','ma50','ma200')):
        issues.append('Invalid positive price/MA/volatility denominator');data_status='DATA_UNAVAILABLE'
    if (finite(values.get('rsi14')) and not 0<=values['rsi14']<=100) or any(
        finite(values.get(k)) and values[k]<0 for k in ('rv20_pct','rv60_pct')):
        issues.append('Invalid RSI/realized-volatility range');data_status='DATA_UNAVAILABLE'
    optional_status={}
    for label,keys,limit in (('vix',('vix',),config.max_vix_age_hours),('sox',('relative_return_sox20_pp',),config.max_benchmark_age_hours)):
        try:
            observed=utc(quality[label+'_observed_at']); available=utc(quality[label+'_available_at'])
            status='OK' if observed<=available<=at and 0<=(at-observed).total_seconds()/3600<=limit else 'STALE_OR_FUTURE'
        except (KeyError,ValueError,TypeError):status='DATA_UNAVAILABLE'
        if any(not finite(values.get(k)) for k in keys) or (label=='vix' and values.get('vix',0)<=0):status='DATA_UNAVAILABLE'
        optional_status[label]=status
        if status!='OK':
            for key in keys:values[key]=None
    payload=dict(symbol=symbol,decision_at=at.isoformat(),variant=variant,configuration=config.name,
        data_status=data_status,quality=dict(quality,required_sources=statuses,optional_sources=optional_status,
            publication_vintage_verified=quality.get('publication_vintage_verified',False),
            optional_indicators_missing=[k for k in OPTIONAL if not finite(values.get(k))]),
        risk_level=None,indicators=values,conditions={},active_conditions=[],score=None,score_contributions={},
        change_reasons=issues,confidence='RESEARCH_RULE_MATCH_ONLY',research_only=True,
        score_used_for_decision=variant=='C',groups_used_for_decision=variant=='B',decision_predicates=None)
    if data_status!='OK':return payload
    i=values;c={}
    c.update(dd_watch=i['drawdown_20_pct']<=-config.watch_dd+1e-10,
        dd_reduce=i['drawdown_20_pct']<=-config.reduce_dd+1e-10,
        dd_critical=i['drawdown_60_pct']<=-config.critical_dd+1e-10,
        fast_drop=i['return_5_pct']<=-config.fast_drop,
        fall_accelerating=i['fall_acceleration_5_pp']<=-3,
        below_ma20=i['close']<i['ma20'],below_ma50=i['close']<i['ma50'],below_ma200=i['close']<i['ma200'],
        ma20_falling=i['ma20_slope_5_pct']<0,ma50_falling=i['ma50_slope_5_pct']<0,
        ma20_slope_deteriorating=i['ma20_slope_change_pp']<0,ma50_slope_deteriorating=i['ma50_slope_change_pp']<0,
        rsi_weak=i['rsi14']<config.rsi_weak,
        relative_qqq_weak=i['relative_return_qqq20_pp']<=-config.relative_weak,
        relative_sox_weak=i['relative_return_sox20_pp']<=-config.relative_weak if finite(i.get('relative_return_sox20_pp')) else None,
        realized_vol_elevated=i['rv60_pct']>0 and i['rv20_pct']>=i['rv60_pct']*config.rv_ratio,
        realized_vol_rising=i['rv20_change_5_ratio']>=.25 if finite(i.get('rv20_change_5_ratio')) else None,
        vix_stress=i['vix']>=config.vix_stress if finite(i.get('vix')) else None,
        support_broken=i['close']<i['support']*.99 if finite(i.get('support')) and i['support']>0 else None)
    groups=dict(price_path=c['dd_reduce'] or c['fast_drop'],
        trend=c['below_ma20'] and c['ma20_falling'] and (c['below_ma50'] or c['rsi_weak']),
        relative=c['relative_qqq_weak'] or c['relative_sox_weak'] is True,
        volatility=any(c[k] is True for k in ('realized_vol_elevated','realized_vol_rising','vix_stress')))
    families={'price_path':(('dd_watch','dd_reduce','fast_drop','fall_accelerating'),3),
        'trend':(('below_ma20','below_ma50','below_ma200','ma20_falling','ma20_slope_deteriorating','rsi_weak'),3),
        'relative':(('relative_qqq_weak','relative_sox_weak'),2),
        'volatility':(('realized_vol_elevated','realized_vol_rising','vix_stress'),2),
        'support':(('support_broken',),1)}
    contributions={name:dict(active=[k for k in keys if c[k] is True],raw_points=sum(c[k] is True for k in keys),cap=cap,
        points=min(cap,sum(c[k] is True for k in keys))) for name,(keys,cap) in families.items()}
    score=sum(v['points'] for v in contributions.values()); count=sum(groups.values())
    if variant=='A':
        critical=c['dd_critical'] and c['below_ma50'] and c['ma50_falling']
        reduce=c['dd_reduce'] and c['below_ma20'] and c['ma20_falling']
        watch=c['dd_watch'] or (c['fast_drop'] and c['below_ma20'])
    elif variant=='B':
        critical=groups['price_path'] and groups['trend'] and (count==4 or (c['dd_critical'] and count>=3))
        reduce=groups['price_path'] and count>=3
        watch=count>=1 or c['dd_watch']
    else:
        critical=score>=config.score_critical;reduce=score>=config.score_reduce;watch=score>=config.score_watch
    level='CRITICAL' if critical else 'REDUCE' if reduce else 'WATCH' if watch else 'HOLD'
    active=sorted(k for k,v in c.items() if v is True)
    reasons=[]
    if previous is None:reasons=['Initial observation; no previous signal']
    else:
        if previous.get('risk_level')!=level:reasons.append(str(previous.get('risk_level'))+' -> '+level)
        added=set(active)-set(previous.get('active_conditions',[]));cleared=set(previous.get('active_conditions',[]))-set(active)
        if added:reasons.append('Activated: '+', '.join(sorted(added)))
        if cleared:reasons.append('Cleared: '+', '.join(sorted(cleared)))
        if not reasons:reasons=['UNCHANGED']
    payload.update(risk_level=level,conditions=c,confirmation_groups=groups,active_conditions=active,
                   score=score,score_contributions=contributions,change_reasons=reasons,
                   decision_predicates=dict(watch=watch,reduce=reduce,critical=critical))
    return payload
