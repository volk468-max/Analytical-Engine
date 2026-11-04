import base64
import csv
import gzip
import io
import json
from pathlib import Path
import tempfile
import unittest
from audit import snapshot_at, load_snapshots, lawcal_active, ma_ready, load_prices, csv_rows, OUT


class AuditTests(unittest.TestCase):
    def test_no_future_snapshot(self):
        ds=['2010-01-04','2010-02-01']; vs=[{'OLD'},{'NEW'}]
        self.assertEqual(snapshot_at(ds,vs,'2010-01-29')[0],{'OLD'})
        self.assertFalse(snapshot_at(ds,vs,'2009-12-31')[0])

    def test_effective_boundary(self):
        self.assertEqual(snapshot_at(['2010-02-01'],[{'NEW'}],'2010-02-01')[0],{'NEW'})

    def test_lawcal_revision_and_removal(self):
        r=dict(date_added='2010-01-04*',date_removed='2010-03-01',created_at='2010-02-01')
        self.assertFalse(lawcal_active(r,'2010-01-05'))
        self.assertTrue(lawcal_active(r,'2010-01-05',False))
        self.assertTrue(lawcal_active(r,'2010-02-01'))
        self.assertFalse(lawcal_active(r,'2010-03-01'))

    def test_duplicate_ticker_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.csv';p.write_text('date,tickers\n2010-01-01,"A,A"\n')
            with self.assertRaises(ValueError):load_snapshots(p)

    def test_missing_price_does_not_fill(self):
        ds=['2020-01-02','2020-01-03','2020-01-06']
        ps={('A',ds[0]):{},('A',ds[2]):{}}
        self.assertFalse(ma_ready(ps,'A',ds,2,3))
        self.assertFalse(ma_ready(ps,'A',ds,1,3))

    def test_future_price_does_not_supply_warmup(self):
        self.assertFalse(ma_ready({('A','2020-01-03'):{}},'A',['2020-01-02','2020-01-03'],0,2))

    def test_invalid_ohlcv_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.csv';p.write_text('symbol,date,open,high,low,close,volume\nA,2010-01-04,5,4,6,5,1\n')
            with self.assertRaises(ValueError):load_prices(p)

    def test_full_output_quality_gates(self):
        s=json.loads((OUT/'summary.json').read_text())
        self.assertFalse(s['historical_backtest_eligible'])
        self.assertFalse(s['live_provider_all_symbols_queried'])
        rows=list(csv.DictReader(io.StringIO(gzip.decompress(base64.b64decode((OUT/'daily-membership.csv.gz.b64').read_bytes())).decode())))
        self.assertEqual(len(rows),4*s['sessions'])
        self.assertEqual(len({(r['source'],r['date']) for r in rows}),len(rows))
        self.assertTrue(all(r['full_membership_verified']=='False' for r in rows))
        self.assertTrue(all(len(r['tickers'].split(';'))==int(r['component_count']) for r in rows))

    def test_yearly_missing_distinct_from_unavailable(self):
        rs=csv_rows(OUT/'historical-membership-coverage.csv')
        self.assertEqual(len(rs),68)
        self.assertTrue(all(int(r['ma200_candidate_observations'])<=int(r['archived_quote_observations']) for r in rs))
        self.assertTrue(all(int(r['archived_quote_observations'])==0 for r in rs if int(r['year'])<2020))

    def test_ticker_identity_not_collapsed_to_issuer(self):
        rs=csv_rows(OUT/'issuer-security-records.csv')
        google=[r for r in rs if r['symbol'] in ('GOOG','GOOGL')]
        self.assertEqual(len(google),2)
        self.assertEqual(google[0]['issuer_cik'],google[1]['issuer_cik'])
        self.assertNotEqual(google[0]['source_record_id'],google[1]['source_record_id'])
        self.assertTrue(all(not r['security_id'] for r in google))


if __name__=='__main__':unittest.main()
