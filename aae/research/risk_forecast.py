"""Research barrier labels and frozen empirical probability estimators, no trades."""
from bisect import bisect_right
from collections import defaultdict
from dataclasses import dataclass
from math import isfinite
from aae.backtest.simulator import utc

MODELS=('historical','drawdown','volatility','ma50_rsi','v3_state','v3_score',
        'technical_combined','technical_plus_v3')


def barrier_label(bars,index,horizon,threshold):
    """Forward labels only. Never passed to features or predict()."""
    if type(index) is not int or not 0<=index<len(bars):raise ValueError('Invalid anchor index')
    if type(horizon) is not int or horizon<1 or not 0<threshold<1:
        raise ValueError('Invalid label horizon/threshold')
    anchor=bars[index];future=bars[index+1:index+horizon+1]
    if future and future[0].open_at<=anchor.available_at:
        raise ValueError('Forecast anchor not available before future session')
    complete=len(future)==horizon
    tolerance=anchor.close*1e-12  # inclusive barriers must be invariant to price-unit scaling
    down=anchor.close*(1-threshold);up=anchor.close*(1+threshold)
    lo=next((b for b in future if b.low<=down+tolerance),None)
    hi=next((b for b in future if b.high>=up-tolerance),None)
    if lo and hi:
        if lo.open_at<hi.open_at:order='DOWN_FIRST'
        elif hi.open_at<lo.open_at:order='UP_FIRST'
        elif lo.open<=down+tolerance:order='DOWN_FIRST_AT_OPEN'
        elif lo.open>=up-tolerance:order='UP_FIRST_AT_OPEN'
        else:order='UNKNOWN_INTRADAY'
    elif lo:order='DOWN_ONLY'
    elif hi:order='UP_ONLY'
    else:order='NEITHER'
    return dict(complete=complete,down_hit=bool(lo) if complete else None,
        up_hit=bool(hi) if complete else None,observed_down_hit=bool(lo),observed_up_hit=bool(hi),
        down_hit_date=lo.close_at.date().isoformat() if lo else None,
        up_hit_date=hi.close_at.date().isoformat() if hi else None,hit_order=order,
        terminal_return_pct=(future[-1].close/anchor.close-1)*100 if complete else None,
        label_available_at=future[-1].available_at.isoformat() if complete else None,
        horizon_end_date=future[-1].close_at.date().isoformat() if complete else None,
        observed_sessions=len(future))


@dataclass(frozen=True)
class ForecastFeatures:
    state:str
    score:int
    drawdown_20_pct:float
    rv20_pct:float
    close:float
    ma50:float
    rsi14:float

    def __post_init__(self):
        if self.state not in ('HOLD','WATCH','REDUCE','CRITICAL') or type(self.score) is not int or not 0<=self.score<=11:
            raise ValueError('Invalid frozen v3 state/score')
        if any(not isfinite(v) for v in (self.drawdown_20_pct,self.rv20_pct,self.close,self.ma50,self.rsi14)):
            raise ValueError('Nonfinite predictor')
        if self.close<=0 or self.ma50<=0 or self.rv20_pct<0 or not 0<=self.rsi14<=100:
            raise ValueError('Invalid technical predictor')

    def cells(self):
        dd=bisect_right((5,10,15,25),max(0,-self.drawdown_20_pct))
        vol=bisect_right((20,40,60,80,120),self.rv20_pct)
        technical=(self.close<self.ma50,bisect_right((30,45,55,70),self.rsi14))
        score=bisect_right((3,5,7,9),self.score)
        combined=(dd,vol,*technical)
        return dict(historical=(),drawdown=(dd,),volatility=(vol,),ma50_rsi=technical,
            v3_state=(self.state,),v3_score=(score,),technical_combined=combined,
            technical_plus_v3=(*combined,self.state,score))


class ProbabilityBank:
    """A per-stock/task/year estimator. Future outcomes are filtered inside fit."""
    def __init__(self,cutoff,strength=20):
        self.cutoff=utc(cutoff)
        if not isfinite(strength) or strength<=0:raise ValueError('Invalid shrinkage')
        self.strength=strength
        self.cells={m:defaultdict(lambda:[0,0,set()]) for m in MODELS}
        self.n=self.positives=0
        self._fitted=False
        self.last_maturity=None
        self.last_anchor=None

    def fit(self,rows):
        if self._fitted:raise ValueError('Estimator is frozen after fitting')
        self._fitted=True
        for row in rows:
            if row['target'] is None or row.get('label_available_at') is None:continue
            maturity=utc(row['label_available_at']);anchor=utc(row['decision_at'])
            if maturity>self.cutoff or anchor>=self.cutoff:continue
            if maturity<=anchor:raise ValueError('Outcome cannot predate anchor')
            if type(row['target']) is not bool:raise ValueError('Binary target required')
            self.n+=1;self.positives+=row['target']
            self.last_maturity=max(self.last_maturity or maturity,maturity)
            self.last_anchor=max(self.last_anchor or anchor,anchor)
            for model,key in row['features'].cells().items():
                stats=self.cells[model][key];stats[0]+=1;stats[1]+=row['target'];stats[2].add(row['calendar_index']//40)
        return self

    def predict(self,features):
        if not isinstance(features,ForecastFeatures):raise TypeError('Causal feature object required')
        if not self.n:return {m:dict(probability=None,status='DATA_UNAVAILABLE',cell_n=0) for m in MODELS}
        keys=features.cells();base=(self.positives+1)/(self.n+2)
        output={}
        for model in MODELS:
            n,pos,blocks=self.cells[model].get(keys[model],(0,0,set()))
            parent=output['technical_combined']['probability'] if model=='technical_plus_v3' else base
            p=base if model=='historical' else (pos+self.strength*parent)/(n+self.strength)
            output[model]=dict(probability=p,status='SUPPORTED_RESEARCH_ESTIMATE' if n>=60 and pos>=10 and n-pos>=10 and len(blocks)>=5 else 'LOW_SUPPORT',
                cell_n=n,cell_positive=pos,cell_negative=n-pos,cell_blocks=len(blocks),
                backoff=n==0,training_n=self.n,training_positive=self.positives,
                training_last_maturity=self.last_maturity.isoformat(),training_last_anchor=self.last_anchor.isoformat())
        return output
