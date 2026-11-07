"""Deterministic synthetic demonstration, NEVER actual user portfolio risk."""
import copy,json,hashlib
from pathlib import Path
from engine import *
OUT=Path(__file__).resolve().parents[2]/'reports/portfolio-risk-probability-v1'
def snapshot():
    t='2030-01-01T22:00:00+00:00'
    return dict(snapshot_id='SYNTHETIC-ONLY-1',decision_at=t,valuation_at=t,base_currency='USD',positions=[dict(symbol='FAKE',shares=1,currency='USD',price=100,price_at=t,source_hash='synthetic')],cash={'USD':20},fx={'USD':dict(rate=1,at=t,source_hash='synthetic')},source_hashes=['synthetic'],source_available_at=t,ingested_at=t,price_basis='RAW_UNADJUSTED',corporate_actions=[],cash_flows=[],peak_history=None,fees_assumptions=None)
def demo():
    s=snapshot();marks=[]
    for i in range(1,61):
        # Synthetic session ids, not a claimed exchange calendar.
        t=f'2030-03-{1+(i-1)//24:02d}T{(i-1)%24:02d}:00:00+00:00'
        marks.append(dict(session=i,at=t,prices={'FAKE':dict(price=87 if i==20 else 100,at=t,source_hash='synthetic')},fx={'USD':dict(rate=1,at=t,source_hash='synthetic')},actions_complete=True,actions=[],cash_accrual={'USD':0}))
    initial,path=nav_path(s,marks);label=touch_label(initial,path,list(range(1,61)),True)
    paths=[[1.0]*60,[.89]+[1.02]*59,[.8]*60,[1.1]*60]
    policy=Policy(.1,.2,2,2,.25);intents=[]
    for i,p in enumerate([.4,.55,.55,.65,.65,.65,.2,.2,.2,.2]):
        r=policy.step(p,i,synthetic=True)
        if r['intent']:
            intents.append(r['intent']);policy.settle(i+1,r['intent']['cumulative_trim_target'])
    log=[];append_record(log,dict(type='forecast',mode='SYNTHETIC_NOT_USER_PORTFOLIO',snapshot_hash=digest(s),code_sha=None,code_content_sha256=hashlib.sha256(Path(__file__).with_name('engine.py').read_bytes()).hexdigest(),model_sha=None,input_vintage='SYNTHETIC-v1',snapshot_id=s['snapshot_id'],decision_at=s['decision_at'],baseline_probability=None,final_probability=None,quality_flags=['SYNTHETIC_UNVALIDATED'],attribution=None,protocol_sha256=hashlib.sha256((OUT/'protocol.md').read_bytes()).hexdigest(),probability=None,interval=None,actual_forecast=False));append_record(log,dict(type='label',mode='SYNTHETIC',forecast_hash=log[0]['record_hash'],full_maturity=True,label=label))
    out=dict(mode='SYNTHETIC_NOT_USER_PORTFOLIO',actual_probability=None,actual_drawdown=None,fixture_initial_nav=initial,fixture_min_nav=min(r['nav'] for r in path),label=label,fixture_budget=drawdown_budget(90,100),synthetic_path_frequency=empirical_synthetic(paths),intents=intents,ladder_original_unit_target_at_120=ladder_target(120,100),shadow_log=log,chain_valid=verify_chain(log),economic_metrics={k:None for k in ('CAGR','max_DD','ES','turnover','trades','missed_upside','recovery')})
    (OUT/'demo.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n');return out
if __name__=='__main__':print(json.dumps(demo(),indent=2))
