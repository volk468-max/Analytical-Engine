"""Self-authored synthetic fixtures; no real licensed observations are committed."""
import copy
import csv
import io
import json
import os
import uuid
from datetime import datetime,timedelta,timezone
from unittest.mock import Mock,patch

import numpy as np
import pytest

from .alpha_full import (EXPERT,FEATURE_SCHEMA,MANIFEST,NAMES,VERSION,context,feature_vector,forecast,
                         key,repair_coherence,train)
from .context_factors import digest
from .test_context_factors import csv_blob,inputs,SESSION,ISSUED
from .alpha_full_runtime import load_bundle,run_full
from .forecast_export import HEADER


def blob_change(fn,*,session=SESSION,issued=ISSUED):
    rows=list(csv.DictReader(io.StringIO(csv_blob().decode())))
    for r in rows:
        r.update(session_date=session,issued_at_utc=issued);fn(r)
    stream=io.StringIO();w=csv.DictWriter(stream,fieldnames=HEADER);w.writeheader();w.writerows(rows)
    return stream.getvalue().encode()


def bundle():
    c,s=inputs()
    for field in s['instruments'][0]['fields'].values():field['forecast_period_role']='FY1'
    return dict(coefficients=c,seeking=s)


def test_cold_start_missing_optional_sources_still_forecasts_all120():
    body=forecast(csv_blob(),SESSION,ISSUED,fixture=True)
    assert len(body['rows'])==120 and MANIFEST['row_count']==120
    assert all(r['probability_raw'] is not None and not r['qualified'] and not r['calibrated'] for r in body['rows'])
    assert {r['weights_mode'] for r in body['rows']}=={'EXPERT_PRIOR_UNTRAINED'}
    assert all(r['missing_features'] and not r['context_provenance'] for r in body['rows'])
    assert sum(r['symbol']=='AVGO' for r in body['rows'])==12
    assert not any(r['symbol']=='NBIS' for r in body['rows'])


def test_available_partial_low_confidence_llm_changes10_but_not_reused_for30():
    b=bundle();e=b['coefficients']['instruments'][0]
    e.update(data_status='PARTIAL',confidence_level='LOW');e['factor_scores']['company_events']=None
    a=forecast(csv_blob(),SESSION,ISSUED,fixture=True)
    c=forecast(csv_blob(),SESSION,ISSUED,bundle={'coefficients':b['coefficients']},fixture=True)
    for x,y in zip(a['rows'],c['rows']):
        if x['symbol']=='AMD' and x['horizon']==10:
            assert y['probability_before_coherence']>x['probability_before_coherence']
            assert 'company_events' in y['missing_features']
        if x['horizon']==30:assert x['probability_before_coherence']==y['probability_before_coherence']


def test_known_neutral_and_unknown_have_different_masks():
    a=feature_vector({'company_events':0});b=feature_vector({});i=NAMES.index('company_events')
    assert a[i]==b[i]==0 and a[len(NAMES)+i]==0 and b[len(NAMES)+i]==1


@pytest.mark.parametrize('fault',['future','stale','horizon','fixture'])
def test_invalid_llm_ignored_without_blocking_technical_model(fault):
    b=bundle()
    if fault=='future':b['coefficients']['created_at_utc']='2030-01-01T00:00:00Z'
    if fault=='stale':b['coefficients']['information_cutoff_utc']='2026-11-01T00:00:00Z'
    if fault=='horizon':b['coefficients']['horizon_sessions']=30
    if fault=='fixture':b['coefficients']['fixture']=False
    body=forecast(csv_blob(),SESSION,ISSUED,bundle={'coefficients':b['coefficients']},fixture=True)
    assert all(r['probability_raw'] is not None for r in body['rows'])
    assert not any(r['context_provenance'] for r in body['rows'])


