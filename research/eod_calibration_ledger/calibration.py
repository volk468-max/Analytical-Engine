"""Minimal frozen-bank/intercept calibrator; no global historical calibration."""
import math,json,hashlib,csv,io
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'reports/eod-calibration-ledger-v1'
def logistic(x):return 1/(1+math.exp(-max(-700,min(700,x))))
def logit(p):
 if not 0<p<1:raise ValueError('INVALID_PROBABILITY')
 return math.log(p/(1-p))
def calibrate(p,y,qualified_support=True):
 if len(p)!=len(y) or not p or any(v not in (0,1) for v in y):raise ValueError('BAD_CALIBRATION_ROWS')
 if not qualified_support:raise ValueError('LOW_EFFECTIVE_SUPPORT')
 z=[logit(x) for x in p];lo,hi=-10.,10.
 for _ in range(100):
  a=(lo+hi)/2;gradient=sum(logistic(x+a)-v for x,v in zip(z,y))+a
  if gradient>0:hi=a
  else:lo=a
 return (lo+hi)/2

def split(rows,year,calendar):
 train_boundary=next(i for i,d in enumerate(calendar) if d>=f'{year-3}-01-01');test_boundary=next(i for i,d in enumerate(calendar) if d>=f'{year}-01-01');cal_end=calendar[test_boundary-60]
 train=[r for r in rows if r['index']<train_boundary-60 and r['maturity']<f'{year-3}-01-01']
 cal=[r for r in rows if r['index']>=train_boundary+60 and r['date']<f'{year}-01-01' and r['maturity']<cal_end]
 test=[r for r in rows if r['index']>=test_boundary+60 and r['date'][:4]==str(year)]
 if not train or not cal or not test:raise ValueError('EMPTY_TEMPORAL_WINDOW')
 assert max(r['maturity'] for r in train)<min(r['date'] for r in cal)
 assert max(r['maturity'] for r in cal)<min(r['date'] for r in test)
 return train,cal,test

def frozen_probabilities(train,rows,key=None):
 base=(sum(r['y'] for r in train)+1)/(len(train)+2);out=[]
 for r in rows:
  subset=train if key is None else [t for t in train if t[key]==r[key]]
  out.append(base if key is None else (sum(t['y'] for t in subset)+20*base)/(len(subset)+20))
 return out

def blocked_results():
 audit=json.loads((OUT/'action-audit.json').read_text());qualified=audit['all_actions_reconciled']
 if qualified:raise RuntimeError('QUALIFIED_DATA_REQUIRES_SEPARATE_LEDGER_MILESTONE_REVIEW; no implicit stage upgrade')
 rows=[]
 for recipe in 'ABC':
  for model in ('HIST','REGIME','VOL','ROLLING_CLIMATOLOGY'):
   rows.append(dict(recipe=recipe,model=model,status='BLOCKED_ACTION_QUALIFICATION',brier=None,log_loss=None,bias=None,slope=None,ECE=None,effective_bin_support=None,threshold_35='NOT VALIDATED',threshold_51='NOT VALIDATED',threshold_60='NOT VALIDATED',calibrated_probability=None))
 s=io.StringIO();w=csv.DictWriter(s,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows);(OUT/'evaluation-status.csv').write_text(s.getvalue())
 # Explicitly synthetic, not estimates for the source portfolios.
 p=[.7]*300;y=[int(i%3==0) for i in range(300)];a=calibrate(p,y)
 demo=dict(mode='SYNTHETIC_ONLY_NOT_PORTFOLIO_EVIDENCE',n=300,p_raw=.7,intercept=a,p_calibrated=logistic(logit(.7)+a),true_personal_probability=None,actual_empirical_metrics=None)
 (OUT/'synthetic-calibration-demo.json').write_text(json.dumps(demo,indent=2)+'\n')
 return rows

def append(records,payload):
 r=dict(payload,previous_hash=records[-1]['hash'] if records else None);r['hash']=hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':')).encode()).hexdigest();records.append(r)
def shadow_mock():
 records=[];append(records,dict(type='forecast',mode='OFFLINE_SYNTHETIC',recorded_at='2030-01-01T22:00:00+00:00',code_sha=None,model_sha=None,protocol_sha256=hashlib.sha256((OUT/'protocol-calibration-ledger.md').read_bytes()).hexdigest(),source_hashes=[],snapshot_id='MOCK_A',recipe='A',label_type='EOD_CLOSE_TOUCH10_60',raw_probability=None,calibrated_probability=None,uncertainty=None,data_quality='UNQUALIFIED',stale=True));append(records,dict(type='label',forecast_hash=records[0]['hash'],status='IMMATURE',outcome=None))
 (OUT/'offline-log-mock.json').write_text(json.dumps(records,indent=2)+'\n')
if __name__=='__main__':blocked_results();shadow_mock()
