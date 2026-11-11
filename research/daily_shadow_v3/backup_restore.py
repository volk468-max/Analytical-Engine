"""Local full-schema synthetic backup verification, never a vendor-retention exemption."""
import os,json,hashlib
import psycopg
from .store import restore_allowed

def verify():
    snapshots=[]
    for var,name in [('ALPHA_SHADOW_STAGE_DSN','alpha_shadow_research'),('ALPHA_SHADOW_RESTORE_DSN','alpha_shadow_restore')]:
        dsn=os.environ[var];info=psycopg.conninfo.conninfo_to_dict(dsn)
        if info.get('host') not in ('127.0.0.1','localhost') or info.get('dbname')!=name or info.get('user')!='alpha_shadow_test_app':raise ValueError('DISPOSABLE_LOOPBACK_ONLY')
        with psycopg.connect(dsn) as c:
            c.execute('set transaction read only')
            rows=c.execute('select kind,event_key,body_text,previous_hash,record_hash from alpha_research_v3.journal order by seq').fetchall()
            assert c.execute("select count(*) from alpha_research_v3.forecasts where run_mode='RESEARCH_FORECAST'").fetchone()[0]==0
            contracts=c.execute("select id from alpha_research_v3.contracts where body->>'scope'='LIVE'").fetchall();assert not contracts
            assert not restore_allowed(['SYNTHETIC_BACKUP_LICENSE_MANIFEST'],[],authority_fresh=False)
        prev=None
        for kind,key,body,prior,digest in rows:
            assert prior==prev and hashlib.sha256(((prev or '')+'|'+kind+'|'+key+'|'+body).encode()).hexdigest()==digest
            prev=digest
        snapshots.append(rows)
    assert snapshots[0]==snapshots[1]
    result=dict(classification='SYNTHETIC_DISPOSABLE_RESTORE_ONLY',research_journal_rows=len(snapshots[0]),original_equals_restored=True,hash_chain_verified=True,actual_research_forecasts=0,fresh_license_authority_required_before_real_backup_restore=True,production_touched=False)
    print(json.dumps(result,indent=2));return result
if __name__=='__main__':verify()
