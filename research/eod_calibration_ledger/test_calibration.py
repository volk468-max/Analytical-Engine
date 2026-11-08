import unittest,math,json,copy
from datetime import date,timedelta
from calibration import *
class Tests(unittest.TestCase):
 def test_intercept_zero_balanced(self):self.assertAlmostEqual(calibrate([.5]*20,[0,1]*10),0)
 def test_regularization(self):self.assertLess(abs(calibrate([.9]*100,[0,1]*50)),abs(logit(.9)))
 def test_ranking_unchanged(self):
  p=[.2,.4,.6,.8]*100;y=[0,0,1,0]*100;a=calibrate(p,y);self.assertEqual(sorted(range(len(p)),key=lambda i:p[i]),sorted(range(len(p)),key=lambda i:logistic(logit(p[i])+a)))
 def test_unsupported_blocked(self):
  with self.assertRaises(ValueError):calibrate([.5],[1],False)
 def test_invalid_probability(self):
  with self.assertRaises(ValueError):calibrate([1],[1])
 def test_maturity_embargo(self):
  dates=[(date(2000,1,1)+timedelta(days=i)).isoformat() for i in range(6000)];rows=[dict(index=i,date=d,maturity=dates[i+60],y=i%2,regime='UP') for i,d in enumerate(dates[:-60])];tr,ca,te=split(rows,2013,dates);self.assertLess(max(r['maturity'] for r in tr),min(r['date'] for r in ca));self.assertLess(max(r['maturity'] for r in ca),min(r['date'] for r in te))
 def test_bank_ignores_future_labels(self):
  tr=[dict(y=0,regime='UP'),dict(y=1,regime='DOWN')];rows=[dict(y=0,regime='UP')];a=frozen_probabilities(tr,rows,'regime');rows[0]['y']=1;self.assertEqual(a,frozen_probabilities(tr,rows,'regime'))
 def test_all_noevent_anchors_included(self):self.assertEqual(frozen_probabilities([dict(y=0)]*100,[{}])[0],1/102)
 def test_deterministic(self):self.assertEqual(calibrate([.7]*50,[0,1]*25),calibrate([.7]*50,[0,1]*25))
 def test_real_results_blocked(self):
  rows=blocked_results();self.assertEqual(len(rows),12);self.assertTrue(all(r['brier'] is None and r['calibrated_probability'] is None for r in rows))
 def test_thresholds_unvalidated(self):self.assertTrue(all(r['threshold_51']=='NOT VALIDATED' for r in blocked_results()))
 def test_mock_does_not_claim_collection(self):
  shadow_mock();r=json.loads((OUT/'offline-log-mock.json').read_text());self.assertEqual(r[0]['mode'],'OFFLINE_SYNTHETIC');self.assertIsNone(r[1]['outcome'])
 def test_hash_chain(self):
  rows=[];append(rows,dict(x=1));append(rows,dict(x=2));self.assertEqual(rows[1]['previous_hash'],rows[0]['hash'])
if __name__=='__main__':unittest.main()
