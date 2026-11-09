"""Synthetic invariants; empirical results are not test acceptance criteria."""
import unittest,tempfile,gzip,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
try:
 from .preliminary import *
 from .reconcile_v2 import mu_facts
except ImportError:
 from preliminary import *
 from reconcile_v2 import mu_facts

class QualificationTests(unittest.TestCase):
 def test_rounding_numeric_not_full_qualification(self):
  r=rounding_check('.57345','.573','2024-03-18','2024-03-18');self.assertTrue(r['compatible']);self.assertFalse(r['fully_qualified']);self.assertFalse(r['vendor_policy_confirmed'])
 def test_rounding_wrong_date(self):self.assertFalse(rounding_check('.57345','.573','2024-03-18','2024-03-19')['compatible'])
 def test_wrong_amount_not_excused_as_rounding(self):self.assertFalse(rounding_check('.57355','.573','2024-03-18','2024-03-18')['compatible'])
 def test_hash_mismatch(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'x.gz';p.write_bytes(gzip.compress(b'fixture'))
   with self.assertRaises(ValueError):verified_bytes(p,'0'*64)
 def test_source_duplicates(self):
  f=pd.DataFrame(dict(close=[1,1],open=[1,1],low=[1,1],high=[1,1]),index=['a','a'])
  with self.assertRaises(ValueError):validate_frame(f,['a'])
 def test_source_gap_and_nonpositive(self):
  for value,dates in [(1,['a','b']),(0,['a'])]:
   f=pd.DataFrame(dict(close=[value],open=[1],low=[1],high=[1]),index=['a'])
   with self.assertRaises(ValueError):validate_frame(f,dates)
 def test_record_date_is_not_ex_date(self):
  issuer=b'On September 25, 2024, Micron declared a quarterly dividend of $0.115 per share, payable in cash on October 23, 2024, to shareholders of record on October 7, 2024'
  self.assertTrue(mu_facts(issuer,b'')['issuer_record_payment_amount']);self.assertFalse(mu_facts(issuer,b'')['reconciled'])
 def test_wrong_security_exchange(self):self.assertFalse(mu_facts(b'',b'OTHER US5951121038 0.115 USD 10/07/2024 10/07/2024 10/23/2024')['reconciled'])

class TemporalTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.dates=xc.get_calendar('XNYS',start='2000-01-01',end='2026-11-06').sessions.strftime('%Y-%m-%d').tolist()
  cls.rows=pd.DataFrame([dict(recipe='A',date=d,index=i,maturity=cls.dates[i+60],y=i%2,regime='UP' if i%3 else 'DOWN',vol_bin=i%4) for i,d in enumerate(cls.dates[:-60]) if i>=253])
 def test_exact_purge_and_maturity_boundaries(self):
  tr,ca,te=windows(self.rows,2018,self.dates);tb=next(i for i,d in enumerate(self.dates) if d>='2015-01-01');vb=next(i for i,d in enumerate(self.dates) if d>='2018-01-01')
  self.assertLess(tr['index'].max(),tb-60);self.assertGreaterEqual(ca['index'].min(),tb+60);self.assertLess(ca.maturity.max(),self.dates[vb-60]);self.assertEqual(te['index'].min(),vb+60);self.assertLess(tr.maturity.max(),ca.date.min());self.assertLess(ca.maturity.max(),te.date.min())
 def test_test_labels_cannot_change_frozen_model(self):
  a,_=fit_year(self.rows,2018,self.dates);other=self.rows.copy();other.loc[other.date>='2018-01-01','y']=1-other.loc[other.date>='2018-01-01','y'];b,_=fit_year(other,2018,self.dates)
  self.assertTrue(a)
  for x,y in zip(a,b):
   for m in MODELS:
    for suffix in ('_raw','_cal'):self.assertEqual(x[m+suffix],y[m+suffix])
 def test_unmatured_labels_cannot_change_first_climatology(self):
  a,_=fit_year(self.rows,2018,self.dates);other=self.rows.copy();mask=other.maturity>=a[0]['date'];other.loc[mask,'y']=1-other.loc[mask,'y'];b,_=fit_year(other,2018,self.dates);self.assertEqual(a[0]['CLIM'],b[0]['CLIM']);self.assertLess(a[0]['clim_last_maturity'],a[0]['date'])
 def test_future_calibration_labels_excluded(self):
  a,info=fit_year(self.rows,2018,self.dates);other=self.rows.copy();mask=(other.date<'2018-01-01')&(other.maturity>=a[0]['cal_fit_cutoff']);other.loc[mask,'y']=1-other.loc[mask,'y'];b,info2=fit_year(other,2018,self.dates)
  self.assertEqual(info['HIST_intercept'],info2['HIST_intercept']);self.assertEqual(a[0]['HIST_cal'],b[0]['HIST_cal'])
 def test_low_cal_support_blocked(self):
  rows=self.rows.copy();rows['y']=0;a,s=fit_year(rows,2018,self.dates);self.assertEqual(a,[]);self.assertEqual(s['status'],'INSUFFICIENT_SUPPORT')
 def test_future_prices_do_not_change_C_weights(self):
  c=np.cumprod(1+np.random.default_rng(1).normal(0,.01,(400,3)),axis=0)*100;d=np.zeros_like(c);a=weights(c,d,252,'C');c[253:]*=3;self.assertTrue(np.array_equal(a,weights(c,d,252,'C')));self.assertAlmostEqual(a.sum(),1);self.assertTrue(((a>=.1)&(a<=.5)).all())
 def test_label_exact60_and_excludes61(self):
  c=np.ones((70,3))*100;d=np.zeros_like(c);c[60]=90;self.assertTrue(frozen_label(c,d,0,np.ones(3)/3)[0]);c[60]=100;c[61]=50;self.assertFalse(frozen_label(c,d,0,np.ones(3)/3)[0])
 def test_immature_label_rejected(self):
  with self.assertRaises(ValueError):frozen_label(np.ones((60,3))*100,np.zeros((60,3)),0,np.ones(3)/3)
 def test_effective_support_respects_calendar_positions(self):
  y=np.tile([0.,0.,1.,1.],100);ix=np.arange(400);a=calendar_neff(y,ix,400);self.assertIsNotNone(a);self.assertLessEqual(a,400);self.assertIsNone(calendar_neff(np.zeros(10),np.arange(10),10))
 def test_disjoint_windows_are_not_daily_observation_count(self):
  ix=disjoint_windows(np.arange(1000));self.assertEqual(len(ix),17);self.assertTrue(all(b-a>=60 for a,b in zip(ix,ix[1:])))
 def test_no_network_in_frozen_price_loader(self):
  from unittest.mock import patch
  with patch('socket.socket',side_effect=AssertionError('NETWORK_NOT_ALLOWED')):
   f,d,a=load_prices();self.assertEqual(len(f),4)
 def test_bootstrap_preserves_calendar_gaps(self):
  values=np.array([0.,1.]);indices=np.array([0,300]);a=boot_calendar(values,indices,301,60,reps=200);b=boot_calendar(values,indices,301,60,reps=200);self.assertTrue(np.array_equal(a,b));self.assertTrue(((a>=0)&(a<=1)).all())

class LedgerTests(unittest.TestCase):
 def setUp(self):
  self.dates=pd.bdate_range('2020-01-02',periods=80).strftime('%Y-%m-%d').tolist();self.c=np.ones((80,3))*100;self.d=np.zeros_like(self.c)
 def test_fee_conservation(self):
  u,c,n,f=rebalance(np.zeros(3),100000,0,self.c[0],np.ones(3)/3,.0025);self.assertAlmostEqual(u@self.c[0]+c,100000-f);self.assertGreaterEqual(c,0);self.assertAlmostEqual(f,n*.0025)
 def test_receivables_not_spendable(self):
  u,c,n,f=rebalance(np.zeros(3),0,100000,self.c[0],np.ones(3)/3,0);self.assertEqual(n,0);self.assertEqual(c,0);self.assertEqual(sum(u),0)
 def test_dividend_payment_no_NAV_jump(self):
  self.c[3:]=99;self.d[3]=1;r=ledger(self.c,self.d,self.dates,'A_STATIC',payments={(s,self.dates[3]):self.dates[5] for s in SYMS[:3]},start=1);by={x['date']:x for x in r};self.assertAlmostEqual(by[self.dates[3]]['nav'],100000);self.assertGreater(by[self.dates[3]]['receivable'],0);self.assertEqual(by[self.dates[5]]['receivable'],0);self.assertAlmostEqual(by[self.dates[5]]['nav'],100000)
 def test_unknown_payment_never_spent(self):
  self.d[3]=1;r=ledger(self.c,self.d,self.dates,'B_STATIC',start=1);self.assertGreater(r[-1]['receivable'],0);self.assertEqual(r[-1]['cash'],40000)
 def test_next_session_execution(self):
  r=ledger(self.c,self.d,self.dates,'A',start=1)
  for row in r:
   if row['traded_notional']:self.assertEqual(row['execution_decision_date'],self.dates[row['index']-1])
 def test_monthly_trade_occurs_after_decision_not_same_close(self):
  self.c[:,0]=100*np.power(1.01,np.arange(80));r=ledger(self.c,self.d,self.dates,'A',start=1);by={x['index']:x for x in r}
  for i in range(3,79):
   if self.dates[i][:7]!=self.dates[i-1][:7]:
    self.assertEqual(by[i]['traded_notional'],0);self.assertGreater(by[i+1]['traded_notional'],0);self.assertEqual(by[i+1]['execution_decision_date'],self.dates[i])
 def test_future_prices_cannot_change_prior_account(self):
  a=ledger(self.c,self.d,self.dates,'A',start=1);self.c[40:]*=2;b=ledger(self.c,self.d,self.dates,'A',start=1);self.assertEqual(a[:39],b[:39])
 def test_no_double_split_on_normalized_prices(self):
  r=ledger(self.c,self.d,self.dates,'A_STATIC',start=1);self.assertAlmostEqual(r[0]['units_NVDA'],r[-1]['units_NVDA']);self.assertAlmostEqual(r[-1]['nav'],100000)
 def test_continuous_not_anchor_reset(self):
  self.c[2:]=80;r=ledger(self.c,self.d,self.dates,'A_STATIC',start=1);self.assertAlmostEqual(r[1]['nav'],80000);self.assertAlmostEqual(r[-1]['drawdown'],.2)
 def test_episodes_strict15_boundary(self):self.assertEqual(episodes([False,True,True,False,True]),[2,1])
 def test_exact15_is_not_a_strict_breach(self):
  self.c[2:]=85;r=ledger(self.c,self.d,self.dates,'A_STATIC',start=1);e=economics(r);self.assertAlmostEqual(e['max_dd'],.15);self.assertEqual(e['breach15_days'],0)
 def test_scheduled_zero_trade_keeps_decision_date(self):
  r=ledger(self.c,self.d,self.dates,'A',start=1);by={x['index']:x for x in r}
  for i in range(3,79):
   if self.dates[i][:7]!=self.dates[i-1][:7]:self.assertEqual(by[i+1]['execution_decision_date'],self.dates[i])
 def test_invalid_leverage_rejected(self):
  with self.assertRaises(ValueError):rebalance(np.zeros(3),100000,0,self.c[0],np.ones(3),0)
if __name__=='__main__':unittest.main()
