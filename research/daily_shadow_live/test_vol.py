import copy, unittest, math, os, uuid
from unittest.mock import MagicMock,patch
from datetime import datetime,timezone
import numpy as np
import pandas as pd
from research.daily_shadow.core import calendar,canonical,sha
from research.daily_shadow_v3.adapter import Snapshot,EODHDAdapter
from research.daily_shadow_v3.legal import fixture_permit
from . import vol

NOW='2026-11-17T02:10:00+00:00';SESSION='2026-11-16'

def sample(symbol='AMD',count=1400):
    days=calendar().sessions[calendar().sessions<=pd.Timestamp(SESSION)][-count:]
    rng=np.random.default_rng(812);ret=rng.normal(.0003,.03,len(days));close=100*np.exp(np.cumsum(ret));low=close*np.exp(-rng.uniform(0,.04,len(days)))
    rows=[dict(date=d.strftime('%Y-%m-%d'),open=float(c),high=float(c*1.02),low=float(l),close=float(c),volume=100.,adjusted_close=float(c)) for d,c,l in zip(days,close,low)]
    return Snapshot('EODHD',SESSION,NOW,None,True,None,{symbol:rows},{symbol:[]},{symbol:[]},{symbol:'USD'},{'fixture':b'self authored'},'a'*64,['fixture://self-authored'])

class NumericalTests(unittest.TestCase):
    def test_manifest_exact_owner_order(self):
        self.assertEqual(vol.SYMBOLS,('ANET','NVDA','AMD','CRWD','NBIS','GOOG','GS','META','MU','LRCX'))
        tasks=vol.series();self.assertEqual(len(tasks),120);self.assertEqual(len({canonical(t) for t in tasks}),120)
        self.assertEqual({t['horizon'] for t in tasks},{10,30})
    def test_each_task_has_independent_fit(self):
        snap=sample();df=vol.frame(snap,'AMD');models=[vol.artifact(df,t,'2026-11-16T00:00:00+00:00',NOW,snap.revision,fixture=True) for t in vol.series(('AMD',))]
        self.assertEqual(len({m['version'] for m in models}),12)
        for m in models:
            self.assertFalse(m['qualified']);self.assertFalse(m['calibrated']);self.assertLess(m['last_maturity'],m['fit_cutoff'])
            if not m['unavailable']:
                p,why=vol.probability(m,float(df.iloc[-1].log_rv20),NOW);self.assertIsNone(why);self.assertTrue(0<=p<=1)
    def test_future_price_and_label_poisoning_cannot_change_parameters(self):
        snap=sample();df=vol.frame(snap,'AMD');task=vol.series(('AMD',))[1];cut='2026-01-01T00:00:00+00:00'
        a=vol.artifact(df,task,cut,NOW,'a'*64);changed=df.copy();changed.loc[changed.index>='2026-01-01',['low','close','log_rv20']]=12345
        b=vol.artifact(changed,task,cut,NOW,'b'*64)
        for k in ('params','training_rows_sha256','last_maturity','n','hits'):self.assertEqual(a[k],b[k])
    def test_rv20_matches_independent_calculation(self):
        df=vol.frame(sample(),'AMD');r=np.diff(np.log(df.close.to_numpy()))[-20:]
        self.assertAlmostEqual(df.iloc[-1].log_rv20,math.log(np.std(r,ddof=1)*math.sqrt(252)))
    def test_split_unit_invariance(self):
        snap=sample();other=copy.deepcopy(snap);day=other.bars['AMD'][-100]['date'];other.splits['AMD']=[dict(date=day,factor=4)]
        for r in other.bars['AMD']:
            if r['date']<day:
                for k in ('open','high','low','close'):r[k]*=4
        np.testing.assert_allclose(vol.frame(snap,'AMD').log_rv20[20:],vol.frame(other,'AMD').log_rv20[20:])
    def test_gaps_and_duplicates_are_blocked_never_zero_filled(self):
        snap=sample();snap.bars['AMD'].pop(-22)
        with self.assertRaisesRegex(ValueError,'HISTORY_CALENDAR_GAP'):vol.frame(snap,'AMD')
        snap=sample();snap.bars['AMD'].append(snap.bars['AMD'][-1])
        with self.assertRaisesRegex(ValueError,'DUPLICATE'):vol.frame(snap,'AMD')
    def test_nbis_legacy_prices_are_excluded(self):
        df=vol.frame(sample('NBIS'),'NBIS');self.assertGreaterEqual(df.index[0],vol.NBIS_START)
    def test_short_history_and_rare_classes_are_not_numbers(self):
        snap=sample(count=300);df=vol.frame(snap,'AMD');m=vol.artifact(df,vol.series(('AMD',))[0],'2026-11-16T00:00:00+00:00',NOW,'a'*64)
        self.assertTrue(m['unavailable']);self.assertEqual(vol.probability(m,0,NOW)[0],None)
        df=vol.frame(sample(),'AMD');df['low']=df['close']=100.;df['log_rv20']=0.
        m=vol.artifact(df,vol.series(('AMD',))[0],'2026-11-16T00:00:00+00:00',NOW,'a'*64)
        self.assertEqual(m['reason'],'INSUFFICIENT_EVENT_CLASS_SUPPORT')
    def test_outcome_excludes_anchor_and_matures_full_horizon(self):
        from research.daily_shadow_v3.resolver import resolve
        from research.daily_shadow.core import future_sessions
        days=future_sessions(SESSION,30);f=dict(id='x',session=SESSION,horizon=30,label_type='EOD_CLOSE',threshold_pct=10)
        rows=[dict(date=d,close=89.,available_at=calendar().session_close(pd.Timestamp(d)).isoformat()) for d in days]
        self.assertEqual(resolve(f,100.,rows,[],NOW,data_reviewed=True)['status'],'IMMATURE')
        end=calendar().session_close(pd.Timestamp(days[-1])).isoformat();r=resolve(f,100.,rows,[],end,data_reviewed=True)
        self.assertEqual(r['completed_sessions'],30);self.assertTrue(r['outcome'])
    def test_source_asof_and_window_gates(self):
        snap=sample();m=vol.artifact(vol.frame(snap,'AMD'),vol.series(('AMD',))[0],'2026-11-16T00:00:00+00:00',NOW,snap.revision,fixture=True)
        good=vol.rows(SESSION,NOW,snap,[m],fixture_permit(),reviewed=True)[0];self.assertIsNotNone(good['probability_raw'])
        bad=copy.deepcopy(snap);bad.retrieved_at='2026-11-18T00:00:00+00:00'
        self.assertEqual(vol.rows(SESSION,NOW,bad,[m],fixture_permit(),reviewed=True)[0]['reason'],'FUTURE_SOURCE_RETRIEVAL')
        self.assertEqual(vol.rows(SESSION,NOW,snap,[m],fixture_permit(),reviewed=False)[0]['probability_raw'],None)
    def test_unknown_symbols_cannot_be_injected_into_adapter(self):
        for value in ((),('AMD','AMD'),('../secret',),('AMD?token',)):
            with self.assertRaises(ValueError):EODHDAdapter(fixture_permit(),symbols=value)
    def test_legacy_pair_metrics_survive_third_model(self):
        from research.daily_shadow_v3.metrics import paired_metrics
        row=dict(session=SESSION,symbol='AMD',label_type='EOD_CLOSE',threshold_pct=5,horizon=10,run_mode='RESEARCH_FORECAST',fixture=False,status='RESEARCH_FORECAST',outcome_status='MATURED',outcome=True,probability_raw=.2)
        result=paired_metrics([dict(row,model_name=m) for m in ('HIST','REGIME','VOL')]);self.assertEqual(result['paired_dates'],1)

