import unittest
from continue_prices import rejection,load_archive


class PriceContinuationTests(unittest.TestCase):
    def row(self,**kw):return dict(dict(Name='A',date='2015-01-02',open='10',high='12',low='9',close='11',volume='100'),**kw)
    def test_missing(self):self.assertTrue(rejection(self.row(open='')))
    def test_nan(self):self.assertEqual(rejection(self.row(close='nan')),'NONFINITE')
    def test_impossible_bar(self):self.assertEqual(rejection(self.row(high='8')),'INVALID_OHLCV')
    def test_identity_quarantine(self):
        self.assertEqual(rejection(self.row(Name='AAL',date='2013-01-02')),'PRE_EFFECTIVE_AAL_IDENTITY')
        self.assertFalse(rejection(self.row(Name='AAL',date='2013-12-09')))
    def test_google_class_split(self):
        self.assertTrue(rejection(self.row(Name='GOOGL',date='2014-04-02')))
        self.assertFalse(rejection(self.row(Name='GOOGL',date='2014-04-03')))


if __name__=='__main__':unittest.main()
