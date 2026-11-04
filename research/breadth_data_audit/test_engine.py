from datetime import date,timedelta
import pytest
from research.breadth_data_audit.engine import BreadthEngine,adjust_splits,divergence

def fixture(n=260,symbols=('A',),values=None):
    ds=[(date(2020,1,1)+timedelta(days=i)).isoformat() for i in range(n)]
    cal=[dict(date=d,close_at=d+'T21:00:00+00:00') for d in ds]
    bars=[dict(security_id=s,date=d,close=(values[i] if values else 100+i),high=(values[i] if values else 100+i)+1,low=(values[i] if values else 100+i)-1,available_at=d+'T22:00:00+00:00',publication_verified=True) for s in symbols for i,d in enumerate(ds)]
    ms=[dict(effective_date=ds[0],available_at=ds[0]+'T00:00:00+00:00',members=list(symbols),pit_verified=True)]
    meta=dict(universe='UNIT_TEST',membership_kind='VERIFIED_SNAPSHOT',source='synthetic_test_fixture',source_version='test',price_basis='ASOF_SPLIT_ADJUSTED_PRICE_ONLY',membership_history_complete=True,publication_times_verified=True,corporate_actions_verified=True,calendar_verified=True,security_ids_verified=True)
    return bars,cal,ms,meta
def result(args,i=-1):
    d=args[1][i]['date'];return BreadthEngine(*args).calculate(d,d+'T23:00:00+00:00')
def test_ma50_and_ma200_exact():
    a=fixture();r=result(a);assert r['pct_above_ma50']==r['pct_above_ma200']==100 and r['historical_backtest_eligible']
def test_equal_ma_is_not_above():
    r=result(fixture(values=[100]*260));assert r['pct_above_ma50']==r['pct_above_ma200']==0
def test_denominator_is_metric_eligible_not_universe_implicitly():
    a=list(fixture(symbols=('A','B')));a[0]=[r for r in a[0] if not(r['security_id']=='B' and r['date']==a[1][-2]['date'])];r=result(a)
    assert r['universe_size']==2 and r['eligible_ma50']==1 and r['coverage_ma50']==.5
    assert r['pct_above_ma50'] is None and r['pct_above_ma50_observed']==100
def test_coverage_policy_explicit_and_no_zero_fill():
    a=list(fixture(symbols=('A','B')));a[0]=[r for r in a[0] if r['security_id']!='B'];d=a[1][-1]['date'];r=BreadthEngine(*a,min_coverage=.5).calculate(d,d+'T23:00:00+00:00')
    assert r['pct_above_ma50']==100 and r['coverage']==.5
def test_ipo_warmup_is_ineligible_not_bearish():
    a=list(fixture());a[0]=a[0][-30:];r=result(a);assert r['eligible_ma50']==0 and r['pct_above_ma50'] is None
def test_delisted_removed_member_not_in_denominator():
    a=list(fixture(symbols=('A','B')));d=a[1][-1]['date'];a[2].append(dict(effective_date=d,available_at=d+'T00:00:00+00:00',members=['A'],pit_verified=True));assert result(a)['universe_size']==1
def test_future_effective_membership_not_early():
    a=list(fixture());d=a[1][-1]['date'];a[2].append(dict(effective_date='2099-01-01',available_at=d+'T00:00:00+00:00',members=['B'],pit_verified=True));assert result(a)['members']=='A'
def test_membership_published_late_not_used():
    a=list(fixture());d=a[1][-1]['date'];a[2].append(dict(effective_date=d,available_at='2099-01-01T00:00:00+00:00',members=['B'],pit_verified=True));assert result(a)['members']=='A'
def test_no_membership_means_unavailable():
    a=list(fixture());a[2]=[];r=result(a);assert r['universe_size']==0 and not r['historical_backtest_eligible']
def test_bar_after_decision_unavailable():
    a=list(fixture());a[0][-1]['available_at']='2099-01-01T00:00:00+00:00';r=result(a);assert r['available_components']==0 and r['pct_above_ma50'] is None
def test_before_close_rejected():
    a=fixture();d=a[1][-1]['date']
    with pytest.raises(ValueError,match='not closed'):BreadthEngine(*a).calculate(d,d+'T20:00:00+00:00')
def test_bar_claiming_publication_before_close_rejected():
    a=list(fixture());a[0][-1]['available_at']=a[1][-1]['date']+'T20:00:00+00:00';assert result(a)['available_components']==0
