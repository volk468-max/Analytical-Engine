"""Offline breadth calculations. No connectors, trades, signals or production imports."""
from datetime import datetime
import math
from statistics import mean

VERSION='breadth-prototype-v1'
def stamp(value):
    t=datetime.fromisoformat(value.replace('Z','+00:00'))
    if t.tzinfo is None:raise ValueError('timezone-aware availability required')
    return t

def adjust_splits(raw,actions,asof,decision_at):
    """Raw nominal bars -> as-of units; action ratio means new shares per old."""
    cutoff=stamp(decision_at);result=[]
    for r in raw:
        if r['date']>asof or stamp(r['available_at'])>cutoff:continue
        factor=1.
        for a in actions:
            if a['ratio']<=0:raise ValueError('invalid split ratio')
            if a['security_id']==r['security_id'] and r['date']<a['effective_date']<=asof and stamp(a['available_at'])<=cutoff:factor*=a['ratio']
        result.append(dict(r,**{k:r[k]/factor for k in ['high','low','close']}))
    return result

class BreadthEngine:
    def __init__(self,bars,calendar,memberships,metadata,min_coverage=1.):
        if not 0<min_coverage<=1:raise ValueError('coverage must be in (0,1]')
        self.calendar=list(calendar);self.dates=[x['date'] for x in calendar]
        if self.dates!=sorted(set(self.dates)):raise ValueError('unordered/duplicate calendar')
        self.index={d:i for i,d in enumerate(self.dates)};self.bars={};self.memberships=memberships;self.meta=metadata;self.minimum=min_coverage
        for r in bars:
            k=(r['security_id'],r['date'])
            if k in self.bars:raise ValueError('duplicate security/session; choose an as-of version explicitly')
            if r['date'] not in self.index:raise ValueError('bar outside session calendar')
            if r.get('price_basis',metadata.get('price_basis'))!=metadata.get('price_basis'):raise ValueError('mixed bar price basis')
            self.bars[k]=r
        for m in memberships:
            if len(m['members'])!=len(set(m['members'])):raise ValueError('duplicate member ID')
            stamp(m['available_at'])
        if metadata.get('price_basis') not in ['COMMON_SPLIT_UNITS_PRICE_ONLY','ASOF_SPLIT_ADJUSTED_PRICE_ONLY']:raise ValueError('explicit homogeneous split price basis required')

    def membership(self,date,decision_at):
        ms=[m for m in self.memberships if m['effective_date']<=date and stamp(m['available_at'])<=stamp(decision_at)]
        return max(ms,key=lambda m:(m['effective_date'],stamp(m['available_at']))) if ms else None

    def window(self,s,i,n,decision_at):
        if i-n+1<0:return None
        out=[];cutoff=stamp(decision_at)
        for d in self.dates[i-n+1:i+1]:
            x=self.bars.get((s,d));session=self.calendar[self.index[d]]
            if x is None or stamp(x['available_at'])>cutoff or stamp(x['available_at'])<stamp(session['close_at']):return None
            if not all(isinstance(x.get(k),(int,float)) and math.isfinite(x[k]) and x[k]>0 for k in ['close','high','low']):return None
            if not x['low']<=x['close']<=x['high']:return None
            out.append(x)
        return out

    def calculate(self,date,decision_at):
        i=self.index[date]
        if stamp(decision_at)<stamp(self.calendar[i]['close_at']):raise ValueError('session not closed')
        m=self.membership(date,decision_at);members=sorted(m['members']) if m else [];n=len(members)
        r=dict(date=date,decision_at=decision_at,universe=self.meta['universe'],members=';'.join(members),universe_size=n,membership_effective=m['effective_date'] if m else None,membership_kind=self.meta['membership_kind'],source=self.meta['source'],source_version=self.meta['source_version'],engine_version=VERSION,price_basis=self.meta['price_basis'],minimum_coverage=self.minimum)
        r['available_components']=sum(self.window(s,i,1,decision_at) is not None for s in members);r['coverage']=r['available_components']/n if n else 0
        r['missing_components']=';'.join(s for s in members if self.window(s,i,1,decision_at) is None)
        for period in [50,200]:
            ws=[w for s in members if (w:=self.window(s,i,period,decision_at)) is not None];den=len(ws);num=sum(w[-1]['close']>mean(x['close'] for x in w) for w in ws);coverage=den/n if n else 0
            r.update({f'eligible_ma{period}':den,f'above_ma{period}_count':num,f'coverage_ma{period}':coverage,f'pct_above_ma{period}_observed':100*num/den if den else None,f'pct_above_ma{period}':100*num/den if den and coverage>=self.minimum else None})
        ws=[w for s in members if (w:=self.window(s,i,2,decision_at)) is not None];a=sum(w[-1]['close']>w[-2]['close'] for w in ws);d=sum(w[-1]['close']<w[-2]['close'] for w in ws);u=len(ws)-a-d
        r.update(ad_eligible=len(ws),advances=a,declines=d,unchanged=u,coverage_ad=len(ws)/n if n else 0,ad_ratio_observed=a/d if d else None,ad_ratio_state='FINITE' if d else 'NO_DECLINERS' if a else 'NO_DIRECTIONAL_MOVES',ad_ratio=a/d if d and n and len(ws)/n>=self.minimum else None)
        ws=[w for s in members if (w:=self.window(s,i,253,decision_at)) is not None];hi=sum(w[-1]['high']>max(x['high'] for x in w[:-1]) for w in ws);lo=sum(w[-1]['low']<min(x['low'] for x in w[:-1]) for w in ws);cov=len(ws)/n if n else 0
        r.update(extrema_eligible=len(ws),coverage_extrema=cov,new_highs_observed=hi,new_lows_observed=lo,new_highs=hi if n and cov>=self.minimum else None,new_lows=lo if n and cov>=self.minimum else None)
        causes=[]
        for key in ['membership_history_complete','publication_times_verified','corporate_actions_verified','calendar_verified','security_ids_verified']:
            if not self.meta.get(key):causes.append(key.upper()+'_UNVERIFIED')
        for s in members:
            w=self.window(s,i,253,decision_at)
            if w and any(not x.get('publication_verified',False) for x in w):
                causes.append('BAR_PUBLICATION_UNVERIFIED');break
        if not m or not m.get('pit_verified'):causes.append('MEMBERSHIP_NOT_PIT')
        for k in ['coverage','coverage_ma50','coverage_ma200','coverage_ad','coverage_extrema']:
            if not n or r[k]<self.minimum:causes.append(k.upper()+'_INSUFFICIENT')
        r['historical_backtest_eligible']=not causes;r['quality_reasons']=';'.join(causes)
        return r

def divergence(current,previous,index_return_pct):
    """20-session lag supplied by caller; no fitting or action recommendation."""
    if current['members']!=previous['members'] or current['pct_above_ma50'] is None or previous['pct_above_ma50'] is None or index_return_pct is None:return None
    return index_return_pct>0 and current['pct_above_ma50']-previous['pct_above_ma50']<0
