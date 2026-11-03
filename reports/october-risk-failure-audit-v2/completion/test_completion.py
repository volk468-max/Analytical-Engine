import csv,hashlib,json
from datetime import datetime
from pathlib import Path
from aae.engines.decision_engine import DecisionEngine

ROOT=Path(__file__).resolve().parent
def read(n):return json.loads((ROOT/n).read_text())
def rows(n):return list(csv.DictReader((ROOT/n).open()))
def test_baseline_unchanged():
    for p,h in read('baseline.json')['sha256'].items():assert hashlib.sha256((ROOT.parents[2]/p).read_bytes()).hexdigest()==h
def test_exact_equity_calendar_and_dst():
    s=rows('session-calendar.csv');assert len(s)==44
    assert s[-1]['date']=='2026-11-02' and '14:30:00' in s[-1]['open_at'] and '21:00:00' in s[-1]['close_at']
    assert '13:30:00' in s[-2]['open_at']
def test_all_stock_sessions_present():
    s={x['date'] for x in rows('session-calendar.csv')};inp=read('inputs.json')
    for sym in ['AMD','NVDA','MU','TSM','AVGO','AMAT','AMZN','META','PLTR','LRCX','NBIS']:
        assert {r['date'] for r in inp['prices'] if r['symbol']==sym and r['date']>='2026-09-01'}==s
def test_exact_old_ohlc_overlap():assert len(rows('overlap-validation.csv'))==10556 and all(r['match']=='True' for r in rows('overlap-validation.csv'))
def test_unmodified_engine_fixture():
    f=read('support-fixtures.json');assert f[0]['support']==99 and f[0]['support_broken']
    assert f[1]['support']==89 and not f[1]['support_broken']
    assert f[2]['support']==1 and not f[2]['support_broken']
def test_support_condition_not_equivalent_to_reduction_action():
    f=read('support-fixtures.json');assert f[1]['synthetic_action']=='TRIM' and not f[1]['support_broken']
def test_actual_fill_after_signal_and_exact_delay():
    s=rows('session-calendar.csv');ds=[x['date'] for x in s]
    for t in rows('trades.csv'):
        if t['kind']=='INITIAL_BUY':continue
        assert ds.index(t['fill_date'])-ds.index(t['signal_date'])==int(t['delay'])
        assert datetime.fromisoformat(t['fill_open_at'])>datetime.fromisoformat(t['signal_available_at'])
def test_no_future_trade():assert all(t['fill_date']<='2026-11-02' for t in rows('trades.csv'))
def test_nav_and_cash():
    for d in rows('daily-equity.csv'):
        assert abs(float(d['equity'])-float(d['cash'])-float(d['stock_value'])-float(d['dividend_receivable']))<1e-7
        assert float(d['cash'])>=-1e-7 and 0<=float(d['shares_fraction'])<=1+1e-9
def test_macro_never_observed_in_future():
    for r in rows('market-chronology.csv'):
        for s in ['DGS2','DGS10','BAMLC0A0CM','BAMLH0A0HYM2']:
            assert not r[s+'_observation_date'] or r[s+'_observation_date']<=r['date']
def test_original_publication_not_claimed():
    assert all(x['confirmed_trade_signal']=='false' for x in rows('market-chronology.csv'))
    assert all(not x['publication_verified'] for x in read('macro-availability.json'))
def test_causal_prefix_unchanged():
    r=read('results.json');assert r['causal_market_prefix_equal'] and r['equity_prefix_equal']
def test_regular_session_request():
    for s in read('data/manifest.json')['sources']:
        if s['source']=='Yahoo chart':assert 'includePrePost=false' in s['url']
def test_nov2_warning_unfilled_inside_audit():
    w=[x for x in rows('warning-timeline.csv') if x['date']=='2026-11-02'];assert w
    assert all(x['earliest_possible_execution'].startswith('2026-11-03T14:30') and x['execution_status']=='OUTSIDE_AUDIT_CALENDAR_ONLY_NO_FILL' for x in w)
def test_model_portfolio_equal_initial_sleeves():
    r=read('results.json');ss=r['summary']
    for p in r['portfolio']:
        xs=[x for x in ss if x['fraction']==p['fraction'] and x['delay']==p['delay']]
        assert len(xs)==11 and abs(sum(x['final_equity'] for x in xs)/11-p['final_equity'])<1e-7
def test_missing_macro_not_fabricated():
    for s in ['DGS2','DGS10','BAMLC0A0CM','BAMLH0A0HYM2']:
        r=next(x for x in rows('data-coverage.csv') if x['series']==s);assert '2026-11-02' in r['missing_equity_sessions']
def test_fed_release_not_used_before_publication():
    for r in rows('market-chronology.csv'):
        if r['last_known_fed_release']:assert datetime.fromisoformat(r['last_known_fed_release'])<=datetime.fromisoformat(r['available_at'])
def test_macro_assumed_release_gate_is_enforced():
    xs=read('macro-availability.json')
    for r in rows('market-chronology.csv'):
        for s in ['DGS2','DGS10','BAMLC0A0CM','BAMLH0A0HYM2']:
            if r[s+'_observation_date']:
                x=next(x for x in xs if x['series']==s and x['date']==r[s+'_observation_date'])
                assert datetime.fromisoformat(x['available_at_assumed'])<=datetime.fromisoformat(r['available_at'])
