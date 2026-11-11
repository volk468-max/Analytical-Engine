"""Read-only local synthetic full-v4 backup verification; never remote production."""
import os,json,hashlib
import psycopg

def verify():
 snapshots=[]
 for variable,db in [('ALPHA_SHADOW_STAGE_DSN','alpha_shadow_research'),('ALPHA_SHADOW_RESTORE_DSN','alpha_shadow_restore')]:
  url=os.environ[variable];info=psycopg.conninfo.conninfo_to_dict(url)
  if info.get('host') not in ('localhost','127.0.0.1') or info.get('dbname')!=db or info.get('user')!='alpha_shadow_test_app':raise ValueError('DISPOSABLE_LOOPBACK_ONLY')
  with psycopg.connect(url) as c:
   c.execute('set transaction read only');snapshot={}
   for table in ('receipts','reports','baselines','renewals','readiness'):
    rows=sorted(r[0] for r in c.execute('select to_jsonb(t)::text from alpha_operations_v4.'+table+' t').fetchall())
    snapshot[table]=dict(rows=len(rows),sha256=hashlib.sha256(json.dumps(rows).encode()).hexdigest())
  snapshots.append(snapshot)
 assert snapshots[0]==snapshots[1]
 result=dict(classification='SYNTHETIC_ISOLATED_ONLY',operation_counts=snapshots[0],exact_content_hash_match=True);print(json.dumps(result,indent=2));return result
if __name__=='__main__':verify()
