"""Reproducible partial reconciliation from saved evidence, no fresh requests."""
import gzip,json,re,hashlib
from pathlib import Path
from datetime import datetime,timezone
from audit import OUT,BASE

def review():
 a=json.loads((OUT/'action-audit.json').read_text());provider=json.loads(gzip.decompress((BASE/'data/NVDA.json.gz').read_bytes()))['chart']['result'][0]
 for row in a['samples']:
  if 'evidence_file' not in row:continue
  b=gzip.decompress((OUT/row['evidence_file']).read_bytes());assert hashlib.sha256(b).hexdigest()==row['sha256'];text=re.sub(r'\s+',' ',re.sub('<[^>]+>',' ',b.decode(errors='replace')))
  if row['id'].startswith('NVDA'):
   phrase='June 10, 2024' if row['id']=='NVDA_2024' else 'July 20';ratio='Ten-for-one' if row['id']=='NVDA_2024' else 'Four-for-One';pos=text.find(phrase);matched=pos>=0 and ratio.lower() in text.lower();row['quoted_date_context']=text[max(0,pos-180):pos+200] if pos>=0 else None
   expected=10 if row['id']=='NVDA_2024' else 4;events=list(provider.get('events',{}).get('splits',{}).values());match=[e for e in events if e.get('numerator')/e.get('denominator')==expected and datetime.fromtimestamp(e['date'],timezone.utc).date().isoformat()==row['expected_effective_date']]
   row['provider_matching_ratio_events']=match;row['reconciled']=bool(matched and match);row['status']='PARTIAL_ISSUER_DATE_RATIO_MATCH' if row['reconciled'] else 'BLOCKED';row['limits']='2021 release conditional on approval; matches reported event, not independent full price/action history validation'
  elif row['id']=='QQQ_2024':row['status']='BLOCKED_NO_HISTORICAL_ROWS';row['reason']='Saved Nasdaq page states Data is currently not available; no dated amount/ex date to reconcile'
  else:row['status']='BLOCKED_NO_DATED_DIVIDEND_RECORD';row['reason']='Quarterly-results index is not the original 2024-09-25 dividend release; .115/ex-date record not present in obtained response'
 # Same-source API follow-up yielded an actual dated amount, unlike the HTML shell.
 followups=json.loads((OUT/'source-followups.json').read_text());raw_api=gzip.decompress((OUT/'evidence/QQQ_API.gz').read_bytes());assert hashlib.sha256(raw_api).hexdigest()==next(r['sha256'] for r in followups if r['id']=='QQQ_API')
 api=json.loads(raw_api)
 record=next(r for r in api['data']['dividends']['rows'] if r['exOrEffDate']=='03/18/2024')
 q=next(r for r in a['samples'] if r['id']=='QQQ_2024');q['independent_record']=record;q['independent_amount']=float(record['amount'].strip('$'));q['provider_amount']=.573;q['amount_difference']=q['independent_amount']-q['provider_amount'];q['status']='BLOCKED_AMOUNT_PRECISION_DISCREPANCY';q['reason']='Nasdaq API .57345 vs frozen Yahoo .573. QQQ not a held asset; small discrepancy is not proof of material portfolio error, but requires explicit reconciliation/tolerance review.'
 a['all_actions_reconciled']=all(r['reconciled'] for r in a['samples']);assert not a['all_actions_reconciled'];a['gate']='BLOCKED_MU_QQQ_ACTION_EVIDENCE';(OUT/'action-audit.json').write_text(json.dumps(a,indent=2)+'\n')
if __name__=='__main__':review()
