import unittest,copy,concurrent.futures
from datetime import datetime,timedelta,timezone
from .core import *
from .runner import *
from .demo import MemoryStore
class Tests(unittest.TestCase):
 def setUp(self):
  self.session='2026-11-06';self.now='2026-11-06T23:30:00+00:00';self.v=archive(b'x',self.session,'2026-11-06T22:00:00+00:00','2026-11-06T22:01:00+00:00',basis='SPLIT_NORMALIZED_PRICE',actions_qualified=False);self.m=blocked_models()[0]
 def test_weekend(self):self.assertEqual(session_gate('2026-11-07','2026-11-07T23:30:00+00:00'),'WEEKEND')
 def test_holiday(self):self.assertEqual(session_gate('2026-12-25','2026-12-25T23:30:00+00:00'),'HOLIDAY')
 def test_early_close(self):self.assertEqual(session_gate('2026-11-27','2026-11-27T18:01:00+00:00'),'READY')
 def test_dst_winter(self):self.assertEqual(session_gate('2026-11-06','2026-11-06T20:30:00+00:00'),'BEFORE_CLOSE')
 def test_dst_summer(self):self.assertEqual(session_gate('2026-07-06','2026-07-06T20:30:00+00:00'),'READY')
 def test_backfill(self):self.assertEqual(session_gate('2026-11-05',self.now),'BACKFILL_NOT_PROSPECTIVE')
 def test_source_stale(self):self.v['session']='2026-11-05';self.assertEqual(quality(self.v,self.session,self.now),'STALE_SESSION')
 def test_source_late(self):self.v['ingestion_at']='2026-11-07T00:00:00+00:00';self.assertEqual(quality(self.v,self.session,self.now),'LATE_OR_FUTURE_SOURCE')
 def test_pit_fail(self):self.assertEqual(quality(self.v,self.session,self.now),'PIT_UNQUALIFIED')
 def test_frozen_archive_not_live(self):self.v['historical_archive']=True;self.assertEqual(quality(self.v,self.session,self.now),'HISTORICAL_REPLAY_NOT_LIVE')
 def test_missing_timestamp(self):self.v['publication_at']=None;self.assertEqual(quality(self.v,self.session,self.now),'MISSING_SOURCE_TIMESTAMPS')
 def test_actions_fail(self):self.v['qualification']='QUALIFIED_PIT';self.assertEqual(quality(self.v,self.session,self.now),'CORPORATE_ACTIONS_UNQUALIFIED')
 def test_no_future_decision(self):
  with self.assertRaises(ValueError):forecast(self.session,'SPY','EOD_CLOSE',5,10,self.m,self.v,self.now,'2027-01-01T00:00:00+00:00')
 def test_actual_no_fabricated_probability(self):self.assertIsNone(forecast(self.session,'SPY','EOD_CLOSE',5,10,self.m,self.v,self.now,self.now)['probability_raw'])
 def test_unqualified_bank(self):self.assertEqual(raw_estimate(self.m,'EOD_CLOSE:5:10',self.session,self.now,'UP')[1],'UNSUPPORTED_TASK')
 def test_mature_train_gate(self):
  m=dict(self.m,qualified=True,supported_tasks=['x'],training=[dict(task='x',symbol=None,y=1,maturity='2027-01-01T00:00:00+00:00')]);self.assertEqual(raw_estimate(m,'x',self.session,self.now,'UP')[1],'IMMATURE_TRAINING_LABEL')
 def test_real_formula_fixture(self):
  m=dict(self.m,qualified=True,supported_tasks=['x'],training=[dict(task='x',symbol=None,y=0,maturity='2025-01-01T00:00:00+00:00'),dict(task='x',symbol=None,y=1,maturity='2025-01-01T00:00:00+00:00')]);self.assertEqual(raw_estimate(m,'x',self.session,self.now,'UP')[0],.5)
 def test_222_series(self):self.assertEqual(len(requested_series()),222)
 def test_recipe_bounds(self):
  rr=recipes([100,200,50],np.random.default_rng(1).normal(0,.02,(252,3)));self.assertAlmostEqual(sum(rr['C']['weights']),1);self.assertTrue(all(.1<=x<=.5 for x in rr['C']['weights']));self.assertEqual(rr['B']['cash'],40000)
 def test_recipe_missing(self):
  with self.assertRaises(ValueError):recipes([100,200,50],np.zeros((199,3)))
 def sample(self,h=10):
  f=dict(id='fixture',session=self.session,horizon=h,threshold_pct=10,label_type='LOW_INTRADAY',basis='SPLIT_NORMALIZED_PRICE');dates=future_sessions(self.session,h);rows=[dict(session=d,low=90,close=101,publication_at=d+'T23:00:00+00:00',source_hash='fixture') for d in dates];return f,rows
 def test_exact_boundary(self):
  f,r=self.sample();o=resolve(f,100,r,'2027-12-31T00:00:00+00:00',f['basis'],True);self.assertTrue(o['outcome']);self.assertEqual(o['time_to_hit'],1)
 def test_low_close_separate(self):
  f,r=self.sample();f['label_type']='EOD_CLOSE';self.assertFalse(resolve(f,100,r,'2027-12-31T00:00:00+00:00',f['basis'],True)['outcome'])
 def test_all_horizons(self):
  for h in (10,20,60):
   f,r=self.sample(h);self.assertEqual(resolve(f,100,r,'2027-12-31T00:00:00+00:00',f['basis'],True)['completed_sessions'],h)
 def test_early_hit_immature(self):
  f,r=self.sample();self.assertEqual(resolve(f,100,r[:1],self.now,f['basis'],True)['status'],'IMMATURE')
 def test_mature_gap(self):
  f,r=self.sample();self.assertEqual(resolve(f,100,r[:-1],'2027-12-31T00:00:00+00:00',f['basis'],True)['status'],'UNRESOLVED')
 def test_wrong_adjustment(self):
  f,r=self.sample();self.assertEqual(resolve(f,100,r,'2027-12-31T00:00:00+00:00','RAW',True)['status'],'UNRESOLVED')
 def test_no_actions(self):
  f,r=self.sample();self.assertEqual(resolve(f,100,r,'2027-12-31T00:00:00+00:00',f['basis'],False)['status'],'UNRESOLVED')
 def test_idempotent_memory(self):
  st=MemoryStore();p=FixtureProvider(self.v);a=run_once(self.session,p,blocked_models(),st,self.now,self.now);b=run_once(self.session,p,blocked_models(),st,self.now,self.now);self.assertEqual(a['ids'],b['ids']);self.assertEqual(len(st.events),222)
 def test_bounded_retry(self):
  class Missing:
   n=0
   def collect(self,session):self.n+=1;raise TimeoutError()
  p=Missing();run_once(self.session,p,blocked_models(),MemoryStore(),self.now,self.now);self.assertEqual(p.n,3)
 def test_no_holiday_forecasts(self):
  st=MemoryStore();r=run_once('2026-12-25',FixtureProvider(self.v),blocked_models(),st,'2026-12-25T23:30:00+00:00','2026-12-25T23:30:00+00:00');self.assertEqual(r['records'],0);self.assertEqual(len(st.events),1)
 def test_no_network(self):
  from unittest.mock import patch
  with patch('socket.socket',side_effect=AssertionError('NETWORK_FORBIDDEN')):
   self.assertEqual(run_once(self.session,FixtureProvider(self.v),blocked_models(),MemoryStore(),self.now,self.now)['records'],222)
 def test_live_guard(self):
  with self.assertRaises(PermissionError):run_once(self.session,FixtureProvider(self.v),blocked_models(),MemoryStore(),self.now,self.now,mode='PROSPECTIVE')
 def test_training_never_pools_other_tasks_or_symbols(self):
  m=dict(self.m,qualified=True,supported_tasks=['x'],training=[dict(task='other',symbol='NVDA',y=1,maturity='2025-01-01T00:00:00+00:00')])
  self.assertIsNone(raw_estimate(m,'x',self.session,self.now,'UP','SPY')[0])
 def test_future_feature_gate(self):
  self.v['feature_available_at']=['2027-01-01T00:00:00+00:00'];self.assertEqual(quality(self.v,self.session,self.now),'FUTURE_FEATURE')
if __name__=='__main__':unittest.main()
