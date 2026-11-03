from datetime import date,timedelta
import math
import pytest
from research.fixed_5pct_buyback.engine import simulate,FEE,SLIP

def fixture(values,signals=(0,)):
    bars=[];calendar={};d=date(2026,9,1)
    for v in values:
        while d.weekday()>4:d+=timedelta(days=1)
        day=d.isoformat();o,c,h,l=v if isinstance(v,tuple) else (v,v,v+1,v-1)
        bars.append(dict(date=day,open=o,close=c,high=h,low=l));calendar[day]=dict(open_at=day+'T13:30:00+00:00');d+=timedelta(days=1)
    sig=[dict(date=bars[i]['date'],available_at=(date.fromisoformat(bars[i]['date'])+timedelta(days=1)).isoformat()+'T00:00:00+00:00') for i in signals]
    return bars,sig,calendar
def run(v,signals=(0,),**kw):return simulate(*fixture(v,signals),fraction=.1,**kw)
def test_next_open_not_signal_close():
    r=run([100,(120,110,121,109),120]);assert r['lots'][0]['sale_price']==120*(1-SLIP)
def test_actual_price_drives_limit():
    r=run([100,100,100]);assert r['lots'][0]['limit_price']==100*(1-SLIP)*.95
def test_no_buy_sale_day_even_low_hits():
    r=run([100,(100,90,101,80),100]);assert r['lots'][0]['status']=='OPEN'
def test_touch_fills_limit_next_day():
    r=run([100,100,(100,99,101,90)]);l=r['lots'][0];assert l['buy_price']==l['limit_price'] and l['buy_date']>l['sale_date']
def test_gap_gets_open_price():
    r=run([100,100,(80,82,85,79)]);assert r['lots'][0]['buy_price']==80
def test_no_buy_above_limit():assert run([100,100,102,104])['lots'][0]['status']=='OPEN'
def test_order_persists_until_late_hit():
    r=run([100,100,101,102,103,90]);assert r['lots'][0]['buy_date']==r['daily'][-1]['date']
def test_separate_lots_with_different_limits():
    r=run([100,100,110,120,130],signals=(0,2));assert len(r['lots'])==2 and r['lots'][0]['limit_price']!=r['lots'][1]['limit_price']
def test_other_free_shares_sell_without_first_restore():
    r=run([100,100,110,120,130],signals=(0,2));assert r['summary']['sales']==2 and r['summary']['open_cycles']==2
def test_persistent_risk_not_repeated_without_new_signal():assert run([100]*8)['summary']['sales']==1
def test_rebuy_exact_sold_quantity():
    r=run([100,100,90]);assert r['lots'][0]['restored']==r['lots'][0]['quantity'];assert math.isclose(r['summary']['shares'],r['summary']['original_shares'])
def test_cash_surplus_is_net_of_both_fees():
    r=run([100,100,90]);l=r['lots'][0];assert math.isclose(l['realized_net_cash_surplus'],l['quantity']*(l['sale_price']-l['buy_price'])-l['sale_fee']-l['buy_fee']);assert math.isclose(r['summary']['cash'],l['realized_net_cash_surplus'])
def test_initial_costs_match_protocol():
    r=run([100,100]);assert math.isclose(r['summary']['original_shares'],100000/(100*(1+SLIP)*(1+FEE)))
def test_delay_extra_session():
    r=run([100,110,120,130],delay=2);assert r['lots'][0]['sale_price']==120*(1-SLIP)
def test_sell_unfilled_at_end():
    r=run([100,100],signals=(1,));assert not r['lots'] and r['summary']['unfilled_sell_signal']
def test_open_proceeds_not_profit():
    r=run([100,100,130]);l=r['lots'][0];assert l['realized_net_cash_surplus'] is None and l['unrealized_missing_shares_benefit']<0
def test_nav_reconciles_every_day():
    r=run([100,100,120,90,130],signals=(0,2));assert all(abs(d['equity']-d['cash']-d['stock_value']-d['dividend_receivable'])<1e-7 for d in r['daily'])
def test_no_debt_or_extra_shares():
    b,s,c=fixture([100,100,120,90,80,70],(0,2,4));r=simulate(b,s,c,fraction=.8);assert all(d['shares']>=-1e-7 and d['cash']>=-1e-7 and d['shares_fraction']<=1+1e-9 for d in r['daily'])
def test_sale_only_never_rebuys():assert not any(t['side']=='BUY' for t in run([100,100,20],mode='sale_only')['trades'])
def test_stress_requires_penetration():
    limit=100*(1-SLIP)*.95;r=run([100,100,(100,100,101,limit)],stress=True);assert r['lots'][0]['status']=='OPEN'
def test_base_exact_touch_and_stress_gap_cap():
    limit=100*(1-SLIP)*.95;assert run([100,100,(100,100,101,limit)])['lots'][0]['status']=='CLOSED'
    l=run([100,100,(limit*.9999,limit,limit,limit*.999)],stress=True)['lots'][0];assert l['buy_price']<=limit
def test_causal_daily_prefix():
    b,s,c=fixture([100,100,101,102,80]);r=simulate(b,s,c,fraction=.1);p=simulate(b[:4],s,c,fraction=.1);assert r['daily'][:4]==p['daily']
def test_incomplete_horizon_not_false_sale():
    l=run([100,100,110])['lots'][0];assert not l['horizon_10_complete'] and l['false_sale_10'] is None
def test_horizon_uses_low_not_final_close():
    l=run([100,100]+[(100,110,111,80)]+[110]*10)['lots'][0];assert l['down5_10'] and l['terminal10_return_pct']>0
def test_open_gap_runup_does_not_count_after_buy_high():
    l=run([100,100,(80,120,150,79)])['lots'][0];assert math.isclose(l['runup_possible_including_fill_day_pct'],100*(101/l['sale_price']-1))
def test_intraday_fill_high_order_is_marked_unknown():assert run([100,100,(100,100,150,90)])['lots'][0]['intraday_order_unknown']
def test_ex_dividend_sale_day_held_preopen():
    b,s,c=fixture([100,100,90]);b[1]['dividend']=1;r=simulate(b,s,c,fraction=.1);assert math.isclose(r['summary']['dividend_receivable'],r['summary']['original_shares'])
def test_no_funds_cannot_top_up():
    # Tiny threshold with maximum limit touch can make the net proceeds insufficient after fees.
    r=run([100,100,(100,100,101,99.94)],threshold=.00001);assert not any(t['side']=='BUY' for t in r['trades']) and r['lots'][0]['cash_rejects']==1
def test_same_day_old_buy_new_sale_no_reuse_of_new_lot():
    r=run([100,100,110,(90,80,91,70),100],signals=(0,2));new=r['lots'][1];assert new['sale_date']<new['buy_date'] if new['buy_date'] else True
def test_future_signal_unavailable_at_fill_rejected():
    b,s,c=fixture([100,100]);s[0]['available_at']='2027-01-01T00:00:00+00:00'
    with pytest.raises(ValueError):simulate(b,s,c,fraction=.1)