def test_seeking_fields_independent_missing_not_global_failure():
    b=bundle();fields=b['seeking']['instruments'][0]['fields'];fields['revenue_revision_30d_pct']['value']=None
    body=forecast(csv_blob(),SESSION,ISSUED,bundle={'seeking':b['seeking']},fixture=True)
    r=next(r for r in body['rows'] if r['symbol']=='AMD')
    assert 'sa_eps_revision' in r['features'] and 'sa_revision_breadth' in r['features']
    assert 'sa_revenue_revision' in r['missing_features']
    assert r['weights_mode']=='EXPERT_PRIOR_UNTRAINED'


def test_future_or_auth_tracking_seeking_observation_is_not_consumed():
    b=bundle();fields=b['seeking']['instruments'][0]['fields']
    fields['eps_revision_30d_pct']['retrieved_at_utc']='2030-01-01T00:00:00Z'
    fields['revenue_revision_30d_pct']['source_url']='https://seekingalpha.com/symbol/AMD?email_auth=private'
    values,reasons,refs=context(b,'AMD',SESSION,10,ISSUED,fixture=True)
    assert 'sa_eps_revision' not in values and 'sa_revenue_revision' not in values


def test_composite_grade_whitelist_and_separate30_session_llm():
    from research.daily_shadow.core import future_sessions
    b=bundle();o=copy.deepcopy(b['seeking']['instruments'][0]['fields']['eps_revision_30d_pct'])
    o.update(value='A+',accounting_basis='PROVIDER_COMPOSITE',fiscal_period='PROVIDER_CURRENT',article_body='MUST_NOT_ARCHIVE')
    b['seeking']['instruments'][0]['fields']['profitability_grade']=o
    c=copy.deepcopy(b['coefficients']);c['horizon_sessions']=30;c['forecast_sessions']=future_sessions(SESSION,30)
    b['coefficients_by_horizon']={'30':c}
    values,missing,refs=context(b,'AMD',SESSION,30,ISSUED,fixture=True)
    assert values['sa_profitability']==1 and 'monetary_policy' in values
    assert 'article_body' not in str(refs)


def test_ensemble_not_counted_as_independent_vote():
    poisoned=blob_change(lambda r:r.update(probability_raw=.99) if r['model']=='ENSEMBLE_RISK' else None)
    a=forecast(csv_blob(),SESSION,ISSUED,fixture=True);b=forecast(poisoned,SESSION,ISSUED,fixture=True)
    assert [r['probability_raw'] for r in a['rows']]==[r['probability_raw'] for r in b['rows']]


def test_base_fallback_and_all_base_blocked():
    body=forecast(blob_change(lambda r:r.update(status='STATUS_BLOCKED',probability_raw='') if r['model']=='VOL' else None),SESSION,ISSUED,fixture=True)
    assert all(r['baseline_model']=='RISK_FORECAST' for r in body['rows'])
    body=forecast(blob_change(lambda r:r.update(status='STATUS_BLOCKED',probability_raw='')),SESSION,ISSUED,bundle=bundle(),fixture=True)
    assert all(r['status']=='STATUS_BLOCKED' and r['probability_raw'] is None for r in body['rows'])


def test_all_nested_touch_constraints_repaired_explicitly():
    def alter(r):
        r['probability_raw']=.1 if r['threshold_pct']=='5' else .9
        if r['horizon']=='10':r['probability_raw']=float(r['probability_raw'])+.05
        if r['label_type']=='EOD_CLOSE':r['probability_raw']=float(r['probability_raw'])+.02
    body=forecast(blob_change(alter),SESSION,ISSUED,fixture=True)
    bank={key(r):r['probability_raw'] for r in body['rows']}
    for (s,h,t,l),p in bank.items():
        if t<15:assert p+1e-10>=bank[s,h,t+5,l]
        if h==10:assert p<=bank[s,30,t,l]+1e-10
        if l=='EOD_CLOSE':assert p<=bank[s,h,t,'LOW_INTRADAY']+1e-10
    assert any(abs(r['coherence_adjustment'])>0 for r in body['rows'])


