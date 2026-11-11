"""Preregistered sample checks; fixture matches are not empirical qualification."""
from decimal import Decimal
REFERENCES=[dict(symbol='NVDA',date='2024-06-10',kind='split',value='10',tolerance='0',url='https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-first-quarter-fiscal-2025'),dict(symbol='NVDA',date='2021-07-20',kind='split',value='4',tolerance='0',url='https://nvidianews.nvidia.com/news/nvidia-announces-four-for-one-stock-split-pending-stockholder-approval-at-annual-meeting-set-for-june-3'),dict(symbol='MU',date='2024-10-07',kind='dividend',value='0.115',tolerance='0.00000001',url='https://www.wienerborse.at/en/news/vienna-stock-exchange-news/micron-technology-dividends-global-market-10-07-2024/'),dict(symbol='QQQ',date='2024-03-18',kind='dividend',value='0.57345',tolerance='0.0005',url='https://www.nasdaq.com/market-activity/etf/qqq/dividend-history')]

def check_event(observed,reference):
    if any(observed.get(k)!=reference[k] for k in ('symbol','date','kind')):return False
    return abs(Decimal(str(observed['value']))-Decimal(reference['value']))<=Decimal(reference['tolerance'])

def check_price(observed,independent):
    if observed['date']!=independent['date'] or observed['basis']!=independent['basis'] or observed['currency']!=independent['currency']:return False
    return all(abs(observed[k]-independent[k])<=max(.01,abs(independent[k])*1e-4) for k in ('open','high','low','close'))
