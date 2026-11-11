"""Explicit disposable staging only. No real data, API, license or live issuance."""
import os,uuid,json
from unittest.mock import patch
from cryptography.fernet import Fernet
from .store import ResearchStore
from .legal import Permit,fixture_permit
from .adapter import EODHDAdapter,VendorError
from .fixtures import *
from .runner import run
from .resolver import resolve
from .metrics import paired_metrics

def rehearse():
    dsn=os.environ['ALPHA_SHADOW_TEST_DSN']
    # Same hard local guard as integration tests, before any write.
    import psycopg
    info=psycopg.conninfo.conninfo_to_dict(dsn)
    if info.get('host') not in ('127.0.0.1','localhost') or info.get('dbname')!='alpha_shadow_research':raise ValueError('LOCAL_DISPOSABLE_ONLY')
    store=ResearchStore(dsn,Fernet.generate_key());models=fixture_models();suffix=str(uuid.uuid4())
    for m in models:m['version']+=':'+suffix
    with patch.dict(os.environ,{'EODHD_API_TOKEN':'synthetic-fixture-only'}):
        blocked_models=copy.deepcopy(models)
        for m in blocked_models:m['version']+=':separate-legal-block-scenario'
        blocked,_,_=run(EODHDAdapter(Permit('EODHD'),FixtureTransport(),clock),blocked_models,store,SESSION,ISSUED,ISSUED)
        p=fixture_permit();t=FixtureTransport();a=EODHDAdapter(p,t,clock)
        summary,rows,snap=run(a,models,store,SESSION,ISSUED,ISSUED,data_reviewed=True)
        # Frozen contract ID makes a retry use the original anchor and immutable IDs.
        retry,_,_=run(a,models,store,SESSION,ISSUED,ISSUED,data_reviewed=True,contract_id=summary['contract_id'])
        assert summary['ids']==retry['ids']
        t.variant='transport'
        try:a.collect(SESSION);raise AssertionError('Failure not injected')
        except VendorError:pass
        t.variant=None;t.revision=1;new=a.collect(SESSION);newref=store.payload(summary['contract_id'],new,p.raw_until)
        store.correction(suffix+':revision',summary['ids'][0],newref,new)
        assert store.private(summary['payload_ref'])['bars']['AMD'][-1]['close']==100
        fid=summary['ids'][0];f=dict(rows[0],id=str(fid));days=__import__('research.daily_shadow.core',fromlist=['future_sessions']).future_sessions(SESSION,f['horizon'])
        import pandas as pd
        future=[dict(date=d,close=100,low=99,available_at=calendar().session_close(pd.Timestamp(d)).isoformat()) for d in days]
        immature=resolve(f,100,future,[],ISSUED,data_reviewed=True);store.outcome(suffix+':immature',immature)
        mature=resolve(f,100,future,[],'2025-06-01T00:00:00Z',data_reviewed=True);oid=store.outcome(suffix+':mature',mature)
        store.outcome(suffix+':outcome-correction',dict(mature,outcome=True,supersedes_id=str(oid)))
        # Genuine own-backend loss rolls back pending health record; reconnect succeeds.
        try:
            with store.connect() as c:
                store.append(c,'HEALTH',suffix+':rollback',dict(status='SYNTHETIC',reason='INJECTED_DB_FAILURE'))
                c.execute('select pg_terminate_backend(pg_backend_pid())')
        except psycopg.Error:pass
        with store.connect() as c:assert c.execute('select count(*) from alpha_research_v3.journal where event_key=%s',(suffix+':rollback',)).fetchone()[0]==0
        purged=store.offboard(summary['contract_id'])
        assert purged==2
        assert store.verify() and store.legacy.verify()
    return dict(classification='SYNTHETIC_OFFLINE_NOT_VENDOR_QUALIFICATION',postgres_major=int(psycopg.connect(dsn).info.server_version//10000),requested_series=222,event_definitions=111,legal_blocked_null=blocked['null_probabilities'],fixture_candidate_probabilities=summary['candidate_probabilities'],fixture_portfolio_null=summary['null_probabilities'],actual_prospective_forecasts=0,actual_vendor_requests=0,actual_qualified_sources=0,source_publication_at=None,model_qualified_changed=False,calibrated_probabilities=0,idempotent_retry=True,source_revisions=2,frozen_original_anchor=True,full_horizon_outcome=mature['status'],own_backend_failure_recovered=True,offboard_active_payloads_deleted=purged,external_backup_purge='NOT_CLAIMED; separate independent receipt required',research_chain_verified=True,legacy_chain_verified=True,paired_live_metrics=store.metrics())
if __name__=='__main__':print(json.dumps(rehearse(),indent=2,sort_keys=True))
