import unittest,numpy as np,csv,gzip,json,hashlib
from study import *
class Tests(unittest.TestCase):
 def test_equal(self):np.testing.assert_allclose(frozen_path(np.ones((61,3))*100,np.zeros((61,3)),0,np.ones(3)/3,0),1)
 def test_cash(self):np.testing.assert_allclose(frozen_path(np.vstack([np.ones(3)*100,np.ones((60,3))*80]),np.zeros((61,3)),0,np.ones(3)*.2,.4),.88)
 def test_bounds(self):
  w=capped_inverse([.01,1,10]);self.assertAlmostEqual(w.sum(),1);self.assertTrue(np.all(w>=.1));self.assertTrue(np.all(w<=.5))
 def test_equal_vol(self):np.testing.assert_allclose(capped_inverse([1,1,1]),np.ones(3)/3)
 def test_no_future_weights(self):
  rng=np.random.default_rng(4);c=np.exp(np.cumsum(rng.normal(0,.03,(303,3)),axis=0));d=np.zeros_like(c);w=weights_at(c,d,252);c[253:]=1e9;np.testing.assert_allclose(w,weights_at(c,d,252))

 def test_immature(self):self.assertIsNone(frozen_path(np.ones((60,3)),np.zeros((60,3)),0,np.ones(3)/3,0))
 def test_gap(self):
  c=np.ones((61,3));c[2,1]=np.nan;self.assertIsNone(frozen_path(c,np.zeros_like(c),0,np.ones(3)/3,0))
 def test_dividend_cash(self):
  c=np.ones((61,3))*99;c[0]=100;d=np.zeros_like(c);d[1]=1;np.testing.assert_allclose(frozen_path(c,d,0,np.ones(3)/3,0),1)
 def test_unit_invariant(self):
  c=np.ones((61,3))*100;d=np.zeros_like(c);np.testing.assert_allclose(frozen_path(c,d,0,np.ones(3)/3,0),frozen_path(c*.1,d*.1,0,np.ones(3)/3,0))
 def test_exact_boundary(self):
  c=np.ones((61,3))*100;c[-1]=90;self.assertAlmostEqual(min(frozen_path(c,np.zeros_like(c),0,np.ones(3)/3,0)),.9)
 def test_no_event(self):self.assertGreater(min(frozen_path(np.ones((61,3))*100,np.zeros((61,3)),0,np.ones(3)/3,0)),.9)
 def test_source_hash(self):
  for r in json.loads((OUT/'sources.json').read_text()):self.assertEqual(hashlib.sha256(gzip.decompress((OUT/'data'/(r['symbol']+'.json.gz')).read_bytes())).hexdigest(),r['raw_sha256'])
 def test_actual_maturity(self):
  with gzip.open(OUT/'forecasts.csv.gz','rt') as f:
   for r in csv.DictReader(f):self.assertLess(r['training_last_maturity'],r['date'][:4]+'-01-01');self.assertGreater(r['maturity'],r['date'])
 def test_overlap(self):self.assertEqual(boot(np.ones(240),120).shape,(999,));np.testing.assert_allclose(boot(np.ones(240),120),1)
if __name__=='__main__':unittest.main()
