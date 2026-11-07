import copy,unittest
from engine import *
from demo import snapshot,demo
class Tests(unittest.TestCase):
 def test_missing_snapshot(self):
  with self.assertRaises(ValueError):validate_snapshot({})
 def test_future_source(self):
  s=snapshot();s['ingested_at']='2031-01-01T00:00:00+00:00'
  with self.assertRaises(ValueError):validate_snapshot(s)
 def test_adjusted_rejected(self):
  s=snapshot();s['price_basis']='ADJUSTED'
  with self.assertRaises(ValueError):validate_snapshot(s)
 def test_missing_fx(self):
  s=snapshot();s['fx']={}
  with self.assertRaises(ValueError):validate_snapshot(s)
 def test_actual_forecast_blocked(self):self.assertIsNone(update_logit(.51,{}, {},'x')['probability'])
 def test_daily_is_not_intraday(self):
  r=touch_label(100,[dict(session=i,nav=100) for i in range(60)],list(range(60)),True);self.assertIsNone(r['primary']);self.assertFalse(r['daily_proxy'])
 def test_exact_touch_boundary(self):
  r=touch_label(100,[dict(session=i,nav=90 if i==59 else 100) for i in range(60)],list(range(60)),True,True);self.assertTrue(r['primary'])
 def test_early_hit_not_mature(self):self.assertIsNone(touch_label(100,[dict(session=0,nav=1)],list(range(60)),False)['primary'])
 def test_missing_session(self):self.assertIsNone(touch_label(100,[dict(session=0,nav=1)],list(range(60)),True)['primary'])
 def test_budget_not_target(self):
  r=drawdown_budget(90,100);self.assertAlmostEqual(r['drawdown'],-.1);self.assertEqual(r['residual'],5);self.assertIsNone(drawdown_budget(None,None)['drawdown'])
 def test_snapshot_frozen(self):
  s=snapshot();before=digest(s);demo();self.assertEqual(before,digest(s))
 def test_joint_paths_not_mean_asset_probabilities(self):self.assertEqual(empirical_synthetic([[.8]*60,[1.2]*60])['probability'],.5)
 def test_es_fractional_tail(self):self.assertAlmostEqual(empirical_synthetic([[.8]*60,[1.1]*60])['expected_shortfall_5pct'],.2)
 def test_no_real_model_from_fixtures(self):self.assertFalse(empirical_synthetic([[1]*60])['calibrated'])
 def test_missing_pit_not_zero(self):
  r=update_logit(.5,{'news':{}},{'news':10},'2030-01-01T00:00:00+00:00',synthetic=True);self.assertIsNone(r['probability'])
 def test_dedup_news(self):
  rows=[dict(event_id='a',text_fingerprint='x'),dict(event_id='a',text_fingerprint='y'),dict(event_id='b',text_fingerprint='x')];self.assertEqual(len(deduplicate(rows)),1)
 def test_opinion_does_not_supply_numeric_value(self):self.assertFalse(qualify_factor(dict(value=None),'2030-01-01T00:00:00+00:00'))
 def test_logodds_not_percentage(self):
  f=dict(value=1,release_at='2030-01-01T00:00:00+00:00',ingested_at='2030-01-01T00:00:00+00:00',source_hash='s',pit_qualified=True,group='news',event_id='a',kind='official',stale=False);r=update_logit(.5,{'a':f},{'a':1},'2030-01-01T00:00:00+00:00',synthetic=True);self.assertAlmostEqual(r['probability'],1/(1+math.exp(-1)))
 def test_correlated_evidence_gate(self):
  f=dict(value=1,release_at='2030-01-01T00:00:00+00:00',ingested_at='2030-01-01T00:00:00+00:00',source_hash='s',pit_qualified=True,group='news',event_id='a',kind='official',stale=False)
  with self.assertRaises(ValueError):update_logit(.5,{'a':f,'b':dict(f,event_id='b')},{'a':1,'b':1},'2030-01-01T00:00:00+00:00',synthetic=True)
 def test_60purge(self):self.assertFalse(eligible_train(40,'2020','2021',100));self.assertTrue(eligible_train(39,'2020','2021',100))
 def test_future_label_excluded(self):self.assertFalse(eligible_train(1,'2022','2021',100))
 def test_policy_no_repeated_trim(self):
  p=Policy(.1,.2,1,0,.25);r=p.step(.55,0,synthetic=True);p.settle(1,.1);self.assertIsNone(p.step(.55,2,synthetic=True)['intent']);self.assertIsNotNone(p.step(.65,3,synthetic=True)['intent'])
 def test_real_policy_blocked(self):self.assertIsNone(Policy(.1,.2,1,0,.25).step(.9,0)['intent'])
 def test_watch_no_sale(self):self.assertIsNone(Policy(.1,.2,1,0,.25).step(.4,0,synthetic=True)['intent'])
 def test_confirmation(self):self.assertIsNone(Policy(.1,.2,2,0,.25).step(.55,0,synthetic=True)['intent'])
 def test_ladder_floor(self):self.assertEqual(ladder_target(200,100),.5);self.assertAlmostEqual(ladder_target(102,100),.95)
 def test_log_tamper(self):
  a=[];append_record(a,{'x':1});append_record(a,{'x':2});self.assertTrue(verify_chain(a));a[0]['x']=3;self.assertFalse(verify_chain(a))
 def test_no_metric_fabrication(self):self.assertTrue(all(x is None for x in demo()['economic_metrics'].values()))
 def test_offset_future_rejected(self):
  s=snapshot();s['ingested_at']='2030-01-01T20:00:00-05:00'
  with self.assertRaises(ValueError):validate_snapshot(s)
 def mark(self,actions,price=100):
  t='2030-01-02T22:00:00+00:00';return dict(session=1,at=t,actions=actions,actions_complete=True,cash_accrual={'USD':0},prices={'FAKE':dict(price=price,at=t,source_hash='synthetic')},fx={'USD':dict(rate=1,at=t,source_hash='synthetic')})
 def test_split_no_double_count(self):
  s=snapshot();initial,path=nav_path(s,[self.mark([dict(type='split',id='s',symbol='FAKE',ratio=2)],50)]);self.assertEqual(initial,path[0]['nav']);self.assertEqual(s['positions'][0]['shares'],1)
 def test_dividend_receivable_and_payment(self):
  initial,path=nav_path(snapshot(),[self.mark([dict(type='dividend_ex',id='d',symbol='FAKE',amount=1,pay_at='2030-01-03T00:00:00+00:00')],99)]);self.assertEqual(path[0]['nav'],initial)
 def test_unsynchronised_low_rejected(self):
  m=self.mark([]);m['prices']['FAKE']['at']='2030-01-02T15:00:00+00:00'
  with self.assertRaises(ValueError):nav_path(snapshot(),[m])
 def test_external_flows_excluded(self):
  m=self.mark([]);m['external_flows']=[100]
  with self.assertRaises(ValueError):nav_path(snapshot(),[m])
 def test_unknown_paydate_blocks(self):
  with self.assertRaises(ValueError):nav_path(snapshot(),[self.mark([dict(type='dividend_ex',id='d',symbol='FAKE',amount=1)])])
 def test_transitive_news_dedup(self):
  rows=[dict(event_id='a',text_fingerprint='x'),dict(event_id='b',text_fingerprint='y'),dict(event_id='a',text_fingerprint='y')];self.assertEqual(len(deduplicate(rows)),1)
 def test_missing_fx_provenance(self):
  m=self.mark([]);del m['fx']['USD']['source_hash']
  with self.assertRaises(ValueError):nav_path(snapshot(),[m])
 def test_missing_cash_accrual(self):
  m=self.mark([]);m['cash_accrual']={}
  with self.assertRaises(ValueError):nav_path(snapshot(),[m])
 def test_dividend_paid_once(self):
  a=self.mark([dict(type='dividend_ex',id='d',symbol='FAKE',amount=1,pay_at='2030-01-03T00:00:00+00:00')],99);b=copy.deepcopy(a);b['at']='2030-01-03T22:00:00+00:00';b['session']=2;b['prices']['FAKE']['at']=b['at'];b['fx']['USD']['at']=b['at'];initial,path=nav_path(snapshot(),[a,b]);self.assertEqual([r['nav'] for r in path],[120,120])
 def test_nonbase_fx_revaluation(self):
  s=snapshot();s['positions'][0]['currency']='EUR';s['fx']['EUR']=dict(rate=2,at=s['valuation_at'],source_hash='synthetic');m=self.mark([]);m['fx']['EUR']=dict(rate=1.8,at=m['at'],source_hash='synthetic');initial,path=nav_path(s,[m]);self.assertEqual(initial,220);self.assertEqual(path[0]['nav'],200)
if __name__=='__main__':unittest.main()
