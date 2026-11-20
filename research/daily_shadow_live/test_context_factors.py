"""Synthetic fixtures only; no Seeking Alpha licensed values in Git."""
import copy
import csv
import io
from datetime import datetime, timedelta, timezone
from itertools import product
from unittest.mock import Mock, MagicMock, patch

import pytest

from research.daily_shadow.core import future_sessions
from .context_factors import (FACTORS, SA_FIELDS, augment, digest, feature_record,
                              fit_correction, task)
from .context_runtime import calculate, export_context
from .forecast_export import HEADER, MODELS, export_session
from .portfolio import SYMBOLS

SESSION = '2026-11-19'
ISSUED = '2026-11-20T02:00:00Z'


def inputs():
    c = dict(schema_version='1.0', fixture=True, run_id='synthetic',
             created_at_utc='2026-11-20T01:59:00Z', information_cutoff_utc='2026-11-20T01:50:00Z',
             last_completed_session=SESSION, forecast_sessions=future_sessions(SESSION,10), horizon_sessions=10,
             instruments=[dict(symbol='AMD', data_status='SUFFICIENT', confidence_level='MEDIUM',
                               factor_scores={k: -20 for k in FACTORS})],
             events=[dict(published_at_utc='2026-11-19T22:00:00Z', retrieved_at_utc='2026-11-20T01:00:00Z')])
    fields = {k:dict(value=2, fiscal_period='FY2027', accounting_basis='NON_GAAP',
                     source_url='https://seekingalpha.com/symbol/AMD/earnings/revisions',
                     source_type='MANUAL_VERIFIED', published_at_utc='2026-11-19T22:00:00Z',
                     retrieved_at_utc='2026-11-20T01:00:00Z') for k in SA_FIELDS}
    s = dict(schema_version='SA_CONTEXT_V1', fixture=True, use_scope='PRIVATE_RESEARCH',
             instruments=[dict(symbol='AMD', data_status='VERIFIED_OBSERVATION', fields=fields)])
    return c,s


def baseline(**extra):
    return dict(session_date=SESSION,symbol='AMD',model='VOL',horizon=10,threshold_pct=5,
                label_type='LOW_INTRADAY', probability_raw=.3,status='RESEARCH_FORECAST',
                reason='LOW_SUPPORT',issued_at_utc=ISSUED,**extra)


def feature():
    return feature_record(*inputs(), 'AMD', SESSION, ISSUED, fixture=True)


def training():
    rows=[]
    for i in range(252):
        issued=datetime(2024,1,1,tzinfo=timezone.utc)+timedelta(days=i)
        f=feature(); f['available_at_utc']=issued.isoformat(); f['session']=issued.date().isoformat()
        f['values'][0]=(-1 if i%2 else 1)*.5
        f['record_sha256']=digest({k:v for k,v in f.items() if k!='record_sha256'})
        row=baseline(); row.update(session_date=f['session'],features=f,issued_at_utc=issued.isoformat(),
                                  maturity_at_utc=(issued+timedelta(days=20)).isoformat(),outcome=i%2)
        rows.append(row)
    return rows


def artifact():
    return fit_correction(training(),task(baseline()),'2026-11-19T00:00:00Z',fixture=True)


def test_signed_features_and_no_total_score_double_count():
    f=feature()
    assert f['status']=='CONTEXT_READY_FOR_RESEARCH'
    assert f['values'][:6]==[-.2]*6 and len(f['values'])==9
    assert f['values'][-1]==0


@pytest.mark.parametrize('fault,reason',[
    ('future','COEFFICIENT_NOT_AVAILABLE_ASOF'), ('stale','STALE_COEFFICIENT'),
    ('partial','COEFFICIENT_PARTIAL_OR_LOW_CONFIDENCE'),('missing','MISSING_OR_NONNUMERIC'),
    ('boolean','MISSING_OR_NONNUMERIC'), ('duplicate','COEFFICIENT_SYMBOL_NOT_UNIQUE'),
    ('horizon','COEFFICIENT_SESSION_OR_HORIZON_MISMATCH'), ('events','FUTURE_COEFFICIENT_EVIDENCE')])
def test_bad_coefficient_never_becomes_neutral(fault,reason):
    c,s=inputs()
    if fault=='future': c['created_at_utc']='2026-11-20T03:00:00Z'
    if fault=='stale': c['information_cutoff_utc']='2026-11-17T01:00:00Z'
    if fault=='partial': c['instruments'][0]['data_status']='PARTIAL'
    if fault=='missing': c['instruments'][0]['factor_scores']['macro_surprises']=None
    if fault=='boolean': c['instruments'][0]['factor_scores']['macro_surprises']=False
    if fault=='duplicate': c['instruments']*=2
    if fault=='horizon': c['horizon_sessions']=30
    if fault=='events': c['events'][0]['retrieved_at_utc']='2026-11-20T02:00:00Z'
    f=feature_record(c,s,'AMD',SESSION,ISSUED,fixture=True)
    assert reason in f['reasons'] and f['values'] is None


