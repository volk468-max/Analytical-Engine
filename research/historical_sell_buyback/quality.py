"""Unconditional diagnostic cohort alongside actual-position-selected sales."""
import csv,json,statistics
from research.historical_sell_buyback.prepare import R,STOCKS,write
def main():
    p=json.loads((R/'prepared.json').read_text());all_rows=[]
    for s in STOCKS:
        bars=sorted([x for x in p['prices'] if x['symbol']==s and x['date']>=p['eligible'][s]],key=lambda x:x['date'])
        for w in p['signals']:
            if w['date']<p['eligible'][s]:continue
            i=next((i+1 for i,x in enumerate(bars) if x['date']==w['date']),None)
            base=dict(symbol=s,signal_date=w['date'],cohort='HYPOTHETICAL_ONE_UNIT_SALE_NO_HOLDINGS_REQUIREMENT_NOT_ACTUAL_TRADE',original_production_signal=False)
            if i is None or i>=len(bars):all_rows.append(dict(**base,execution_status='OUTSIDE_WINDOW_NO_PRICE'));continue
            sale=bars[i]['open']*.9995;future=bars[i+1:];limit=sale*.95;hit=next((x for x in future if x['low']<=limit),None)
            before=[x for x in future if not hit or x['date']<hit['date']];inclusive=[x for x in future if not hit or x['date']<=hit['date']]
            z=dict(**base,execution_status='HYPOTHETICAL_EXECUTABLE',hypothetical_execution_date=bars[i]['date'],hypothetical_execution_price=sale,nominal_hypothetical_execution_price=sale*bars[i]['split_future_factor'],first_down5_date=hit['date'] if hit else None,wait_sessions=next((j+1 for j,x in enumerate(future) if hit and x['date']==hit['date']),None),runup_before_hit_day_pct=100*(max([sale,bars[i]['high']]+[x['high'] for x in before])/sale-1),runup_inclusive_possible_upper_pct=100*(max([sale,bars[i]['high']]+[x['high'] for x in inclusive])/sale-1),sale_day_hit5=bars[i]['low']<=limit)
            for n in [5,10,20]:
                xs=future[:n];complete=len(xs)==n;z['complete_'+str(n)]=complete;z['down5_'+str(n)]=any(x['low']<=limit for x in xs) if complete else None;z['terminal_'+str(n)+'_pct']=100*(xs[-1]['close']/sale-1) if complete else None;z['observed_max_drop_'+str(n)+'_pct']=100*max(0,1-min(x['low'] for x in xs)/sale) if xs else None
            all_rows.append(z)
    write('signal-quality-all-eligible.csv',all_rows)
    old=list(csv.DictReader((R/'signal-quality.csv').open()))
    for w in old:
        xs=[x for x in all_rows if x['signal_date']==w['signal_date']];execs=[x for x in xs if x['execution_status']=='HYPOTHETICAL_EXECUTABLE'];complete=[x for x in execs if x['complete_10']];wait=[x['wait_sessions'] for x in execs if x['wait_sessions'] is not None]
        w.update(hypothetical_eligible_stocks=len(xs),hypothetical_executable_stocks=len(execs),hypothetical_mature10=len(complete),hypothetical_false10=sum(not x['down5_10'] for x in complete),hypothetical_positive_terminal10=sum(x['terminal_10_pct']>0 for x in complete),hypothetical_ever_hit5=sum(x['first_down5_date'] is not None for x in execs),hypothetical_mean_completed_wait=statistics.mean(wait) if wait else None,selection_note='Actual-position cohort may be depleted; hypothetical cohort kept separate')
    write('signal-quality.csv',old)
if __name__=='__main__':main()
