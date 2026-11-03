"""Execute the unchanged main DecisionEngine for synthetic support fixtures only."""
import csv,json
from pathlib import Path
from aae.engines.decision_engine import DecisionEngine
ROOT=Path(__file__).resolve().parent
def snapshot(price):
    return dict(symbol='SYNTHETIC_NOT_HISTORICAL_FUNDAMENTALS',technical=dict(current_price=price,technical_score=40,rsi14=50,ma50=100,ma200=100),fundamental=dict(fundamental_score=80),risk=dict(risk_score=30),revisions=dict(revision_score=40),market={})
def main():
    engine=DecisionEngine();p=[dict(date='2026-10-01',close=100,low=99,high=101)];c=dict(date='2026-10-02',close=90,low=89,high=91)
    fixtures=[]
    for name,h in [('strict_prior',p),('include_current',p+[c]),('include_future',p+[dict(date='2026-10-03',close=1,low=1,high=1)])]:
        r=engine.evaluate(snapshot(90),h);fixtures.append(dict(case=name,support=r['range']['support'],support_broken=r['conditions']['support_broken'],synthetic_action=r['action'],warning='Synthetic fundamentals; not a historical decision replay'))
    (ROOT/'support-fixtures.json').write_text(json.dumps(fixtures,indent=2)+'\n')
    inp=json.loads((ROOT/'inputs.json').read_text());rows=[]
    for symbol in ['AMD','NVDA','MU','TSM','AVGO','AMAT','AMZN','META','PLTR','LRCX','NBIS']:
        bars=sorted((x for x in inp['prices'] if x['symbol']==symbol),key=lambda x:x['date'])
        for i,r in enumerate(bars):
            if r['date']<'2026-09-01':continue
            prior=bars[max(0,i-120):i];included=bars[max(0,i-119):i+1]
            a=min(x['low'] for x in prior);b=min(x['low'] for x in included)
            rows.append(dict(symbol=symbol,date=r['date'],close=r['close'],prior120_support=a,include_current120_support=b,prior_break=r['close']<a,include_break=r['close']<b,masked_break=r['close']<a and not r['close']<b,production_input_status='UNKNOWN',warmup_limited=len(prior)<120))
    with (ROOT/'support-impact.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
    print(json.dumps(dict(fixtures=fixtures,conditional_masked=len([r for r in rows if r['masked_break']]),first_by_stock={s:next((r['date'] for r in rows if r['symbol']==s and r['masked_break']),None) for s in sorted({r['symbol'] for r in rows})})))
if __name__=='__main__':main()