def test_no_lookahead_prefix_invariance():
    a=fixture();d=a[1][250]['date'];e=BreadthEngine(*a);before=e.calculate(d,d+'T23:00:00+00:00');a[0][-1]['close']=100000;after=BreadthEngine(*a).calculate(d,d+'T23:00:00+00:00');assert before==after
def test_split_causal_normalization_no_fake_decline():
    rows=[dict(security_id='A',date='2020-01-01',high=102,low=98,close=100,available_at='2020-01-01T22:00:00+00:00'),dict(security_id='A',date='2020-01-02',high=51,low=49,close=50,available_at='2020-01-02T22:00:00+00:00')]
    action=dict(security_id='A',effective_date='2020-01-02',ratio=2,available_at='2020-01-01T12:00:00+00:00')
    assert adjust_splits(rows,[action],'2020-01-02','2020-01-02T23:00:00+00:00')[0]['close']==50
    assert adjust_splits(rows,[action],'2020-01-01','2020-01-01T23:00:00+00:00')[0]['close']==100
def test_future_split_publication_excluded():
    a=fixture(2);action=dict(security_id='A',effective_date=a[1][0]['date'],ratio=2,available_at='2099-01-01T00:00:00+00:00');assert adjust_splits(a[0],[action],a[1][1]['date'],a[1][1]['date']+'T23:00:00+00:00')[0]['close']==100
def test_uniform_split_unit_scaling_invariant():
    a=fixture();r=result(a)
    for x in a[0]:
        for k in ['close','high','low']:x[k]/=10
    z=result(a)
    for k in ['pct_above_ma50','pct_above_ma200','advances','new_highs','new_lows']:assert r[k]==z[k]
def test_high_low_excludes_current_252_prior_sessions():
    a=fixture(253);r=result(a);assert r['new_highs']==1 and r['new_lows']==0
    a[0][-1]['high']=a[0][-2]['high'];a[0][-1]['close']=a[0][-2]['close'];assert result(a)['new_highs']==0
def test_extrema_warmup_exact_253():assert result(fixture(252))['new_highs'] is None
def test_ad_zero_denominator_not_infinity():
    r=result(fixture());assert r['advances']==1 and r['declines']==0 and r['ad_ratio'] is None and r['ad_ratio_state']=='NO_DECLINERS'
def test_missing_gap_not_bridged():
    a=list(fixture());a[0].pop(-10);assert result(a)['pct_above_ma50'] is None
def test_duplicate_member_and_bar_rejected():
    a=list(fixture());a[0].append(a[0][0])
    with pytest.raises(ValueError,match='duplicate security'):BreadthEngine(*a)
    a=list(fixture());a[2][0]['members']=['A','A']
    with pytest.raises(ValueError,match='duplicate member'):BreadthEngine(*a)
def test_security_identity_survives_ticker_rename():
    a=fixture()
    for i,x in enumerate(a[0]):x['ticker']='OLD' if i<150 else 'NEW'
    assert result(a)['pct_above_ma200']==100
def test_proxy_never_historical_index():
    a=list(fixture());a[2][0]['pit_verified']=False;assert not result(a)['historical_backtest_eligible']
def test_unverified_bar_publication_fails_closed():
    a=fixture();a[0][-1]['publication_verified']=False;assert not result(a)['historical_backtest_eligible']
def test_calendar_and_price_basis_validation():
    a=list(fixture());a[1]=list(reversed(a[1]))
    with pytest.raises(ValueError,match='calendar'):BreadthEngine(*a)
    a=list(fixture());a[3]['price_basis']='MIXED'
    with pytest.raises(ValueError,match='basis'):BreadthEngine(*a)
def test_deterministic_and_divergence_causal_inputs():
    assert result(fixture())==result(fixture())
    assert divergence(dict(members='A',pct_above_ma50=40),dict(members='A',pct_above_ma50=60),1)
    assert divergence(dict(members='B',pct_above_ma50=40),dict(members='A',pct_above_ma50=60),1) is None
def test_mixed_bar_basis_rejected():
    a=fixture();a[0][-1]['price_basis']='RAW'
    with pytest.raises(ValueError,match='mixed'):BreadthEngine(*a)
def test_new_low_and_flat_ad():
    assert result(fixture(values=[100]*252+[90]*8))['new_lows']==0
    a=fixture(253,values=[100]*252+[90]);r=result(a);assert r['new_lows']==1 and r['declines']==1
    r=result(fixture(values=[100]*260));assert r['unchanged']==1 and r['ad_ratio_state']=='NO_DIRECTIONAL_MOVES'
