"""No price refresh. Independent material-action evidence attempt, fail closed."""
import gzip,hashlib,json,urllib.request,urllib.error
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'reports/eod-calibration-ledger-v1';BASE=ROOT/'reports/model-portfolios-eod-v1'
SAMPLES=[('NVDA_2024','https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-first-quarter-fiscal-2025','2024-06-10','10:1'),('NVDA_2021','https://nvidianews.nvidia.com/news/nvidia-announces-four-for-one-stock-split-pending-stockholder-approval-at-annual-meeting-set-for-june-3','2021-07-20','4:1'),('MU_2024','https://investors.micron.com/quarterly-results','2024-10-07','.115'),('QQQ_2024','https://www.nasdaq.com/market-activity/etf/qqq/dividend-history','2024-03-18','.573')]
def run():
 frozen=[]
 for r in json.loads((BASE/'sources.json').read_text()):
  b=(BASE/'data'/(r['symbol']+'.json.gz')).read_bytes();raw=gzip.decompress(b);assert hashlib.sha256(raw).hexdigest()==r['raw_sha256'];frozen.append(dict(symbol=r['symbol'],raw_sha256=r['raw_sha256'],frozen_file_sha256=hashlib.sha256(b).hexdigest()))
 rows=[]
 for id,url,date,amount in SAMPLES:
  record=dict(id=id,url=url,retrieved_at=datetime.now(timezone.utc).isoformat(),expected_effective_date=date,expected_ratio_or_dividend=amount,license='UNKNOWN_NOT_ATTESTED',reconciled=False)
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'AlphaOS research public action audit'}),timeout=20) as r:b=r.read();record['http_status']=r.status;record['final_url']=r.url
   (OUT/'evidence'/(id+'.html.gz')).write_bytes(gzip.compress(b,mtime=0));record['sha256']=hashlib.sha256(b).hexdigest();record['evidence_file']='evidence/'+id+'.html.gz';record['status']='FETCHED_PENDING_DATED_EVENT_REVIEW'
  except (OSError,urllib.error.HTTPError) as e:record['status']='BLOCKED';record['error']=type(e).__name__;record['http_status']=getattr(e,'code',None)
  rows.append(record)
 (OUT/'action-audit.json').write_text(json.dumps(dict(frozen_price_hashes=frozen,samples=rows,all_actions_reconciled=False,gate='BLOCKED_PENDING_INDEPENDENT_RECONCILIATION',classification='RESEARCH_PRICE_REPLAY_NOT_PIT'),indent=2)+'\n');print(json.dumps(rows,indent=2))
if __name__=='__main__':run()
