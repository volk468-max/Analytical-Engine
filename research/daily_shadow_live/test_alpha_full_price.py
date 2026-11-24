"""Self-authored signed-return fixtures; never vendor quotes or live backfills."""
import copy,json,os,uuid
from datetime import datetime,timezone,timedelta
from types import SimpleNamespace
import numpy as np
import pytest
from . import alpha_full_price as price
from .test_vol import sample,SESSION,NOW
from .test_alpha_full import bundle
from .alpha_full_price_runtime import collect_frames,evaluation,training_records
from research.daily_shadow_v3.legal import fixture_permit
from research.daily_shadow_v3.adapter import VendorError


def frames(symbols=('AMD','NVDA','QQQ','SPY','SOXX'),count=180):
    result={s:price.price_frame(sample(s,count=count),s) for s in symbols}
    price.attach_market(result);return result


def test_signed_price_targets25_times2_distinct_from_touch():
    result=price.forecast(frames(),{},SESSION,NOW,fixture=True)
    assert len(price.SYMBOLS)==len(set(price.SYMBOLS))==25
    assert len(result['rows'])==50 and len(result['market_rows'])==6
    numeric=[r for r in result['rows'] if r['expected_return_pct'] is not None]
    assert len(numeric)==4 and {r['symbol'] for r in numeric}=={'AMD','NVDA'}
    assert all(r['band_low_pct']<=r['expected_return_pct']<=r['band_high_pct'] for r in numeric)
    assert all(r['weights_mode']=='EXPERT_CONTEXT_PRIOR' and not r['calibrated'] for r in numeric)
    assert result['label_definition'].startswith('TERMINAL_CLOSE')
    assert 'probability_raw' not in numeric[0]


def test_missing_market_proxy_or_one_stock_does_not_stop_other_forecasts():
    f=frames(('AMD',));result=price.forecast(f,{'NVDA':'SOURCE_DOWN'},SESSION,NOW,fixture=True)
    assert sum(r['expected_return_pct'] is not None for r in result['rows'])==2
    assert all(r['reason']=='SOURCE_DOWN' for r in result['rows'] if r['symbol']=='NVDA')
    assert all(not r['qualified'] for r in result['rows'])


def test_collection_isolates_failure_and_unverified_identity():
    def collector(s):
        if s=='AMD':raise VendorError('SOURCE_TIMEOUT')
        return sample(s,count=80)
    f,failed,snapshots=collect_frames(fixture_permit(),SESSION,collector=collector)
    assert failed['AMD']=='SOURCE_TIMEOUT'
    assert 'NVDA' in f and 'QQQ' in f and 'SCZM' not in failed


def test_collection_archives_each_snapshot_before_fetching_next():
    events = []

    def collect(symbol):
        events.append(('collect', symbol))
        return sample(symbol, count=80)

    def archive(symbol, snapshot):
        events.append(('archive', symbol))
        if symbol == 'AMD':
            raise RuntimeError('archive unavailable')
        return ('ref', snapshot.revision, snapshot.retrieved_at)

    frames, failures, sources = collect_frames(
        fixture_permit(), SESSION, collector=collect, archive=archive,
    )
    assert events[::2] == [('collect', symbol) for _, symbol in events[1::2]]
    assert all(kind == 'archive' for kind, _ in events[1::2])
    assert failures['AMD'] == 'SOURCE_ARCHIVE_UNAVAILABLE'
    assert 'AMD' not in sources and 'AMD' not in frames
    assert sources['NVDA'][0] == 'ref'


def test_verified_identity_cannot_extend_portfolio():
    identity={'SCZM':dict(provider_symbol='SCZM.US',currency='USD',status='VERIFIED',
                         source_url='https://eodhd.com/',verified_at_utc=datetime.now(timezone.utc).isoformat())}
    f,failed,_=collect_frames(fixture_permit(),SESSION,collector=lambda s:sample(s,count=80),identities=identity)
    assert 'SCZM' not in f and 'STRIP' not in failed


def test_signed_llm_scores_affect_price_and_no10_to30_reuse():
    b=bundle();c=b['coefficients'];c['last_completed_session']=SESSION
    from research.daily_shadow.core import future_sessions
    c['forecast_sessions']=future_sessions(SESSION,10)
    c['created_at_utc']=NOW;c['information_cutoff_utc']='2026-11-17T01:50:00Z'
    c['events']=[dict(published_at_utc='2026-11-16T21:00:00Z',retrieved_at_utc='2026-11-17T01:00:00Z')]
    f=frames(('AMD',));a=price.forecast(f,{},SESSION,NOW,fixture=True)
    d=price.forecast(f,{},SESSION,NOW,bundle={'coefficients':c},fixture=True)
    pairs=[(x,y) for x,y in zip(a['rows'],d['rows']) if x['symbol']=='AMD']
    assert pairs[0][1]['expected_return_pct']<pairs[0][0]['expected_return_pct']
    assert pairs[1][1]['expected_return_pct']==pairs[1][0]['expected_return_pct']


