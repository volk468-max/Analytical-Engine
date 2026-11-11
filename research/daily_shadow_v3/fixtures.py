"""Self-authored artificial values. No vendor response or real daily prices here."""
import json,copy
from datetime import datetime,timezone
import pandas as pd
from research.daily_shadow.core import calendar,canonical,sha,requested_series
from .adapter import SYMBOLS

SESSION='2025-01-02'
ISSUED='2025-01-03T01:31:00+00:00' # 20:31 New York winter; a synthetic test clock.

class FixtureTransport:
    fixture=True
    def __init__(self):self.calls=0;self.revision=0;self.variant=None
    def get(self,path,query,secret):
        self.calls+=1
        if not secret:raise AssertionError('Fixture still exercises secret injection')
        if self.variant=='transport':raise ConnectionError('SYNTHETIC_FAILURE')
        if path.endswith('/US'):return canonical([dict(Code=s,Currency='EUR' if self.variant=='currency' and s=='MU' else 'USD') for s in SYMBOLS]).encode()
        symbol=path.rsplit('/',1)[1].split('.')[0]
        if '/splits/' in path:return b'[]'
        if '/div/' in path:return b'[]'
        dates=calendar().sessions_in_range('2024-01-02',SESSION).strftime('%Y-%m-%d').tolist()
        rows=[dict(date=d,open=100.,high=101.,low=99.,close=100.+(self.revision if d==SESSION else 0),adjusted_close=98.,volume=1000) for d in dates]
        if self.variant=='late':rows=rows[:-1]
        if self.variant=='mixed' and symbol=='MU':rows=rows[:-1]
        if self.variant=='duplicate':rows.append(rows[-1])
        if self.variant=='nan':rows[-1]['low']=float('nan')
        if self.variant=='wrongohlc':rows[-1]['low']=110.
        if self.variant=='missing':rows[-1].pop('close')
        return json.dumps(rows).encode()

def fixture_models():
    models=[]
    for symbol,label,t,h,name in requested_series():
        m=dict(name=name,fixture=True,qualified=False,calibrated=False,series=dict(symbol=symbol,label_type=label,threshold_pct=t,horizon=h),supported_tasks=[f'{label}:{t}:{h}'],created_at='2024-01-01T00:00:00+00:00',fit_cutoff='2024-01-01T00:00:00+00:00',count_bank=dict(n=100,hits=25,last_maturity='2023-12-01T00:00:00+00:00',groups={'UP':dict(n=50,hits=10),'DOWN':dict(n=30,hits=10),'MIXED':dict(n=20,hits=5)}),training_source_qualified=False)
        m['version']='fixture-v3-'+sha(canonical(m).encode());models.append(m)
    return models

def clock():return datetime.fromisoformat(ISSUED)

def outcome_window(original,forecast,close=90.5):
    """Self-authored future test marks, never vendor or historical validation."""
    from research.daily_shadow.core import future_sessions
    from .adapter import Snapshot
    days=future_sessions(forecast['session'],forecast['horizon'])
    bars={s:[dict(date=d,open=close,high=close+1,low=close-1,close=close,adjusted_close=close,volume=1000) for d in days] for s in SYMBOLS}
    raw={'SYNTHETIC_OUTCOME_WINDOW':canonical(bars).encode()}
    return Snapshot('EODHD',days[-1],'2025-06-01T00:00:00+00:00',None,True,None,bars,{s:[] for s in SYMBOLS},{s:[] for s in SYMBOLS},{s:'USD' for s in SYMBOLS},raw,sha(raw['SYNTHETIC_OUTCOME_WINDOW']),['fixture://self-authored-outcome-window'])
