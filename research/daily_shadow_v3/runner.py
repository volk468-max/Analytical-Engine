"""Explicit one-shot research preparation; no service, cron, purchase or trade path."""
from .engine import candidates
from datetime import datetime,timezone
from research.daily_shadow.core import utc

def run(adapter,models,store,session,issued=None,decision=None,*,mode='SYNTHETIC',data_reviewed=False,live_approved=False,contract_id=None):
    if mode not in ('SYNTHETIC','RESEARCH_FORECAST'):raise ValueError('UNSUPPORTED_MODE')
    fixture=bool(adapter.transport.fixture)
    if mode=='RESEARCH_FORECAST':
        if not live_approved:raise PermissionError('SEPARATE_FIRST_LIVE_APPROVAL_REQUIRED')
        if fixture:raise PermissionError('FIXTURES_ARE_NOT_REAL_PROSPECTIVE_INPUTS')
        if contract_id is None:raise PermissionError('PRE_REGISTERED_LEGAL_CONTRACT_REQUIRED')
        permit=store.permit(contract_id)
        if permit!=adapter.permit:raise PermissionError('LEGAL_AUTHORITY_MISMATCH')
    elif not fixture:raise PermissionError('REAL_PROVIDER_CANNOT_RUN_AS_SYNTHETIC')
    if mode=='RESEARCH_FORECAST' and (issued is not None or decision is not None):raise PermissionError('LIVE_TIMESTAMPS_MUST_BE_ACTUAL_POST_COLLECTION_CLOCK')
    snapshot=adapter.collect(session);permit=adapter.permit
    if mode=='RESEARCH_FORECAST':issued=decision=datetime.now(timezone.utc).isoformat()
    elif issued is None or decision is None:raise ValueError('EXPLICIT_SYNTHETIC_CLOCK_REQUIRED')
    cid=store.register(permit,contract_id)
    rows=candidates(session,issued,decision,snapshot,models,permit,data_reviewed=data_reviewed)
    ref=None
    if snapshot.raw_responses and snapshot.legal_reason is None:ref=store.payload(cid,snapshot,permit.raw_until)
    key=mode+':'+session+':'+str(cid)
    ids=store.forecasts(key,rows,models,cid,ref,snapshot,mode)
    return dict(run_mode=mode,fixture=fixture,rows=len(rows),candidate_probabilities=sum(r['probability_raw'] is not None for r in rows),null_probabilities=sum(r['probability_raw'] is None for r in rows),actual_live_forecasts=0 if fixture else sum(r['probability_raw'] is not None for r in rows),model_status='MODEL_NOT_VALIDATED',training_status='TRAINING_REPLAY_NOT_PIT',ids=ids,contract_id=cid,payload_ref=ref),rows,snapshot