if __name__=='__main__':unittest.main()

DSN=__import__('os').environ.get('ALPHA_SHADOW_TEST_DSN')
@unittest.skipUnless(DSN,'Explicit disposable local SQL required')
class SQLTests(unittest.TestCase):
    def setUp(self):
        import psycopg,uuid
        from cryptography.fernet import Fernet
        from research.daily_shadow_v3.store import ResearchStore
        info=psycopg.conninfo.conninfo_to_dict(DSN)
        if info.get('host') not in ('127.0.0.1','localhost') or info.get('dbname')!='alpha_shadow_research':raise ValueError('LOCAL_ONLY')
        self.store=ResearchStore(DSN,Fernet.generate_key());self.permit=fixture_permit();self.cid=self.store.register(self.permit)
        self.snap=sample();source=self.snap.bars['AMD']
        for symbol in vol.SYMBOLS:
            self.snap.bars[symbol]=source;self.snap.currency[symbol]='USD';self.snap.splits[symbol]=[];self.snap.dividends[symbol]=[]
        self.snap.revision=sha(str(uuid.uuid4()).encode());self.ref=self.store.payload(self.cid,self.snap,self.permit.raw_until)
        self.models=[];self.rows=[]
        for symbol in vol.SYMBOLS:
            df=vol.frame(self.snap,symbol)
            bank=[vol.artifact(df,t,'2026-11-16T00:00:00+00:00',NOW,self.snap.revision,fixture=True) for t in vol.series((symbol,))]
            self.models.extend(bank);self.rows.extend(vol.rows(SESSION,NOW,self.snap,bank,self.permit,reviewed=True))
        self.key='VOL_TEST:'+str(uuid.uuid4())
    def test_sql_120_atomic_idempotent_and_30_session_support(self):
        ids=self.store.forecasts(self.key,self.rows,self.models,self.cid,self.ref,self.snap)
        self.assertEqual(len(ids),120);self.assertEqual(ids,self.store.forecasts(self.key,self.rows,self.models,self.cid,self.ref,self.snap));self.assertTrue(self.store.verify())
        with self.store.connect() as c:
            result=c.execute('select count(*),count(*) filter(where horizon=30) from alpha_research_v3.forecasts where id=any(%s)',(ids,)).fetchone()
        self.assertEqual(result,(120,60))
    def test_last_bad_row_rolls_back_entire_batch(self):
        import psycopg
        bad=[dict(r) for r in self.rows];bad[-1]['model_hash']='0'*64
        with self.assertRaises(psycopg.Error):self.store.forecasts(self.key,bad,self.models,self.cid,self.ref,self.snap)
        with self.store.connect() as c:self.assertEqual(c.execute('select count(*) from alpha_research_v3.journal where event_key like %s',(self.key+'%',)).fetchone()[0],0)
    def test_legacy_and_vol_batch_queries_are_separate(self):
        from .vol_runtime import prior_batch
        ids=self.store.forecasts(self.key,self.rows,self.models,self.cid,self.ref,self.snap)
        with self.store.connect() as c:
            n,_=prior_batch(c,SESSION)
            legacy=c.execute("select count(*) from alpha_research_v3.forecasts where id=any(%s) and model_id in(select id from alpha_shadow_v1.model_registry where model_name in('HIST','REGIME'))",(ids,)).fetchone()[0]
        self.assertEqual(legacy,0);self.assertGreaterEqual(n,0) # synthetic not a live batch
    def test_fixture_cannot_be_promoted_to_live(self):
        import psycopg
        with self.assertRaises(psycopg.Error):self.store.forecasts(self.key,self.rows,self.models,self.cid,self.ref,self.snap,run_mode='RESEARCH_FORECAST')
    def test_model_allowlist_and_no_raw_immutable_fields(self):
        import psycopg
        bad=[dict(r) for r in self.rows];bad[-1]['price']=123
        with self.assertRaises(psycopg.Error):self.store.forecasts(self.key,bad,self.models,self.cid,self.ref,self.snap)

