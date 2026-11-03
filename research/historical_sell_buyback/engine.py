"""Pure daily-bar, segregated-lot research simulator. No application/network imports."""
from datetime import datetime
import math

FEE=.0005
SLIP=.0005

def simulate(bars, signals, calendar, fraction=0, threshold=.05, mode='limit', delay=1, stress=False, capital=100000, fee_rate=FEE, slip_rate=SLIP):
    if not 0<=fraction<=1 or not 0<threshold<1 or delay<1 or int(delay)!=delay:raise ValueError('invalid policy')
    if mode not in ('limit','sale_only'):raise ValueError('invalid mode')
    dates=[b['date'] for b in bars]
    if dates!=sorted(set(dates)):raise ValueError('duplicate/unsorted bars')
    for b in bars:
        if b['low']>min(b['open'],b['close']) or b['high']<max(b['open'],b['close']):raise ValueError('OHLC')
    if any(b['date'] not in calendar for b in bars):raise ValueError('unknown session')
    signal_map={s['date']:s for s in signals}
    original=capital/(bars[0]['open']*(1+slip_rate)*(1+fee_rate));shares=original;cash=0.;receivable=0.
    trades=[dict(side='INITIAL_BUY',date=dates[0],quantity=original,price=bars[0]['open']*(1+slip_rate),fee=original*bars[0]['open']*(1+slip_rate)*fee_rate,slippage=original*bars[0]['open']*slip_rate,lot_id=None)]
    lots=[];orders=[];daily=[];pending=None;peak=capital;maxdd=0
    for i,b in enumerate(bars):
        d=b['date'];receivable+=shares*b.get('dividend',0)
        if pending and pending['due']==i:
            if datetime.fromisoformat(calendar[d]['open_at'])<=datetime.fromisoformat(pending['available_at']):raise ValueError('future signal at fill')
            qty=min(pending['requested'],shares);price=b['open']*(1-slip_rate);fee=qty*price*fee_rate
            if qty>1e-10:
                shares-=qty;cash+=qty*price-fee
                lot=dict(lot_id=len(lots)+1,signal_date=pending['date'],signal_available_at=pending['available_at'],sale_date=d,sale_index=i,sale_price=price,quantity=qty,sale_fee=fee,sale_slippage=qty*b['open']*slip_rate,limit_price=price*(1-threshold),active_index=i+1,budget=qty*price-fee,status='OPEN',buy_date=None,buy_price=None,buy_fee=0.,buy_slippage=0.,restored=0.,cash_rejects=0)
                lots.append(lot);trades.append(dict(side='SELL',date=d,signal_date=pending['date'],quantity=qty,price=price,fee=fee,slippage=lot['sale_slippage'],lot_id=lot['lot_id']))
                if mode=='limit':orders.append(dict(lot_id=lot['lot_id'],created_date=d,active_date=dates[i+1] if i+1<len(dates) else None,limit_price=lot['limit_price'],quantity=qty,status='ACTIVE' if i+1<len(dates) else 'NO_ELIGIBLE_BAR'))
            pending=None
        # New lots are excluded by active_index. Existing gap fills and touches are FIFO.
        if mode=='limit':
            for lot in lots:
                if lot['status']!='OPEN' or i<lot['active_index']:continue
                limit=lot['limit_price'];fill=None;kind=None
                if b['open']<=limit:
                    fill=min(limit,b['open']*(1+slip_rate)) if stress else b['open'];kind='OPEN_GAP'
                elif b['low']<=limit*(1-slip_rate if stress else 1):fill=limit;kind='INTRADAY_TOUCH'
                if fill is None:continue
                cost=lot['quantity']*fill;fee=cost*fee_rate
                if cost+fee>lot['budget']+1e-8:
                    lot['cash_rejects']+=1;continue # all-or-none, never an external top-up
                shares+=lot['quantity'];cash-=cost+fee;lot['budget']-=cost+fee
                lot.update(status='CLOSED',buy_date=d,buy_price=fill,buy_fee=fee,buy_slippage=lot['quantity']*(fill-b['open']) if kind=='OPEN_GAP' and stress else 0.,restored=lot['quantity'],fill_kind=kind)
                trades.append(dict(side='BUY',date=d,quantity=lot['quantity'],price=fill,fee=fee,slippage=lot['buy_slippage'],lot_id=lot['lot_id'],fill_kind=kind))
                next(o for o in orders if o['lot_id']==lot['lot_id']).update(status='FILLED',fill_date=d,fill_price=fill)
        if shares< -1e-7 or shares>original+1e-7 or cash< -1e-7:raise AssertionError('cash/share conservation')
        if d in signal_map and fraction>0:
            if pending:raise ValueError('overlapping pending sale; protocol requires one')
            pending=dict(date=d,available_at=signal_map[d]['available_at'],requested=min(original*fraction,shares),due=i+delay)
        equity=cash+shares*b['close']+receivable;peak=max(peak,equity);maxdd=max(maxdd,1-equity/peak)
        daily.append(dict(date=d,equity=equity,shares=shares,cash=cash,stock_value=shares*b['close'],dividend_receivable=receivable,shares_fraction=shares/original,drawdown_pct=100*(1-equity/peak),open_lots=sum(l['status']=='OPEN' for l in lots)))
    for lot in lots:
        i=lot['sale_index'];after=bars[i+1:];until=[b for b in after if not lot['buy_date'] or b['date']<lot['buy_date']];inclusive=[b for b in after if not lot['buy_date'] or b['date']<=lot['buy_date']]
        if lot.get('fill_kind')=='OPEN_GAP':inclusive=until
        for n in (5,10,20):
            future=after[:n];lot[f'horizon_{n}_complete']=len(future)==n;lot[f'observed_min_low_{n}']=min(b['low'] for b in future) if future else None;lot[f'observed_max_drop_{n}_pct']=100*max(0,1-min(b['low'] for b in future)/lot['sale_price']) if future else None
            lot[f'max_drop_{n}_pct']=lot[f'observed_max_drop_{n}_pct'] if len(future)==n else None
            hit=next((b for b in future if b['low']<=lot['sale_price']*.95),None);lot[f'down5_{n}']=bool(hit) if len(future)==n else None
        hit=next((b for b in after if b['low']<=lot['sale_price']*.95),None);lot['down5_observed_date']=hit['date'] if hit else None;lot['down5_wait_sessions']=dates.index(hit['date'])-i if hit else None
        lot['sale_session_low_drop_pct']=100*max(0,1-bars[i]['low']/lot['sale_price'])
        lot['sale_session_low5_hit']=bars[i]['low']<=lot['sale_price']*.95
        lot['first_down5_including_sale_session']=lot['sale_date'] if lot['sale_session_low5_hit'] else lot['down5_observed_date']
        lot['terminal10_return_pct']=100*(after[9]['close']/lot['sale_price']-1) if len(after)>=10 else None
        lot['false_sale_10']=not lot['down5_10'] if lot['horizon_10_complete'] else None
        lot['runup_before_fill_day_pct']=100*(max([lot['sale_price'],bars[i]['high']]+[b['high'] for b in until])/lot['sale_price']-1)
        lot['runup_possible_including_fill_day_pct']=100*(max([lot['sale_price'],bars[i]['high']]+[b['high'] for b in inclusive])/lot['sale_price']-1)
        lot['intraday_order_unknown']=lot.get('fill_kind')=='INTRADAY_TOUCH'
        lot['gross_savings']=lot['quantity']*(lot['sale_price']-lot['buy_price']) if lot['buy_date'] else None
        lot['realized_net_cash_surplus']=lot['gross_savings']-lot['sale_fee']-lot['buy_fee'] if lot['buy_date'] else None
        lot['wait_sessions']=dates.index(lot['buy_date'])-i if lot['buy_date'] else None
        lot['unrealized_missing_shares_benefit']=lot['budget']-lot['quantity']*bars[-1]['close'] if not lot['buy_date'] else 0.
        lot['missed_dividends']=lot['quantity']*sum(b.get('dividend',0) for b in bars[i+1:] if not lot['buy_date'] or b['date']<=lot['buy_date'])
        lot['terminal_close']=bars[-1]['close'];lot['threshold']=threshold
    fees=sum(t['fee'] for t in trades);slip=sum(t['slippage'] for t in trades)
    return dict(daily=daily,lots=lots,orders=orders,trades=trades,summary=dict(initial=capital,final_equity=daily[-1]['equity'],return_pct=100*(daily[-1]['equity']/capital-1),maximum_drawdown_pct=100*maxdd,shares=shares,original_shares=original,shares_deficit=original-shares,cash=cash,dividend_receivable=receivable,fees=fees,slippage=slip,sales=len(lots),closed_cycles=sum(l['status']=='CLOSED' for l in lots),open_cycles=sum(l['status']=='OPEN' for l in lots),realized_net_cash_surplus=sum(l['realized_net_cash_surplus'] or 0 for l in lots),unrealized_missing_shares_benefit=sum(l['unrealized_missing_shares_benefit'] for l in lots),missed_dividends=sum(l['missed_dividends'] for l in lots),unfilled_sell_signal=pending['date'] if pending else None))
