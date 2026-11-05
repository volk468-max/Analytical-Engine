"""Compare selected observed ticker states to primary-event facts, without repairing data."""
import base64
import csv
import gzip
import io
from audit import OUT, write_csv


def main():
    rows=list(csv.DictReader(io.StringIO(gzip.decompress(base64.b64decode((OUT/'daily-membership.csv.gz.b64').read_bytes())).decode())))
    states={(r['source'],r['date']):set(r['tickers'].split(';')) for r in rows}
    checks=[
        ('fja_sp500','2010-01-04','GOOGL',False,'GOOG class A before 2014-04-03','https://www.nasdaqtrader.com/TraderNews.aspx?id=ETA2014-24'),
        ('thuning_sp500','2010-01-04','GOOGL',False,'GOOG class A before 2014-04-03','https://www.nasdaqtrader.com/TraderNews.aspx?id=ETA2014-24'),
        ('lawcal_sp500','2010-01-04','GOOG',True,'Google class A symbol at date; published helper loses row','https://press.spglobal.com/2014-02-03-Treatment-of-Google-Stock-Split-in-the-S-P-100-and-S-P-500'),
        ('lawcal_sp500','2022-06-08','META',False,'Symbol effective next trading day, not revision date','https://www.nasdaqtrader.com/TraderNews.aspx?id=ECA2022-125'),
        ('thuning_ndx','2015-12-21','ENDP',True,'Official addition; alternative NDOI is not silently mapped','https://ir.nasdaq.com/news-releases/news-release-details/annual-changes-nasdaq-100-index-4'),
        ('thuning_ndx','2014-12-22','CMCSK',True,'Official Class A Special addition','https://ir.nasdaq.com/news-releases/news-release-details/annual-changes-nasdaq-100-index-3'),
        ('thuning_ndx','2010-01-04','NLOK',False,'Symbol became NLOK in November 2019','https://www.nasdaq.com/press-release/symantec-completes-sale-of-enterprise-security-assets-to-broadcom-2019-11-04'),
        ('thuning_ndx','2017-01-03','QRTEA',False,'Symbol became QRTEA in March 2018','https://investors.qvcgrp.com/news-media/press-releases/detail/14/liberty-interactive-and-gci-liberty-announce-completion-of'),
    ]
    result=[]
    for source,day,ticker,expected,reason,url in checks:
        observed=ticker in states[source,day]
        result.append(dict(source=source,date=day,symbol=ticker,expected_symbol_present=expected,observed_symbol_present=observed,
            symbol_check_matches=expected==observed,reason=reason,primary_source=url,automatic_repair=False))
    write_csv(OUT/'primary-checks.csv',result)
    print('Primary symbol checks:',len(result),'mismatches:',sum(not r['symbol_check_matches'] for r in result))


if __name__=='__main__':main()