def training(n=30,symbols=('AMD',)):
    out=[]
    for i in range(n):
        issued=datetime(2025,1,1,tzinfo=timezone.utc)+timedelta(days=i)
        for s in symbols:
            x=feature_vector({'company_events':.5 if i%2 else -.5})
            out.append(dict(session=issued.date().isoformat(),symbol=s,issued_at=issued.isoformat(),
                maturity_at=(issued+timedelta(days=20)).isoformat(),outcome_available_at=(issued+timedelta(days=21)).isoformat(),
                target=[10,5,'LOW_INTRADAY'],feature_names=list(NAMES),feature_schema_sha256=FEATURE_SCHEMA,
                x=x,offset=0.,y=1-i%2,fixture=False))
    return out


def test_learning_starts_with_pooled_history_without252_session_gate():
    a=train(training(),(10,5,'LOW_INTRADAY'),ISSUED)
    assert a['kind']=='LEARNED_POOLED_EXPERIMENTAL' and not a['qualified'] and a['distinct_sessions']==30
    b=train(training(symbols=('AMD','NVDA','AVGO')),(10,5,'LOW_INTRADAY'),ISSUED)
    assert b['n']==90 and b['distinct_sessions']==30
    assert np.allclose(a['beta'],b['beta'],atol=1e-7)
    assert train(training(19,('AMD','NVDA')),(10,5,'LOW_INTRADAY'),ISSUED) is None


@pytest.mark.parametrize('fault',['future','duplicate','fixture','feature_version'])
def test_training_rejects_leakage_fixture_and_corrupt_archive(fault):
    rows=training()
    if fault=='future':rows[0]['outcome_available_at']='2030-01-01T00:00:00Z'
    if fault=='duplicate':rows.append(rows[0])
    if fault=='fixture':rows[0]['fixture']=True
    if fault=='feature_version':rows[0]['feature_names']=[]
    with pytest.raises(ValueError):train(rows,(10,5,'LOW_INTRADAY'),ISSUED)


def test_learned_artifact_used_and_tamper_rejected():
    a=train(training(),(10,5,'LOW_INTRADAY'),ISSUED)
    b=forecast(csv_blob(),SESSION,ISSUED,artifacts={(10,5,'LOW_INTRADAY'):a},fixture=True)
    assert sum(r['weights_mode']=='LEARNED_POOLED_EXPERIMENTAL' for r in b['rows'])==10
    a['beta'][0]=1234
    with pytest.raises(ValueError,match='INVALID_LEARNED_ARTIFACT'):
        forecast(csv_blob(),SESSION,ISSUED,artifacts={(10,5,'LOW_INTRADAY'):a},fixture=True)


def test_bundle_delivery_and_historical_bootstrap_protection():
    import base64
    with patch.dict(os.environ,{'ALPHA_FULL_BUNDLE_B64':base64.b64encode(b'{"seeking":{}}').decode()},clear=True):
        assert load_bundle()=={'seeking':{}}
    store=Mock();audit=Mock()
    with patch.dict(os.environ,{'ALPHA_FULL_ENABLED':'true'},clear=True):
        run_full(store,audit,b'',SESSION,now=datetime(2027,1,1,tzinfo=timezone.utc))
    store.connect.assert_not_called()
    assert audit.emit.call_args.kwargs['reason']=='OUTSIDE_PROSPECTIVE_WINDOW'


def test_full_export_reconstructs_exact_archived_json_with_small_private_chunks():
    import base64,gzip,hashlib
    from .alpha_full_runtime import emit_export
    from research.daily_shadow.core import canonical
    body=forecast(csv_blob(),SESSION,ISSUED,fixture=True);audit=Mock()
    emit_export(audit,body,'synthetic-run')
    records=[c.kwargs for c in audit.emit.call_args_list];ready=records[-1];chunks=records[:-1]
    assert ready['status']=='READY' and ready['row_count']==120 and ready['learned']==0
    assert [c['chunk_index'] for c in chunks]==list(range(ready['chunk_count']))
    payload=gzip.decompress(base64.b64decode(''.join(c['payload_b64'] for c in chunks)))
    assert payload==canonical(body).encode() and hashlib.sha256(payload).hexdigest()==ready['json_sha256']