@pytest.mark.parametrize('field,value,reason',[
    ('source_url','https://seekingalpha.com/symbol/AMD?email_auth=secret','UNSAFE_OR_NONCANONICAL_SA_URL'),
    ('source_url','https://evil.example/symbol/AMD','UNSAFE_OR_NONCANONICAL_SA_URL'),
    ('retrieved_at_utc','2026-11-21T01:00:00Z','SEEKING_NOT_AVAILABLE_ASOF'),
    ('published_at_utc','2026-11-20T01:30:00Z','SEEKING_NOT_AVAILABLE_ASOF'),
    ('fiscal_period','FY2028','SEEKING_PERIOD_OR_BASIS_MISMATCH'),
    ('value',None,'MISSING_OR_NONNUMERIC'),
    ('source_type','EMAIL_HEADLINE','SEEKING_UNSUPPORTED_SOURCE_TYPE')])
def test_bad_seeking_inputs(field,value,reason):
    c,s=inputs(); s['instruments'][0]['fields'][SA_FIELDS[0]][field]=value
    f=feature_record(c,s,'AMD',SESSION,ISSUED,fixture=True)
    assert reason in f['reasons'] and f['values'] is None


def test_no_artifact_no_made_up_probability():
    r=baseline(); out=augment(r,feature())
    assert out['enhanced_probability_raw'] is None
    assert out['context_reason']=='NO_TRAINED_CONTEXT_ARTIFACT'
    assert out['baseline']==r


def test_trained_correction_is_separate_unqualified_and_input_unchanged():
    a=artifact(); f=feature(); r=baseline(); before=copy.deepcopy(r)
    out=augment(r,f,a)
    assert 0<out['enhanced_probability_raw']<1
    assert out['context_status']=='UNVALIDATED_CONTEXT_RESEARCH'
    assert not out['qualified'] and r==before and out['baseline']['reason']=='LOW_SUPPORT'
    assert a['beta'][1]<0  # synthetic positive score means fewer synthetic DOWN hits


@pytest.mark.parametrize('fault,reason',[
    ('sparse','INSUFFICIENT_PROSPECTIVE_CONTEXT_HISTORY'),
    ('future','TRAINING_NOT_POINT_IN_TIME_OR_UNMATURED'),
    ('duplicate','DUPLICATE_TRAINING_SESSION'),
    ('other_model','TRAINING_TARGET_MISMATCH'),
    ('fixture','TRAINING_CONTEXT_UNAVAILABLE')])
def test_training_rejects_leakage_and_mixed_targets(fault,reason):
    rows=training()
    if fault=='sparse': rows=rows[:251]
    if fault=='future': rows[0]['maturity_at_utc']='2027-01-01T00:00:00Z'
    if fault=='duplicate': rows.append(copy.deepcopy(rows[0]))
    if fault=='other_model': rows[0]['model']='RISK_FORECAST'
    if fault=='fixture': rows[0]['features']['fixture']=False
    with pytest.raises(ValueError,match=reason):
        fit_correction(rows,task(baseline()),'2026-11-19T00:00:00Z',fixture=True)


def test_no_retroactive_adjustment_no_30_session_reuse_and_no_unblocking():
    f=feature(); r=baseline(); r['issued_at_utc']='2026-11-20T01:00:00Z'
    assert augment(r,f)['context_reason']=='CONTEXT_NOT_AVAILABLE_AT_BASELINE_ISSUE'
    r=baseline(); r['horizon']=30
    assert augment(r,f)['context_reason']=='NO_30_SESSION_COEFFICIENT'
    r=baseline(); r['status']='STATUS_BLOCKED'; r['probability_raw']=None
    assert augment(r,f,artifact())['context_reason']=='BASELINE_BLOCKED'


def test_artifact_tampering_is_rejected():
    a=artifact(); a['beta'][0]=999
    assert augment(baseline(),feature(),a)['context_reason']=='INVALID_CONTEXT_ARTIFACT_OR_FEATURE_HASH'


def csv_blob():
    stream=io.StringIO(); w=csv.DictWriter(stream,fieldnames=HEADER); w.writeheader()
    for m in MODELS:
        for s,h,t,l in product(SYMBOLS+(('SPY','QQQ','SOXX') if m=='MARKET_PRECURSORS' else ()),
                                (10,30),(5,10,15),('LOW_INTRADAY','EOD_CLOSE')):
            r=baseline(); r.update(symbol=s,model=m,horizon=h,threshold_pct=t,label_type=l); w.writerow(r)
    return stream.getvalue().encode()