def test_market_proxy_uses_its_own_profile_not_a_stock_score():
    from research.daily_shadow.core import future_sessions
    b=bundle();c=b['coefficients'];c['last_completed_session']=SESSION
    c['forecast_sessions']=future_sessions(SESSION,10);c['created_at_utc']=NOW
    c['information_cutoff_utc']='2026-11-17T01:50:00Z'
    c['events']=[dict(published_at_utc='2026-11-16T21:00:00Z',retrieved_at_utc='2026-11-17T01:00:00Z')]
    c['instruments'][0]['symbol']='QQQ'
    x,missing,refs=price.context_vector({'market_coefficients_by_horizon':{'10':c}},'QQQ',SESSION,10,NOW,fixture=True)
    assert x[price.CONTEXT_NAMES.index('monetary_policy')]<0 and 'monetary_policy' in refs


def test_future_series_blocks_only_affected_symbol():
    f=frames(('AMD','NVDA'));f['AMD']=f['AMD'].rename(index={SESSION:'2030-01-01'})
    body=price.forecast(f,{},SESSION,NOW,fixture=True)
    assert all(r['expected_return_pct'] is None for r in body['rows'] if r['symbol']=='AMD')
    assert all(r['expected_return_pct'] is not None for r in body['rows'] if r['symbol']=='NVDA')


def test_training_head_excludes_labels_not_mature_by_fit_time():
    f=frames(('AMD',),count=180);a=price.fit_prices(f,10,NOW)
    b=price.fit_prices(f,10,'2026-09-01T23:00:00Z')
    assert b['n']<a['n'] and a['qualified'] is False


def test_company_assessment_monthly_cache_is_signed_and_stale_independent():
    b={'company_assessments_by_horizon':{'10':{'AMD':dict(fundamental_score=50,
         fundamental_score_asof_utc='2026-11-01T00:00:00Z',analyst_score=-20,
         analyst_score_asof_utc='2026-01-01T00:00:00Z',confidence_level='MEDIUM',
         source_record_sha256='a'*64,fixture=True)}}}
    x,missing,refs=price.context_vector(b,'AMD',SESSION,10,NOW,fixture=True)
    assert x[price.CONTEXT_NAMES.index('fundamental_assessment')]==.25
    assert 'analyst_assessment' in missing and 'fundamental_assessment' in refs


def test_malformed_optional_structure_does_not_stop_other_sources_or_positions():
    b=bundle();b['coefficients_by_horizon']=[];b['company_assessments_by_horizon']=[]
    from research.daily_shadow.core import future_sessions
    c=b['coefficients'];c.update(last_completed_session=SESSION,forecast_sessions=future_sessions(SESSION,10),
         created_at_utc=NOW,information_cutoff_utc='2026-11-17T01:50:00Z',
         events=[dict(published_at_utc='2026-11-16T21:00:00Z',retrieved_at_utc='2026-11-17T01:00:00Z')])
    b['coefficients']['instruments'].append(None);b['seeking']['instruments'].append(None)
    b['seeking']['instruments'][0]['fields']['eps_revision_30d_pct']['source_url']=42
    r=price.forecast(frames(('AMD','NVDA')),{},SESSION,NOW,bundle=b,fixture=True)
    assert sum(row['expected_return_pct'] is not None for row in r['rows'])==4
    assert 'monetary_policy' in next(row for row in r['rows'] if row['symbol']=='AMD')['context_provenance']
    c=b['coefficients'];c.pop('run_id')
    x,missing,refs=price.context_vector({'coefficients':c},'AMD',SESSION,10,NOW,fixture=True)
    assert not any(k in refs for k in ('monetary_policy','financial_conditions'))
    assert x[:6]==[0]*6


def test_compressed_private_input_delivery_preserves_values():
    import base64,gzip
    from unittest.mock import patch
    from .alpha_full_runtime import load_bundle
    b={'coefficients_by_horizon':{'10':{'run_id':'self-authored'}},'seeking':{}}
    encoded=base64.b64encode(gzip.compress(json.dumps(b).encode(),mtime=0)).decode()
    with patch.dict(os.environ,{'ALPHA_FULL_BUNDLE_B64':encoded},clear=True):assert load_bundle()==b


def test_pooled_context_learning_waits_for_real_distinct_sessions():
    rows=[]
    for i in range(30):
        t=datetime(2025,1,1,tzinfo=timezone.utc)+timedelta(days=i)
        rows.append(dict(session=t.date().isoformat(),symbol='AMD',horizon=10,issued_at=t.isoformat(),
            outcome_available_at=(t+timedelta(days=20)).isoformat(),context_vector=[.5]*26,
            technical_return=0,horizon_volatility=.1,actual_return_pct=1,feature_schema_sha256=price.SCHEMA))
    assert price.fit_context(rows[:19],10,NOW) is None
    a=price.fit_context(rows,10,NOW);assert a['distinct_sessions']==30 and not a['qualified']
    rows[0]['outcome_available_at']='2030-01-01T00:00:00Z'
    a=price.fit_context(rows,10,NOW);assert a['excluded_records']==1


