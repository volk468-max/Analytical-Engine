"""Offline independent sample reconciliation; never promotes full source qualification."""
import json,gzip,hashlib,re,html
from pathlib import Path
from datetime import datetime,timezone
try:
 from .preliminary import OUT,BASE,rounding_check,load_prices
except ImportError:
 from preliminary import OUT,BASE,rounding_check,load_prices
OLD=OUT.parent/'eod-calibration-ledger-v1'

def clean(raw):return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',raw.decode(errors='replace'))))
def mu_facts(issuer,exchange):
 a,b=clean(issuer),clean(exchange)
 # Issuer confirms record/payment, NOT ex-date; exchange explicitly supplies ex-date.
 declaration=bool(re.search(r'On September 25, 2024,.{0,150}declared a quarterly dividend of \$0\.115 per share, payable in cash on October 23, 2024,.{0,110}October 7, 2024',a))
 exchange_row=bool(re.search(r'MICRON TECHNOLOGY INC\*? US5951121038 0\.115 USD 10/07/2024 10/07/2024 10/23/2024',b))
 return dict(issuer_record_payment_amount=declaration,exchange_ex_record_payment_amount=exchange_row,reconciled=declaration and exchange_row)

def run(rawdir):
 sources=json.loads((OUT/'source-retrievals.json').read_text());bodies={}
 for r in sources:
  b=(Path(rawdir)/(r['id']+'.html')).read_bytes()
  if hashlib.sha256(b).hexdigest()!=r['sha256']:raise ValueError('EVIDENCE_HASH_MISMATCH')
  bodies[r['id']]=b
 mu=mu_facts(bodies['MU_ISSUER'],bodies['MU_VIENNA']);frames,dates,actions=load_prices();event=[x for x in actions if x['symbol']=='MU' and x['kind']=='dividends' and x['date']=='2024-10-07'];mu['frozen_provider_event']=event;mu['reconciled']=mu['reconciled'] and len(event)==1 and str(event[0]['record']['amount'])=='0.115'
 api=gzip.decompress((OLD/'evidence/QQQ_API.gz').read_bytes());expected=next(r['sha256'] for r in json.loads((OLD/'source-followups.json').read_text()) if r['id']=='QQQ_API')
 if hashlib.sha256(api).hexdigest()!=expected:raise ValueError('QQQ_API_EVIDENCE_HASH')
 record=next(r for r in json.loads(api)['data']['dividends']['rows'] if r['exOrEffDate']=='03/18/2024');qe=next(x for x in actions if x['symbol']=='QQQ' and x['kind']=='dividends' and x['date']=='2024-03-18');qqq=rounding_check(record['amount'].strip('$'),str(qe['record']['amount']),'2024-03-18',qe['date']);qqq.update(independent_record=record,source='Official Nasdaq API saved in v1; hash reverified',raw_sha256=expected,not_held_in_ABC=True,interpretation='ROUNDING_COMPATIBLE_NOT_VENDOR_POLICY_VERIFIED')
 counts={s:sum(x['symbol']==s and x['kind']=='dividends' for x in actions) for s in frames}
 result=dict(supersedes='v1 sample-level MU blocker only; v1 evidence unchanged',classification='RESEARCH_PRICE_REPLAY_NOT_PIT',MU_sample_reconciled=mu['reconciled'],MU=mu,QQQ=qqq,full_qualification=False,gate='BLOCKED_FULL_HISTORY_PIT_AND_INDEPENDENT_CONTINUITY',provider_dividend_counts=counts,facts=dict(MU_currency='USD',MU_amount='0.115',MU_announcement='2024-09-25',MU_ex_date='2024-10-07',MU_record_date='2024-10-07',MU_payment_date='2024-10-23'),residual_risks=['Full independent split/dividend/ex-date completeness unverified','Independent price/adjustment continuity for full history unverified','Historical provider vintages and availability unverified','Most dividend payment dates unknown; liquidity convention only','Surviving selected basket and reused test history','Provider licenses not attested; not live/executable input','Vienna notice is venue-specific; US settlement/API contract not independently audited','QQQ numeric rounding consistent, vendor rounding specification not independently confirmed'])
 (OUT/'action-reconciliation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(MU=mu['reconciled'],QQQ_rounding_compatible=qqq['compatible'],fully_qualified=False)))
if __name__=='__main__':
 import sys
 run(sys.argv[1])