def test_full_516_contract_and_avgo_preserved():
    c,s=inputs(); c.pop('fixture'); s['fixture']=False
    output=calculate(csv_blob(),dict(session=SESSION,coefficients=c,seeking=s))
    assert len(output['rows'])==516
    assert sum(r['baseline']['symbol']=='AVGO' for r in output['rows'])==48
    assert not any(r['baseline']['symbol']=='NBIS' for r in output['rows'])
    assert not any(r['enhanced_probability_raw'] is not None for r in output['rows'])


def test_disabled_hook_does_not_read_or_emit():
    audit=Mock()
    with patch.dict('os.environ',{},clear=True):
        export_context(b'',audit,SESSION)
    audit.emit.assert_not_called()


def test_enabled_missing_bundle_emits_explicit_status():
    audit=Mock()
    with patch.dict('os.environ',{'ALPHA_CONTEXT_RESEARCH_ENABLED':'true'},clear=True):
        export_context(b'',audit,SESSION)
    assert audit.emit.call_args.kwargs['reason']=='CONTEXT_BUNDLE_NOT_CONFIGURED'


def test_incoherent_baseline_is_flagged_without_modification():
    rows=list(csv.DictReader(io.StringIO(csv_blob().decode())))
    for r in rows:
        if r['symbol']=='AMD' and r['model']=='VOL' and r['horizon']=='10':
            r['probability_raw']='0.1' if r['threshold_pct']=='5' else '0.5'
    stream=io.StringIO(); w=csv.DictWriter(stream,fieldnames=HEADER); w.writeheader(); w.writerows(rows)
    c,s=inputs(); c.pop('fixture'); s['fixture']=False
    output=calculate(stream.getvalue().encode(),dict(session=SESSION,coefficients=c,seeking=s))
    group=[r for r in output['rows'] if r['baseline']['symbol']=='AMD' and r['baseline']['model']=='VOL'
           and r['baseline']['horizon']=='10']
    assert len(group)==6 and all(r['context_reason']=='BASELINE_INCOHERENT' for r in group)
    assert group[0]['baseline']['probability_raw']=='0.1'


def test_context_failure_cannot_suppress_baseline_export_or_leak_error_text():
    rows=list(csv.DictReader(io.StringIO(csv_blob().decode())))
    tuples=[]
    for r in rows:
        r['horizon']=int(r['horizon']); r['threshold_pct']=int(r['threshold_pct'])
        r['probability_raw']=float(r['probability_raw']); r['issued_at_utc']=datetime.fromisoformat(ISSUED.replace('Z','+00:00'))
        tuples.append(tuple(r[k] for k in HEADER))
    store=MagicMock(); connection=store.connect.return_value.__enter__.return_value
    connection.execute.return_value.fetchall.return_value=tuples
    audit=Mock()
    with patch(export_context.__module__+'.export_context',side_effect=ValueError('sensitive input must not be emitted')):
        export_session(store,audit,SESSION)
    messages=[call.kwargs for call in audit.emit.call_args_list]
    assert any(m['phase']=='FORECAST_EXPORT' and m['status']=='READY' for m in messages)
    assert messages[-1]['reason']=='CONTEXT_INPUT_OR_CALCULATION_INVALID'
    assert 'sensitive input' not in str(messages)


def test_descriptive_audit_does_not_call_similarity_accuracy():
    from .model_audit import audit_predictions
    result=audit_predictions(csv_blob())
    assert all(p['exact_equal']==120 for p in result['pairs'])
    assert result['accuracy']=='NOT_EVALUATED_NO_MATURE_OUTCOMES'
    assert result['retirement_decision']=='NOT_SUPPORTED_BY_SINGLE_SESSION_SIMILARITY'


def test_rf_is_exactly_one_ensemble_component_not_the_whole_ensemble():
    from .test_vol import sample
    from . import risk_forecast_daily as rf, ensemble_daily as ens
    snap=sample(); q=sample('QQQ')
    snap.bars.update(q.bars); snap.splits.update(q.splits); snap.currency.update(q.currency)
    target=rf.series(('AMD',))[0]
    f=rf.frame(snap,'AMD'); e=ens.frame(snap,'AMD')
    cutoff='2026-11-16T00:00:00+00:00'; issued='2026-11-17T02:10:00+00:00'
    a=rf.artifact(f,target,cutoff,issued,'a'*64,fixture=True)
    b=ens.artifact(e,target,cutoff,issued,'a'*64,fixture=True)
    rf_p=rf.probability(a,rf.cell(f.iloc[-1]),issued)[0]
    components=ens.component_predictions(b,ens.cell(e.iloc[-1]))
    assert rf_p==components['technical_combined']['probability']
    assert len(components)==5 and a['n']==b['n'] and a['hits']==b['hits']