def test_weekly_scoring_separates_maturity_failure_and_direction_errors():
    from unittest.mock import MagicMock
    r=dict(horizon=10,status='EXPERIMENTAL_PRICE_FORECAST',expected_return_pct=2.,technical_return=.01,
           band_low_pct=-4.,band_high_pct=5.,target_session='2026-12-31')
    blocked=dict(r,status='STATUS_BLOCKED');unresolved=dict(r,target_session='2026-11-13')
    store=MagicMock();store.connect.return_value.__enter__.return_value.execute.return_value.fetchall.return_value=[
        (r,-1.,datetime(2026,11,16,tzinfo=timezone.utc)),(r,None,None),(blocked,None,None),(unresolved,None,None)]
    m=evaluation(store,NOW)['by_horizon']['10']
    assert (m['matured'],m['blocked'],m['pending'],m['unresolved'])==(1,1,1,1)
    assert m['mae_percentage_points']==3 and m['matched_technical_mae_pp']==2
    assert m['strict_sign_accuracy']==m['directional_accuracy']==0


@pytest.mark.skipif(not os.environ.get('ALPHA_SHADOW_TEST_DSN'),reason='Disposable PG required')
class TestPriceSQL:
    def connect(self):
        import psycopg
        url=os.environ['ALPHA_SHADOW_TEST_DSN'];info=psycopg.conninfo.conninfo_to_dict(url)
        assert info.get('host') in ('127.0.0.1','localhost') and info.get('dbname')=='alpha_shadow_research'
        c=psycopg.connect(url);c.execute('set role alpha_shadow_writer');return c

    def body(self):
        from .runtime import latest_completed
        now=datetime.now(timezone.utc);session=latest_completed(now)
        from research.daily_shadow.core import calendar
        import pandas as pd
        if (now-calendar().session_close(pd.Timestamp(session)).to_pydatetime()).total_seconds()>=36*3600:pytest.skip('Outside genuine issue window')
        snapshot=sample('AMD',count=180);dates=calendar().sessions_in_range('2020-01-01',session).strftime('%Y-%m-%d').tolist()[-180:]
        snapshot.session=session
        for r,d in zip(snapshot.bars['AMD'],dates):r['date']=d
        frame=price.price_frame(snapshot,'AMD')
        body=price.forecast({'AMD':frame},{},session,now.isoformat())
        version='ALPHA_FULL_PRICE_V1-'+uuid.uuid4().hex[:16];body['model_version']=version
        for r in body['rows']:r['model_version']=version
        return body

    def test_atomic50_and_evaluation_pending_no_fake_accuracy(self):
        from research.daily_shadow.core import canonical
        b=self.body()
        with self.connect() as c:
            count=c.execute('select count(*) from alpha_research_v3.forecasts').fetchone()[0]
            rid=c.execute('select alpha_full_price_v1.record(%s,%s)',(uuid.uuid4(),canonical(b))).fetchone()[0]
            assert rid==c.execute('select alpha_full_price_v1.record(%s,%s)',(uuid.uuid4(),canonical(b))).fetchone()[0]
            assert c.execute('select jsonb_array_length(body->\'rows\') from alpha_full_price_v1.runs where id=%s',(rid,)).fetchone()[0]==50
            assert c.execute('select count(*) from alpha_research_v3.forecasts').fetchone()[0]==count
        metrics=evaluation(SimpleNamespace(connect=self.connect),datetime.now(timezone.utc).isoformat())
        assert all(m['matured']==0 for m in metrics['by_horizon'].values())
        assert training_records(SimpleNamespace(connect=self.connect),datetime.now(timezone.utc).isoformat())==[]

    @pytest.mark.parametrize('fault',['fixture','duplicate','target','null','backdate'])
    def test_invalid_price_batch_rejected(self,fault):
        import psycopg
        from research.daily_shadow.core import canonical
        b=self.body()
        if fault=='fixture':b['fixture']=True
        if fault=='duplicate':b['rows'][0]=copy.deepcopy(b['rows'][1])
        if fault=='target':b['rows'][0]['target_session']=b['session']
        if fault=='null':b['rows'][0]['qualified']=None
        if fault=='backdate':b['session']='2025-01-02'
        with pytest.raises(psycopg.Error),self.connect() as c:c.execute('select alpha_full_price_v1.record(%s,%s)',(uuid.uuid4(),canonical(b)))

    def test_future_outcome_cannot_be_used_for_learning(self):
        import psycopg
        from research.daily_shadow.core import canonical
        b=self.body()
        with self.connect() as c:rid=c.execute('select alpha_full_price_v1.record(%s,%s)',(uuid.uuid4(),canonical(b))).fetchone()[0]
        with pytest.raises(psycopg.Error),self.connect() as c:
            c.execute('select alpha_full_price_v1.resolve(%s,%s,%s,%s,%s)',(rid,'AMD',10,1.,datetime.now(timezone.utc).isoformat()))
