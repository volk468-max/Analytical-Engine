import csv,gzip,hashlib,json,math,random
from pathlib import Path
import pytest
from research.signal_predictive_accuracy.engine import classify,outcome,episodes,features
from research.signal_predictive_accuracy.baselines import block_weights,design,estimate
from research.signal_predictive_accuracy.io import R,load,rows,STOCKS,MARKETS

def bars(values):
    return [dict(date=f'2026-01-{i+1:02d}',open=o,high=h,low=l,close=c,factor=1) for i,(o,h,l,c) in enumerate(values)]
def flat(n=12):return bars([(100,101,99,100)]*n)
def test_down_first_tp():assert classify(bars([(100,102,94,98),(98,106,97,104)]),100,horizon=2)['classification']=='TRUE_POSITIVE'
def test_up_first_fp_even_later_crash():assert classify(bars([(100,106,99,104),(100,101,80,90)]),100,horizon=2)['classification']=='FALSE_POSITIVE'
def test_same_bar_unknown_not_guessed_from_gap():
    x=classify(bars([(90,110,85,100)]),100,horizon=1);assert x['classification']=='UNKNOWN' and x['order']=='SAME_BAR_UNKNOWN'
def test_neither_is_false_only_full_horizon():
    assert classify(flat(10),100)['classification']=='FALSE_POSITIVE'
    assert classify(flat(9),100)['classification']=='UNRESOLVED'
def test_partial_window_may_decide_tp_but_is_not_complete():
    x=classify(bars([(100,101,90,95)]),100);assert x['classification']=='TRUE_POSITIVE' and not x['complete']
def test_partial_up_first_is_decided_false():assert classify(bars([(100,110,99,105)]),100)['classification']=='FALSE_POSITIVE'
def test_no_reference_unresolved():assert classify([],None)['classification']=='UNRESOLVED'
def test_first_event_same_day_only_not_later_hits():
    x=classify(bars([(100,102,94,99),(100,110,90,100)]),100,horizon=2);assert x['classification']=='TRUE_POSITIVE'
def test_exact_threshold_touch_counts():assert classify(bars([(100,104,95,100)]),100,horizon=1)['classification']=='TRUE_POSITIVE'
def test_primary_open_is_next_session_not_signal_close():
    a=bars([(100,101,99,100),(110,111,109,110)]);x=outcome(a,0,'OPEN');assert x['reference_price']==110 and x['return_1_pct']==0
def test_close_anchor_separate():
    a=bars([(100,101,99,100),(110,111,109,110)]);x=outcome(a,0,'CLOSE');assert x['reference_price']==100 and abs(x['return_1_pct']-10)<1e-9
def test_execution_session_included_and_signal_day_excluded():
    a=bars([(100,150,50,100),(100,102,94,99)]);x=outcome(a,0);assert x['classification']=='TRUE_POSITIVE' and x['down_latency']==1
def test_terminal_return_not_intrahorizon_target():
    a=bars([(100,101,99,100),(100,104,94,99),(100,103,99,102)]);x=outcome(a,0);assert x['classification']=='TRUE_POSITIVE' and x['return_1_pct']<0 and x['return_3_pct'] is None
def test_longer_future_suffix_not_change_short_outcomes():
    a=flat(22);a[3]['low']=94;x=outcome(a,0);z=outcome(a[:11],0);assert x['classification']==z['classification'] and x['max_drop_10_pct']==z['max_drop_10_pct']
def test_features_no_future_suffix():
    a=flat(70);a[-1]['close']=1;assert features(a,40)==features(a[:41],40)
def test_split_unit_changes_no_event_or_return():
    a=flat(22);a[2]['low']=90;sm=[dict(x,**{k:x[k]/10 for k in ['open','high','low','close']}) for x in a];x=outcome(a,0);y=outcome(sm,0);assert x['classification']==y['classification'] and abs(x['max_drop_20_pct']-y['max_drop_20_pct'])<1e-9
def test_nested_decline_is_one_episode():
    a=bars([(100,101,99,100),(95,96,94,95),(97,98,96,97),(85,86,84,85),(100,101,99,100)]);e=episodes(a,a[0]['date'],a[-1]['date']);assert len(e)==1 and e[0]['status']=='RECOVERED' and abs(e[0]['depth_pct']-15)<1e-9
def test_unfinished_recovery_not_fabricated():
    a=bars([(100,101,99,100),(80,81,79,80)]);e=episodes(a,a[0]['date'],a[-1]['date']);assert len(e)==1 and e[0]['recovery_date'] is None
def test_distinct_recovered_events_not_merged():
    a=bars([(100,101,99,100),(90,91,89,90),(100,101,99,100),(94,95,93,94)]);assert len(episodes(a,a[0]['date'],a[-1]['date']))==2
def test_block_weights_total_and_deterministic():
    a=block_weights(1465,60,random.Random(1));b=block_weights(1465,60,random.Random(1));assert a==b and sum(a)==1465 and min(a)>=0
def test_bootstrap_uses_shared_control_weights():
    d=dict(data=[dict(score=1),dict(score=0),dict(score=1)],candidates={('a',):[1,2]},pairs=[(0,('a',))]);assert estimate(d,[1,1,1])==(1,.5,.5);assert estimate(d,[1,0,2])==(1,1,0)
