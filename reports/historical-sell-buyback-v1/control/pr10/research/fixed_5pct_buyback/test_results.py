"""Cross-ledger identities and archived-benchmark checks, not mirrored signal rules."""
import csv,hashlib,json
from datetime import datetime
from pathlib import Path
import pytest
R=Path(__file__).resolve().parents[2]/'reports/fixed-5pct-buyback-v1'
def rows(n):return list(csv.DictReader((R/n).open()))
def test_input_snapshots_unchanged():
    root=R.parents[1]
    for x in json.loads((R/'inputs/provenance.json').read_text())['read_only_snapshots']:
        assert hashlib.sha256((root/x['local']).read_bytes()).hexdigest()==x['sha256']
def test_published_signals_used_without_redefinition():
    s=[x for x in rows('inputs/warning-timeline.csv') if x['flag']=='sector_flag'];assert rows('signals-used.csv')==s
def test_initial_shares_identical_to_buy_hold():
    ss=rows('stock-results.csv')
    for x in ss:
        if x['scenario'].startswith('E_'):continue
        b=next(z for z in ss if z['symbol']==x['symbol'] and z['scenario']=='A_BUY_HOLD');assert x['original_shares']==b['original_shares']
def test_portfolio_nav_components_reconcile():
    for x in rows('daily-portfolio-equity.csv'):
        assert abs(float(x['equity'])-float(x['stock_value'])-float(x['cash'])-float(x['dividend_receivable']))<1e-7
def test_terminal_nav_relative_to_hold_matches_lot_cash_and_dividends():
    lots=rows('cycles.csv')
    for x in rows('stock-results.csv'):
        if x['scenario'].startswith('E_'):continue
        ls=[l for l in lots if l['scenario']==x['scenario'] and l['symbol']==x['symbol']]
        delta=sum(float(l['realized_net_cash_surplus'] or 0)+float(l['unrealized_missing_shares_benefit'])-float(l['missed_dividends']) for l in ls)
        assert abs(delta-float(x['excess_vs_buyhold']))<1e-6
def test_open_lots_account_for_entire_share_deficit():
    ls=rows('cycles.csv')
    for x in rows('stock-results.csv'):
        if x['scenario'].startswith('E_'):continue
        missing=sum(float(l['quantity']) for l in ls if l['scenario']==x['scenario'] and l['symbol']==x['symbol'] and l['status']=='OPEN')
        assert abs(missing-float(x['shares_deficit']))<1e-6
def test_actual_calendar_next_open_delay():
    cal=rows('inputs/session-calendar.csv');ds=[x['date'] for x in cal];sig={x['date']:x for x in rows('signals-used.csv')}
    for t in rows('sales.csv'):
        assert ds.index(t['date'])-ds.index(t['signal_date'])==int(t['delay'])
        assert datetime.fromisoformat(cal[ds.index(t['date'])]['open_at'])>datetime.fromisoformat(sig[t['signal_date']]['available_at'])
def test_no_buy_on_or_before_lot_sale_and_no_limit_violation():
    lots={(x['scenario'],x['symbol'],x['lot_id']):x for x in rows('cycles.csv')}
    for x in rows('buybacks.csv'):
        l=lots[x['scenario'],x['symbol'],x['lot_id']];assert x['date']>l['sale_date'];assert float(x['price'])<=float(l['limit_price'])+1e-9;assert x['quantity']==l['quantity']
def test_every_portfolio_has_all_44_dates():
    ds=rows('daily-portfolio-equity.csv')
    for s in {x['scenario'] for x in ds}:assert len([x for x in ds if x['scenario']==s])==44
def test_pr9_prior_policy_reproduced():
    assert json.loads((R/'run.json').read_text())['prior_replay_matched']
    xs=rows('comparison.csv');assert abs(float(next(x for x in xs if x['scenario']=='E_PRIOR_0.1_D1')['final_equity'])-90513.68929175907)<1e-7
def test_censored_sale_labels_not_counted_false():
    for l in rows('cycles.csv'):
        if l['horizon_10_complete']=='False':assert l['false_sale_10']==''
