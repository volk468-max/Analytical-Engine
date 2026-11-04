from research.signal_predictive_accuracy.completion import strict,pre_onset,group_stats
from research.signal_predictive_accuracy.engine import outcome

def bars(n):return [dict(date=str(i),open=100,high=101,low=99,close=100) for i in range(n)]
def test_full_ten_required_even_early_touch():
    a=bars(5);a[1]['low']=90;z=outcome(a,0)
    assert z['classification']=='TRUE_POSITIVE' and strict(z)=='UNRESOLVED'
def test_unknown_is_unresolved_in_clarified_spec():
    a=bars(11);a[2].update(low=90,high=110)
    assert strict(outcome(a,0))=='UNRESOLVED'
def test_execution_session_is_first_of_ten():
    a=bars(11);a[1]['low']=90
    assert strict(outcome(a,0))=='TRUE_POSITIVE'
def test_pre_onset_excludes_onset_close_and_later():
    ci={str(i):i for i in range(30)};e=dict(start_date='20',peak_date='19')
    assert pre_onset({'10','19','20','21'},ci,e,5)==['19']
def test_pre_onset_window_boundary():
    ci={str(i):i for i in range(30)};e=dict(start_date='20',peak_date='19')
    assert set(pre_onset({'14','15','19'},ci,e,5))=={'15','19'}
def test_accuracy_does_not_count_unresolved_as_false():
    x=group_stats([{'status':s} for s in ['TRUE_POSITIVE','FALSE_POSITIVE','UNRESOLVED']])
    assert x['precision']==.5 and x['unresolved']==1