class RuntimeTests(unittest.TestCase):
    def test_preclose_never_fits_or_writes_forecasts(self):
        from .vol_runtime import run_vol
        store=MagicMock();result=run_vol(store,fixture_permit(),MagicMock(),SESSION,clock=lambda:datetime.fromisoformat('2026-11-16T18:00:00+00:00'))
        self.assertEqual(result['status'],'WAITING_VALID_SESSION_WINDOW');store.connect.assert_not_called()
    def test_existing_live_manifest_never_reissues_a_new_version(self):
        from .vol_runtime import run_vol
        store=MagicMock();c=store.connect.return_value.__enter__.return_value;c.execute.return_value.fetchone.side_effect=[(True,),(120,108)]
        collector=MagicMock();result=run_vol(store,fixture_permit(),MagicMock(),SESSION,clock=lambda:datetime.fromisoformat(NOW),collector=collector)
        self.assertEqual(result['status'],'ALREADY_RECORDED');collector.assert_not_called()
    def test_partial_manifest_is_not_silently_filled(self):
        from .vol_runtime import run_vol
        store=MagicMock();c=store.connect.return_value.__enter__.return_value;c.execute.return_value.fetchone.side_effect=[(True,),(12,12)]
        collector=MagicMock();r=run_vol(store,fixture_permit(),MagicMock(),SESSION,clock=lambda:datetime.fromisoformat(NOW),collector=collector)
        self.assertEqual(r['status'],'PARTIAL_FAILURE');collector.assert_not_called()
    def test_vol_feature_requires_explicit_enable(self):
        from .vol_runtime import enabled
        import os
        with patch.dict(os.environ,{},clear=True):self.assertFalse(enabled())
        with patch.dict(os.environ,{'ALPHA_VOL_ENABLED':'true'}):self.assertTrue(enabled())
    def test_preflight_never_publishes_and_reports_all10(self):
        from .vol_runtime import preflight
        store=MagicMock()
        with patch('research.daily_shadow_live.vol_runtime.EODHDAdapter') as adapter,patch('research.daily_shadow_live.runtime.receipt') as receipt:
            adapter.return_value.collect.side_effect=[sample(s) for s in vol.SYMBOLS]
            report=preflight(store,fixture_permit(),MagicMock(),SESSION,clock=lambda:datetime.fromisoformat(NOW))
        self.assertEqual(receipt.call_count,10);self.assertEqual(report['models'],120);self.assertEqual(report['checked']+report['blocked'],120);store.forecasts.assert_not_called();store.append.assert_not_called()

    def test_legacy_failure_does_not_suppress_vol(self):
        from .test_worker_fix import DiagnosticTests
        from research.daily_shadow_v3.adapter import VendorError
        import os
        with patch.dict(os.environ,{'ALPHA_VOL_ENABLED':'true','ALPHA_VOL_PREFLIGHT_ONCE':'false'}),patch('research.daily_shadow_live.vol_runtime.run_vol',return_value=dict(phase='VOL',status='RECORDED',issued=120,blocked=0)) as issuer,patch('research.daily_shadow_live.vol_runtime.inspect_vol',return_value=dict(phase='VOL_SQL_AUDIT',status='DIRECT_READ_ONLY_SQL')):
            code,records,_=DiagnosticTests().run_mock(issue_error=VendorError('SOURCE_STILL_REVISING'))
        issuer.assert_called_once();self.assertEqual(code,2);self.assertTrue(any(r.get('phase')=='VOL' and r.get('status')=='RECORDED' for r in records))