def test_matching_empty_cells_stay_unmatched():
    a=[dict(date='2026-01-01',quarter='2026Q1',regime='BULL',eligible_signature='A',complete10=True,score=1,calendar_index=0,sector_warning=True,mechanical=False,dd_bin='LT3')];d=design(a,'RANDOM_MATCHED','STOCK');assert d['unmatched']==['2026-01-01'] and not d['pairs']
def test_mechanical_can_overlap_real_warning():
    a=[dict(date='2026-01-01',quarter='2026Q1',regime='BULL',eligible_signature='A',complete10=True,score=1,calendar_index=0,sector_warning=True,mechanical=True,dd_bin='LT3')];assert design(a,'MECHANICAL_QQQ_R5','STOCK')['pairs']
def test_source_integrity_and_original_dates():
    p=load();assert len(p['signals'])==134 and p['signals'][-1]['date']=='2026-11-02'
def test_primary_table_no_unknown_as_false():
    xs=[x for x in rows(R/'signals.csv') if x['cohort']=='STOCK' and x['anchor']=='OPEN'];assert len(xs)==1385
    assert sum(x['classification']=='UNKNOWN' for x in xs)==4 and sum(x['classification']=='UNRESOLVED' for x in xs)==11
def test_nbis_not_included_before_eligibility():assert all(x['signal_date']>='2024-10-21' for x in rows(R/'signals.csv') if x['symbol']=='NBIS')
def test_no_production_accuracy_claims():assert all(x['production_confirmed']=='False' for x in rows(R/'signals.csv'))
def test_primary_maturity_excludes_last_day():
    c=json.loads((R/'control-cache.json').read_text());assert not c[-1]['complete10'] and c[-11]['complete10']
def test_baseline_match_never_conditions_on_future_labels():
    # Candidate cell is determined by quarter/regime/eligibility, not score.
    a=[dict(date='2026-01-01',quarter='2026Q1',regime='BULL',eligible_signature='A',complete10=True,score=1,calendar_index=0,sector_warning=True,mechanical=True,dd_bin='LT3'),dict(date='2026-01-02',quarter='2026Q1',regime='BULL',eligible_signature='A',complete10=True,score=0,calendar_index=1,sector_warning=False,mechanical=True,dd_bin='LT3')];x=design(a,'RANDOM_MATCHED','STOCK');a[1]['score']=1;y=design(a,'RANDOM_MATCHED','STOCK');assert x['pairs']==y['pairs'] and x['candidates']==y['candidates']
def test_missed_event_matching_never_same_close_warning():
    for x in rows(R/'missed-falls.csv'):
        if x['warning_date']:assert x['warning_date']<x['threshold_date'] and int(x['signal_lead_sessions'])>=1 and int(x['execution_lead_sessions'])>=0
def test_confidence_adjusts_two_primary_comparisons():
    xs=rows(R/'baseline-confidence.csv');p=[x for x in xs if x['cohort']=='STOCK' and x['model']!='DRAWDOWN_MATCHED_RANDOM']
    assert len(p)==6 and all(float(x['marginal_confidence'])==.975 and int(x['resamples'])==1999 for x in p)
def test_all_control_panels_match_prespecified_cells_and_frequency():
    import io,collections
    cache={x['date']:x for x in json.loads((R/'control-cache.json').read_text())};counts=collections.Counter()
    with gzip.open(R/'matched-control-panels.csv.gz','rt') as f:
        for x in csv.DictReader(f):
            a=cache[x['warning_date']];b=cache[x['control_date']]
            assert a['quarter']==b['quarter'] and a['regime']==b['regime'] and a['eligible_signature']==b['eligible_signature']
            if x['model']=='MECHANICAL_QQQ_R5':assert b['mechanical']
            else:assert not b['sector_warning']
            if x['model']=='DRAWDOWN_MATCHED_RANDOM':assert a['dd_bin']==b['dd_bin']
            counts[x['model'],int(x['panel'])]+=1
    matches={x['model']:int(x['matched_warning_dates']) for x in rows(R/'baseline-comparison.csv') if x['cohort']=='STOCK'}
    assert len(counts)==1500 and all(n==matches[model] for (model,panel),n in counts.items())
def test_primary_event_catalogue_has_no_nested_overlaps():
    xs=rows(R/'drawdown-events.csv')
    for s in STOCKS:
        es=sorted((x for x in xs if x['symbol']==s),key=lambda x:x['start_date'])
        for a,b in zip(es,es[1:]):assert a['recovery_date'] and a['recovery_date']<b['start_date']
def test_missing_prehistory_not_counted_as_zero_drawdown():
    xs=[x for x in rows(R/'signals.csv') if x['cohort']=='STOCK' and x['anchor']=='OPEN' and x['complete_10']=='True'];known=[x for x in xs if x['known_drawdown_20_pct']!='']
    stat=next(x for x in rows(R/'statistics.csv') if x['cohort']=='STOCK' and x['anchor']=='OPEN' and x['group']=='ALL');assert int(stat['known_dd20_rows'])==len(known)
    assert abs(float(stat['already_down5_fraction'])-sum(float(x['known_drawdown_20_pct'])>=5 for x in known)/len(known))<1e-12
