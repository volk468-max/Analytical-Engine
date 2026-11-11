"""Offline tests. Artificial fixtures never qualify a real provider or historical series."""
import copy,os,math,unittest
from dataclasses import replace
from unittest.mock import patch
from datetime import timedelta
from .legal import Permit,fixture_permit
from .adapter import *
from .fixtures import FixtureTransport,clock,fixture_models,SESSION,ISSUED
from .engine import candidates,probability
from .resolver import resolve
from .metrics import paired_metrics
from .actions import REFERENCES,check_event,check_price
from .store import restore_allowed
from .runner import run
from research.daily_shadow.core import future_sessions,requested_series,utc

class LegalTests(unittest.TestCase):
 def setUp(self):self.p=fixture_permit()
 def test_unqualified_before_secret_and_network(self):
  t=FixtureTransport()
  with patch.dict(os.environ,{},clear=True):s=EODHDAdapter(Permit('EODHD'),t,clock).collect(SESSION)
  self.assertEqual(s.legal_reason,'LICENSE_UNQUALIFIED');self.assertEqual(t.calls,0);self.assertIsNone(s.revision)
 def test_trial_no_durable_storage(self):self.assertEqual(replace(self.p,paid=False).reason(ISSUED,fixture=True),'TRIAL_DURABLE_STORAGE_FORBIDDEN')
 def test_exact_budget_includes_tax(self):
  for price,valid in [('50',True),('50.01',False),('NaN',False),('-1',False),('Infinity',False)]:self.assertEqual(replace(self.p,total_monthly_usd=price).reason(ISSUED,fixture=True) is None,valid)
 def test_malformed_price_fails_closed(self):self.assertEqual(replace(self.p,total_monthly_usd='invalid').reason(ISSUED,fixture=True),'INVALID_TOTAL_PRICE')
 def test_unconfirmed_total_and_class(self):
  self.assertEqual(replace(self.p,total_monthly_usd=None).reason(ISSUED,fixture=True),'TOTAL_PRICE_TAXES_UNCONFIRMED')
  self.assertIsNotNone(replace(self.p,operator_class='UNKNOWN').reason(ISSUED,fixture=True))
 def test_missing_retention_capabilities(self):
  for name in ('raw_storage','hash_metadata_retention','nonreconstructible_forecasts_retention','cloud','backups'):
   self.assertEqual(replace(self.p,**{name:False}).reason(ISSUED,fixture=True),'RETENTION_CAPABILITIES_NOT_APPROVED')
 def test_expiry_and_offboard(self):
  self.assertEqual(replace(self.p,access_until=ISSUED).reason(ISSUED,fixture=True),'SUBSCRIPTION_EXPIRED')
  self.assertEqual(replace(self.p,raw_until=ISSUED).reason(ISSUED,fixture=True),'RAW_TTL_EXPIRED')
  self.assertEqual(replace(self.p,revoked=True).reason(ISSUED,fixture=True),'VENDOR_OFFBOARDED')
 def test_full_horizon_retention(self):self.assertEqual(self.p.reason(ISSUED,fixture=True,horizon_end=self.p.raw_until),'RETENTION_SHORTER_THAN_LABEL_HORIZON')
 def test_fixture_not_live_permission(self):self.assertEqual(self.p.reason(ISSUED,fixture=False),'FIXTURE_LIVE_SCOPE_MISMATCH')
 def test_restored_backup_not_license_authority(self):
  self.assertFalse(restore_allowed(['x'],['x']));self.assertFalse(restore_allowed(['x'],[],authority_fresh=True));self.assertTrue(restore_allowed(['x'],['x'],authority_fresh=True))

class AdapterTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  with patch.dict(os.environ,{'EODHD_API_TOKEN':'fixture-secret'}):cls.s=EODHDAdapter(fixture_permit(),FixtureTransport(),clock).collect(SESSION)
 def adapter(self,t=None,p=None):return EODHDAdapter(p or fixture_permit(),t or FixtureTransport(),clock)
 def test_missing_credentials_no_requests(self):
  t=FixtureTransport()
  with patch.dict(os.environ,{},clear=True):s=self.adapter(t).collect(SESSION)
  self.assertEqual(s.legal_reason,'MISSING_CREDENTIALS');self.assertEqual(t.calls,0)
 def test_mapping_currency_basis_publication(self):
  self.assertEqual(set(self.s.bars),set(SYMBOLS));self.assertTrue(all(v=='USD' for v in self.s.currency.values()));self.assertIsNone(self.s.publication_at);self.assertEqual(self.s.retrieved_at,ISSUED)
  self.assertIn('RAW_AS_TRADED',self.s.basis);self.assertTrue(all('api_token' not in u for u in self.s.source_uris));self.assertNotIn('100.0',repr(self.s))
 def test_invalid_inputs_fail_closed(self):
  for variant in ('late','mixed','duplicate','nan','wrongohlc','missing','currency','transport'):
   with self.subTest(variant=variant),patch.dict(os.environ,{'EODHD_API_TOKEN':'fixture-secret'}):
    t=FixtureTransport();t.variant=variant
    with self.assertRaises(VendorError):self.adapter(t).collect(SESSION)
 def test_wrong_provider(self):
  t=FixtureTransport();s=self.adapter(t,fixture_permit('Tiingo')).collect(SESSION);self.assertEqual(s.legal_reason,'PROVIDER_CONTRACT_MISMATCH');self.assertEqual(t.calls,0)
 def test_no_network_without_separate_gate(self):
  class Real:
   fixture=False
   def get(*args):raise AssertionError('must not run')
  with patch.dict(os.environ,{'EODHD_API_TOKEN':'fixture-secret'}),self.assertRaisesRegex(VendorError,'OUTBOUND'):self.adapter(Real(),replace(fixture_permit(),scope='LIVE')).collect(SESSION)
 def test_revision_frozen_first_as_seen(self):
  t=FixtureTransport()
  with patch.dict(os.environ,{'EODHD_API_TOKEN':'fixture-secret'}):
   first=self.adapter(t).collect(SESSION);t.revision=1;second=self.adapter(t).collect(SESSION)
  self.assertNotEqual(first.revision,second.revision);self.assertEqual(first.bars['AMD'][-1]['close'],100)
 def test_secret_sanitized_transport_exception(self):
  class Bad(FixtureTransport):
   def get(self,path,params,secret):raise RuntimeError(secret)
  with patch.dict(os.environ,{'EODHD_API_TOKEN':'fixture-secret'}):
   with self.assertRaises(VendorError) as exc:self.adapter(Bad()).collect(SESSION)
  self.assertNotIn('fixture-secret',str(exc.exception))
 def test_split_basis_excludes_total_return_and_future_actions(self):
  row=self.s.bars['NVDA'][-1];events=[dict(date='2025-01-03',factor=10)]
  self.assertEqual(normalized_prefix([row],events,SESSION)[0]['close'],100)
  self.assertEqual(normalized_prefix([row],events,'2025-01-03')[0]['close'],10)
  self.assertNotEqual(normalized_prefix([row],[],SESSION)[0]['close'],row['adjusted_close'])
 def test_exact_forward_and_reverse_splits(self):
  for encoded,wanted in [('10.000000/1.000000',10),('4/1',4),('1/5',.2)]:self.assertEqual(ratio(encoded),wanted)
  for encoded in ('1/0','NaN/1','1/-1','1','2/1/1'):
   with self.assertRaises(VendorError):ratio(encoded)
 def test_dividend_units_and_actions_schema(self):
  class Actions(FixtureTransport):
   def get(self,path,params,secret):
    if '/div/' in path:return b'[{"date":"2024-10-07","currency":"USD","value":0.0115,"unadjustedValue":0.115,"paymentDate":"2024-10-23"}]'
    return super().get(path,params,secret)
  with patch.dict(os.environ,{'EODHD_API_TOKEN':'fixture-secret'}):s=self.adapter(Actions()).collect(SESSION)
  self.assertEqual(s.dividends['MU'][0]['unadjusted_value'],.115);self.assertEqual(s.dividends['MU'][0]['value_current_share_units'],.0115)
 def test_dates_holidays_dst_early_close(self):
  p=fixture_permit()
  for day,stamp in [('2025-01-02',ISSUED),('2025-07-03','2025-07-04T00:31:00Z'),('2025-03-10','2025-03-11T00:30:00Z'),('2025-11-03','2025-11-04T01:30:00Z')]:self.assertIsNone(issuance_gate(day,stamp,p))
  self.assertEqual(issuance_gate('2025-01-01',ISSUED,p),'WEEKEND_OR_HOLIDAY')
  self.assertEqual(issuance_gate(SESSION,'2025-01-03T01:29:00Z',p),'BEFORE_CONSERVATIVE_FINALIZATION_WINDOW')
  self.assertEqual(issuance_gate(SESSION,'2025-01-04T01:31:00Z',p),'STALE_OR_BACKDATED_SESSION')
  self.assertEqual(issuance_gate(SESSION,ISSUED,replace(p,finalization_verified=False)),'PROVIDER_FINALIZATION_NOT_VERIFIED')
 def test_preregistered_primary_reference_tolerances(self):
  for r in REFERENCES:
   obs={k:r[k] for k in ('symbol','date','kind','value')};self.assertTrue(check_event(obs,r));obs['date']='2025-01-02';self.assertFalse(check_event(obs,r))
  r=REFERENCES[-1];self.assertTrue(check_event(dict(symbol='QQQ',date=r['date'],kind='dividend',value=.573),r));self.assertFalse(check_event(dict(symbol='QQQ',date=r['date'],kind='dividend',value=.572),r))
 def test_price_tolerance_does_not_mix_basis(self):
  p=dict(date=SESSION,basis='RAW',currency='USD',open=100,high=101,low=99,close=100);q=dict(p,close=100.005);self.assertTrue(check_price(p,q));q['basis']='TOTAL_RETURN';self.assertFalse(check_price(p,q))

class EngineTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  with patch.dict(os.environ,{'EODHD_API_TOKEN':'fixture-secret'}):cls.s=EODHDAdapter(fixture_permit(),FixtureTransport(),clock).collect(SESSION)
 def rows(self,s=None,models=None,p=None,reviewed=True):return candidates(SESSION,ISSUED,ISSUED,s or self.s,models or fixture_models(),p or fixture_permit(),data_reviewed=reviewed)
 def test_coverage_two_models_per_definition(self):
  models=fixture_models();before=copy.deepcopy(models);r=self.rows(models=models)
  self.assertEqual(len(r),222);self.assertEqual(sum(x['probability_raw'] is not None for x in r),216);self.assertEqual(sum(x['symbol'] in 'ABC' for x in r),6);self.assertEqual(models,before)
  self.assertTrue(all(x['probability_calibrated'] is None for x in r));self.assertTrue(all(x['training_status']=='TRAINING_REPLAY_NOT_PIT' for x in r))
 def test_legal_and_review_null(self):
  self.assertTrue(all(x['probability_raw'] is None for x in self.rows(p=Permit('EODHD'))));self.assertTrue(all(x['probability_raw'] is None for x in self.rows(reviewed=False)))
 def test_wrong_source_basis_blocked(self):
  s=copy.deepcopy(self.s);s.basis='TOTAL_RETURN_OHLC';self.assertTrue(all(x['probability_raw'] is None for x in self.rows(s=s)))
 def test_asof_source_after_decision(self):
  s=copy.deepcopy(self.s);s.retrieved_at='2025-01-03T01:32:00Z';self.assertTrue(all(x['probability_raw'] is None for x in self.rows(s=s)))
 def test_fake_publication_after_collection(self):
  s=copy.deepcopy(self.s);s.publication_at='2025-01-03T01:32:00Z';self.assertTrue(all(x['probability_raw'] is None for x in self.rows(s=s)))
 def test_future_model_and_unmatured_training(self):
  for field,value in [('created_at','2030-01-01T00:00:00Z'),('fit_cutoff','2030-01-01T00:00:00Z')]:
   models=fixture_models();models[0][field]=value;r=self.rows(models=models);self.assertIsNone(r[0]['probability_raw']);self.assertIsNone(r[1]['probability_raw'])
  models=fixture_models();models[0]['count_bank']['last_maturity']=models[0]['fit_cutoff'];self.assertIsNone(self.rows(models=models)[0]['probability_raw'])
 def test_count_formulas_and_no_qualified_mutation(self):
  s=requested_series()[0];m=fixture_models()[0];p,e=probability(m,s,ISSUED,'UP');self.assertAlmostEqual(p,26/102);self.assertIsNone(e);self.assertFalse(m['qualified'])
 def test_ambiguous_models(self):
  models=fixture_models();models.append(models[0]);
  with self.assertRaises(ValueError):self.rows(models=models)
 def test_live_runner_refuses_fixture_and_unapproved(self):
  for approved in (False,True):
   with self.assertRaises(PermissionError):run(EODHDAdapter(fixture_permit(),FixtureTransport(),clock),fixture_models(),None,SESSION,ISSUED,ISSUED,mode='RESEARCH_FORECAST',live_approved=approved)

