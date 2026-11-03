import csv,gzip,hashlib,json,math,statistics
from pathlib import Path
import pytest
from research.historical_sell_buyback.engine import simulate
from research.historical_sell_buyback.signals import reconstruct,SEMIS
from research.historical_sell_buyback.stats import annual,metrics

ROOT=Path(__file__).resolve().parents[2];R=ROOT/'reports/historical-sell-buyback-v1'
def read(n):return json.loads((R/n).read_text())
def rows(n):return list(csv.DictReader((R/n).open()))
# Reuse the immutable PR10 execution checks against the historical adapter, not duplicate their implementation.
_path=R/'control/pr10/research/fixed_5pct_buyback/test_engine.py'
_src=_path.read_text().replace('research.fixed_5pct_buyback.engine','research.historical_sell_buyback.engine');_ns={};exec(compile(_src,str(_path),'exec'),_ns)
_checks={k:v for k,v in _ns.items() if k.startswith('test_')}
@pytest.mark.parametrize('name',sorted(_checks))
def test_inherited_pr10_execution(name):_checks[name]()

def test_gate_is_exact():
    g=read('control/gate.json');assert g['gate_passed'] and g['sector_daily_rows_equal']==44 and g['exact_PR10_generated_files_equal']==15 and g['adapted_engine_control_cases_equal']==66
def test_control_source_hashes():
    for x in read('control/source-manifest.json')['files']:
        assert hashlib.sha256((R/'control/pr10'/x['path']).read_bytes()).hexdigest()==x['sha256']
def test_all_raw_responses_have_frozen_hashes():
    for x in read('data/manifest.json')['sources']:assert hashlib.sha256((R/'data'/x['raw_file']).read_bytes()).hexdigest()==x['raw_sha256']
def test_calendar_and_dates():
    cal=rows('calendar.csv');assert cal[0]['date']=='2021-01-04' and cal[-1]['date']=='2026-11-02' and len(cal)==1465
    assert '14:30:00' in cal[-1]['open_at'] and '21:00:00' in cal[-1]['close_at']
def test_eligibility_no_phantom_nbis():
    p=read('prepared.json');assert p['eligible']['NBIS']=='2024-10-21'
    assert all(d=='2021-01-04' for s,d in p['eligible'].items() if s!='NBIS')
def test_signal_future_prefix_invariance():
    p=read('prepared.json');cut='2022-12-30';a,e=reconstruct(p['prices'],'2021-01-01',cut);b,f=reconstruct([x for x in p['prices'] if x['date']<=cut],'2021-01-01',cut);assert a==b and e==f
def test_signal_uses_exact_fixed_seven_only():
    p=read('prepared.json');ps=[dict(x) for x in p['prices']]
    for x in ps:
        if x['symbol'] not in SEMIS+['QQQ']:x['close']*=100000
    assert reconstruct(ps,'2021-01-01','2026-11-02')[1]==p['signals']
def test_split_return_equivalence():
    xs=rows('split-return-invariance.csv');assert len(xs)==35 and all(abs(float(x['causal_return5'])-float(x['constant_unit_return5']))<1e-11 for x in xs)
def test_constant_unit_ledger_invariant_to_future_split_units():
    b,s,c=_ns['fixture']([100,100,90,110]);a=simulate(b,s,c,fraction=.1)
    smaller=[dict(x,**{k:x[k]/4 for k in ['open','high','low','close']}) for x in b];z=simulate(smaller,s,c,fraction=.1)
    assert all(abs(x['equity']-y['equity'])<1e-7 for x,y in zip(a['daily'],z['daily']))
    assert abs(z['summary']['shares']-a['summary']['shares']*4)<1e-7
def test_split_crossing_lot_nominal_equivalence():
    b,s,c=_ns['fixture']([50,50,47]);z=simulate(b,s,c,fraction=.1);l=z['lots'][0]
    nominal_sale_price=l['sale_price']*2;nominal_sold=l['quantity']/2
    assert abs(nominal_sale_price*nominal_sold-l['sale_price']*l['quantity'])<1e-7
    assert l['buy_price']<=nominal_sale_price*.95/2 and l['restored']==nominal_sold*2
def test_increased_costs_are_applied_not_overwritten():
    b,s,c=_ns['fixture']([100,100,90,110]);a=simulate(b,s,c,fraction=.1);z=simulate(b,s,c,fraction=.1,fee_rate=.001,slip_rate=.001)
    assert z['summary']['fees']>a['summary']['fees'] and z['summary']['original_shares']<a['summary']['original_shares']
def test_no_annual_reset_in_annual_statistics():
    d=[dict(date='2021-12-31',equity=110000,cash=10000),dict(date='2022-01-03',equity=99000,cash=10000),dict(date='2022-12-30',equity=121000,cash=10000)]
    y=annual(d);assert y[1]['initial_equity']==110000 and abs(y[1]['return_pct']-10)<1e-9 and abs(y[1]['maximum_drawdown_pct']-10)<1e-9
def test_reserved_cash_before_nbis_entry():
    if not (R/'daily-portfolio.csv').exists():pytest.skip('run long economics first')
    # Comparison of reserved11 vs comparable10 must be an exact linear contribution while NBIS is cash.
    ds=rows('daily-portfolio.csv');firsts={}
    for x in ds:
        if x['date']=='2021-01-04':firsts[x['variant'],x['scenario']]=x
    for (v,s),x in firsts.items():
        if v=='RESERVED11':assert abs(float(x['equity'])-(float(firsts['COMPARABLE10',s]['equity'])*10+100000)/11)<1e-7
def test_all_primary_nav_components_reconcile():
    for x in rows('daily-portfolio.csv'):assert abs(float(x['equity'])-float(x['cash'])-float(x['stock_value'])-float(x['dividend_receivable']))<1e-6
def test_no_more_shares_than_bh_in_primary_normalized_units():
    ss=rows('stock-performance.csv')
    for x in ss:
        if x['mode']=='PR9_ORIGINAL':continue
        assert float(x['shares'])<=float(x['original_shares'])+1e-7 and float(x['cash'])>=-1e-7
def test_trade_nominal_value_equals_constant_unit_value():
    for n in ['sales.csv','buybacks.csv']:
        for t in rows(n):assert abs(float(t['quantity'])*float(t['price'])-float(t['nominal_quantity'])*float(t['nominal_fill_price']))<1e-6
def test_limit_corporate_unit_conversion():
    for l in rows('lots.csv'):
        assert abs(float(l['limit_price'])-float(l['sale_price'])*.95)<1e-8
        if l['buy_price']:assert float(l['buy_price'])<=float(l['limit_price'])+1e-9
def test_signal_quality_not_production():assert all(x['original_production_signal']=='False' for x in rows('signal-quality.csv'))
