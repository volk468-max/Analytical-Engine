"""Read-only verification of two explicitly named disposable loopback databases."""
import os,json,hashlib
import psycopg
from psycopg.conninfo import conninfo_to_dict

def verify_restore(original_dsn,restored_dsn):
 for dsn,name in [(original_dsn,'alpha_shadow_research'),(restored_dsn,'alpha_shadow_restore')]:
  info=conninfo_to_dict(dsn)
  if info.get('host') not in ('127.0.0.1','localhost') or info.get('dbname')!=name or info.get('user')!='alpha_shadow_test_app':raise ValueError('DISPOSABLE_LOOPBACK_RESTORE_ONLY')
 snapshots=[]
 for dsn in (original_dsn,restored_dsn):
  with psycopg.connect(dsn) as c:
   c.execute('set transaction read only');rows=c.execute('select kind,event_key,body_text,previous_hash,record_hash from alpha_shadow_v1.audit_events order by seq').fetchall();pros=c.execute("select count(*) from alpha_shadow_v1.forecast_runs where mode='PROSPECTIVE'").fetchone()[0];assert pros==0
  prev=None
  for kind,key,body,prior,digest in rows:
   assert prior==prev and hashlib.sha256(((prev or '')+'|'+kind+'|'+key+'|'+body).encode()).hexdigest()==digest
   prev=digest
  snapshots.append(rows)
 assert snapshots[0]==snapshots[1],'RESTORE_CONTENT_MISMATCH'
 result=dict(scope='DISPOSABLE_LOOPBACK_ONLY',audit_rows=len(snapshots[0]),original_equals_restored=True,hash_chain_valid=True,prospective_rows=0,production_touched=False)
 print(json.dumps(result,indent=2));return result
if __name__=='__main__':verify_restore(os.environ['ALPHA_SHADOW_STAGE_DSN'],os.environ['ALPHA_SHADOW_RESTORE_DSN'])