@pytest.mark.skipif(not os.environ.get('ALPHA_SHADOW_TEST_DSN'),reason='Disposable PG required')
class TestFullSQL:
    def connect(self):
        import psycopg
        url=os.environ['ALPHA_SHADOW_TEST_DSN'];info=psycopg.conninfo.conninfo_to_dict(url)
        assert info.get('host') in ('127.0.0.1','localhost') and info.get('dbname')=='alpha_shadow_research'
        c=psycopg.connect(url);c.execute('set role alpha_shadow_writer');return c

    def body(self):
        from .runtime import latest_completed
        from research.daily_shadow.core import calendar
        import pandas as pd
        now=datetime.now(timezone.utc);session=latest_completed(now)
        if (now-calendar().session_close(pd.Timestamp(session)).to_pydatetime()).total_seconds()>=36*3600:
            pytest.skip('Outside genuine prospective SQL test window')
        body=forecast(blob_change(lambda r:None,session=session,issued=(now-timedelta(seconds=1)).isoformat()),session,now.isoformat())
        version='ALPHA_FULL_V1-'+uuid.uuid4().hex[:16]
        body['model_version']=version
        for r in body['rows']:r['model_version']=version
        return body

    def test_atomic_archive_idempotent_immutable_and_prior_tables_untouched(self):
        import psycopg
        from research.daily_shadow.core import canonical
        b=self.body()
        with self.connect() as c:
            prior=c.execute('select count(*) from alpha_research_v3.forecasts').fetchone()[0]
            first=c.execute('select alpha_full_v1.record(%s,%s)',(uuid.uuid4(),canonical(b))).fetchone()[0]
            again=c.execute('select alpha_full_v1.record(%s,%s)',(uuid.uuid4(),canonical(b))).fetchone()[0]
            assert first==again
            assert c.execute('select jsonb_array_length(body->\'rows\') from alpha_full_v1.runs where id=%s',(first,)).fetchone()[0]==120
            assert c.execute('select count(*) from alpha_research_v3.forecasts').fetchone()[0]==prior
        with pytest.raises(psycopg.Error),self.connect() as c:
            c.execute('delete from alpha_full_v1.runs where id=%s',(first,))

    def test_training_reader_requires_exact_resolved_baseline_references(self):
        from .alpha_full_runtime import learning_records
        from types import SimpleNamespace
        records=learning_records(SimpleNamespace(connect=self.connect),datetime.now(timezone.utc).isoformat())
        assert records==[]  # Self-authored SQL archive fixtures have no real baseline references/outcomes.

    @pytest.mark.parametrize('fault',['fixture','duplicate','retired','null','incoherent','backdate'])
    def test_sql_rejects_invalid_journal(self,fault):
        import psycopg
        from research.daily_shadow.core import canonical
        b=self.body()
        if fault=='fixture':b['fixture']=True
        if fault=='duplicate':b['rows'][0]=copy.deepcopy(b['rows'][1])
        if fault=='retired':b['rows'][0]['symbol']='NBIS'
        if fault=='null':b['rows'][0]['qualified']=None
        if fault=='backdate':
            b['session']='2025-01-02'
            for r in b['rows']:r['session']=b['session']
        if fault=='incoherent':
            b['rows'][0]['probability_raw']=0
            b['rows'][2]['probability_raw']=1
        with pytest.raises(psycopg.Error),self.connect() as c:
            c.execute('select alpha_full_v1.record(%s,%s)',(uuid.uuid4(),canonical(b)))