class OutcomeTests(unittest.TestCase):
 def data(self,h=10):
  f=dict(id='fixture',session=SESSION,horizon=h,threshold_pct=10,label_type='EOD_CLOSE');days=future_sessions(SESSION,h)
  rows=[dict(date=d,close=99,low=85,available_at=calendar().session_close(pd.Timestamp(d)).isoformat()) for d in days]
  now=(calendar().session_close(pd.Timestamp(days[-1]))+pd.Timedelta(hours=4)).isoformat();return f,rows,now
 def test_full_horizon_even_early_touch(self):
  for h in (10,20,60):
   f,rows,now=self.data(h);rows[0]['close']=80;r=resolve(f,100,rows,[],now,data_reviewed=True);self.assertEqual(r['status'],'MATURED');self.assertTrue(r['outcome']);self.assertEqual(r['completed_sessions'],h)
   self.assertEqual(resolve(f,100,rows,[],rows[0]['available_at'],data_reviewed=True)['status'],'IMMATURE')
 def test_missing_duplicate_future_rows(self):
  f,rows,now=self.data()
  for r in (rows[:-1],rows+[rows[0]]):self.assertEqual(resolve(f,100,r,[],now,data_reviewed=True)['status'],'UNRESOLVED')
 def test_touch_low_distinct_from_eod_close(self):
  f,rows,now=self.data();self.assertFalse(resolve(f,100,rows,[],now,data_reviewed=True)['outcome']);f['label_type']='LOW_INTRADAY';self.assertTrue(resolve(f,100,rows,[],now,data_reviewed=True)['outcome'])
 def test_split_does_not_create_false_crash(self):
  f,rows,now=self.data();rows=[dict(r,close=9.9) for r in rows];self.assertFalse(resolve(f,100,rows,[dict(date=rows[0]['date'],factor=10)],now,data_reviewed=True)['outcome'])
 def test_bad_anchors_nan_missing_legal_actions(self):
  f,rows,now=self.data()
  for anchor in (0,float('nan'),None):self.assertEqual(resolve(f,anchor,rows,[],now,data_reviewed=True)['status'],'UNRESOLVED')
  rows[0]['close']=float('nan');self.assertEqual(resolve(f,100,rows,[],now,data_reviewed=True)['reason'],'INVALID_FUTURE_MARK')
 def test_future_row_cannot_claim_availability_before_close(self):
  f,rows,now=self.data();rows[-1]['available_at']=ISSUED;self.assertEqual(resolve(f,100,rows,[],now,data_reviewed=True)['reason'],'FUTURE_BAR_AVAILABLE_BEFORE_ITS_CLOSE')
 def test_late_source_not_matured(self):
  f,rows,now=self.data();rows[-1]['available_at']='2030-01-01T00:00:00Z';self.assertEqual(resolve(f,100,rows,[],now,data_reviewed=True)['status'],'IMMATURE')

class MetricTests(unittest.TestCase):
 def test_pairs_only_and_no_iid_confidence(self):
  r=dict(session=SESSION,symbol='AMD',label_type='EOD_CLOSE',threshold_pct=10,horizon=10,run_mode='RESEARCH_FORECAST',status='RESEARCH_FORECAST',outcome_status='MATURED',outcome=True,probability_raw=.25)
  rows=[dict(r,model_name=n) for n in ('HIST','REGIME')];out=paired_metrics(rows);self.assertEqual(out['paired_dates'],1);self.assertAlmostEqual(out['metrics']['HIST']['brier'],.5625);self.assertIsNone(out['independent_events']);self.assertIsNone(out['confidence_interval'])
  self.assertEqual(paired_metrics([dict(x,fixture=True) for x in rows])['paired_dates'],0)
  self.assertEqual(paired_metrics(rows[:1])['paired_dates'],0)
 def test_duplicate_versions_and_mismatched_event_denied(self):
  r=dict(session=SESSION,symbol='AMD',label_type='EOD_CLOSE',threshold_pct=10,horizon=10,run_mode='RESEARCH_FORECAST',status='RESEARCH_FORECAST',outcome_status='MATURED',outcome=True,probability_raw=.25,model_name='HIST')
  with self.assertRaises(ValueError):paired_metrics([r,r])
  with self.assertRaises(ValueError):paired_metrics([r,dict(r,model_name='REGIME',outcome=False)])
if __name__=='__main__':unittest.main()
