"""Retrospective economic labels; deliberately never imported by trading policy."""
from statistics import mean


def next_trough(bars, sale_index):
    """First subsequent confirmed closing trough, else right-censored minimum."""
    for i in range(max(1,sale_index),len(bars)-1):
        if bars[i].close<=bars[i-1].close and bars[i].close<bars[i+1].close:
            return i,False,i+1
    return min(range(sale_index,len(bars)),key=lambda i:bars[i].close),True,None


def lot_contribution_at(lot, close, date):
    matches=[m for m in lot['matches'] if m['buy_date']<=date]
    remaining=lot['quantity']-sum(m['quantity'] for m in matches)
    # All missed dividends through this date, including those allocated to matches.
    missed=sum(value for d,value in lot['dividend_events'] if d<=date)
    return (sum(m['quantity']*(lot['sale_net']-m['buy_fill'])-m['buy_commission'] for m in matches)
            +remaining*(lot['sale_net']-close)-missed)


def signal_economics(result, false_labels=None):
    output=[]
    false_labels=false_labels or {}
    bars=result['bars'];last=result['daily'][-1]
    for lot in result['lots']:
        index,censored,confirmed=next_trough(bars,lot['sale_index'])
        trough=bars[index]
        date=trough.close_at.date().isoformat()
        matched=lot['matches'];completed=lot['remaining']<=1e-8
        end_mark=lot['remaining']*(lot['sale_net']-last['close'])-lot['missed_dividends_remaining']
        pnl=lot['realized_contribution']+end_mark
        restored=sum(m['quantity'] for m in matched)
        avg_buy=sum(m['quantity']*m['buy_fill'] for m in matched)/restored if restored else None
        raw_drop=max(0,lot['sale_fill']-trough.close)
        full_loss=max(0,lot['sale_mid']-trough.close)*result['original_shares']
        actual=lot_contribution_at(lot,trough.close,date)
        label=false_labels.get((result['symbol'],lot['signal_date'])) or {}
        row=dict(symbol=result['symbol'],signal_id=lot['signal_id'],lot_id=lot['lot_id'],reason=lot['reason'],
            signal_date=lot['signal_date'],signal_close=lot['signal_close'],sale_date=lot['sale_date'],
            sale_fill=lot['sale_fill'],sale_mid=lot['sale_mid'],sold_quantity=lot['quantity'],
            sold_original_fraction=lot['quantity']/result['original_shares'],
            next_local_min_date=date,next_local_min_close=trough.close,
            trough_confirmed_date=bars[confirmed].close_at.date().isoformat() if confirmed is not None else None,
            trough_censored=censored,additional_decline_after_fill_pct=raw_drop/lot['sale_fill']*100,
            maximum_avoidable_decline_usd=raw_drop*lot['quantity'],
            actual_contribution_at_trough_usd=actual,
            original_position_decline_to_trough_usd=full_loss,
            avoided_fraction_of_original_decline_pct=max(0,actual)/full_loss*100 if full_loss else None,
            first_buy_date=matched[0]['buy_date'] if matched else None,
            full_lot_recovery_date=matched[-1]['buy_date'] if completed and matched else None,
            average_buy_fill=avg_buy,restored_quantity=restored,unrestored_quantity=lot['remaining'],
            price_difference=(avg_buy-lot['sale_fill']) if avg_buy is not None else None,
            sale_commission=lot['sale_commission'],sale_slippage=lot['sale_slippage'],
            buy_commission=sum(m['buy_commission'] for m in matched),
            buy_slippage=sum(m['buy_slippage'] for m in matched),
            missed_growth=sum(m['missed_growth'] for m in matched)+max(0,lot['remaining']*(last['close']-lot['sale_fill'])),
            missed_dividends=lot['missed_dividends'],
            realized_net_contribution=lot['realized_contribution'],unrealized_net_contribution=end_mark,
            total_net_contribution=pnl,cycle_completed=completed,
            profitable_completed=lot['realized_contribution']>0 if completed else None,
            final_cash=last['cash'],final_share_deficit=last['share_deficit'],
            false_reduce_followed_by_growth=label.get('false_reduce_followed_by_growth'),
            forward_5_pct=label.get('forward_5_pct'),forward_10_pct=label.get('forward_10_pct'),forward_20_pct=label.get('forward_20_pct'),
            average_absence_sessions=sum(m['quantity']*m['absent_sessions'] for m in matched)/restored if restored else None)
        output.append(row)
    # An entry may be blocked or queued beyond cutoff: do not invent its sale.
    lot_signals={r['signal_id'] for r in output}
    for d in result['decisions']:
        if d['signal_id'] not in lot_signals:
            output.append(dict(symbol=result['symbol'],signal_id=d['signal_id'],signal_date=d['date'],
                signal_close=d['close'],reason=d['level'],execution_status=d['status'],
                sold_quantity=0,sale_date=None,cycle_completed=False,
                false_reduce_followed_by_growth=(false_labels.get((result['symbol'],d['date'])) or {}).get('false_reduce_followed_by_growth')))
    return output


def economic_metrics(result, baseline):
    rows=[r for r in signal_economics(result) if r.get('sale_date')]
    closed=[r for r in rows if r['cycle_completed']]
    delta=result['daily'][-1]['equity']-baseline['daily'][-1]['equity']
    decomposition=sum(r['total_net_contribution'] for r in rows)
    if abs(delta-decomposition)>1e-5:
        raise AssertionError(f'Economic attribution failed: {delta} != {decomposition}')
    actual_protection=[r['actual_contribution_at_trough_usd'] for r in rows if not r['trough_censored']]
    # A direct CRITICAL has two component lots, but is one first-REDUCE decision.
    grouped={}
    for row in rows:grouped.setdefault(row['signal_id'],[]).append(row)
    first_reduce_groups=[group for group in grouped.values() if any(r['reason']=='REDUCE' for r in group)]
    completed_signals=[group for group in first_reduce_groups if all(r['cycle_completed'] for r in group)]
    positive_signals=sum(sum(r['realized_net_contribution'] for r in group)>0 for group in completed_signals)

    return dict(equity_difference_vs_buy_hold=delta,attributed_difference=decomposition,
        completed_reduce_signals=len(completed_signals),
        profitable_completed_reduce_signal_pct=positive_signals/len(completed_signals)*100 if completed_signals else None,
        completed_lots=len(closed),open_lots=len(rows)-len(closed),
        profitable_completed_lot_pct=mean(r['profitable_completed'] for r in closed)*100 if closed else None,
        net_realized_contribution=sum(r['realized_net_contribution'] for r in rows),
        net_open_contribution=sum(r['unrealized_net_contribution'] for r in rows),
        actual_trough_protection_sum=sum(actual_protection),
        positive_trough_protection_lot_pct=mean(p>0 for p in actual_protection)*100 if actual_protection else None,
        missed_growth=sum(r['missed_growth'] for r in rows),
        missed_dividends=sum(r['missed_dividends'] for r in rows),
        pending_order_conflicts=sum(d['status']=='PENDING_ORDER_CONFLICT' for d in result['decisions']),
        floor_blocked_entries=sum(d['status']=='SHARE_FLOOR' for d in result['decisions']),
        unfilled_cutoff_signals=sum(d['status']=='UNFILLED_AT_CUTOFF' for d in result['decisions']),
        cancelled_buys=len(result['cancellations']),
        signals=len(result['decisions']), high_risk_entries=sum(d['new_high_entry'] for d in result['decisions']),
        executed_reduction_lots=len(rows),
        average_matched_absence_sessions=(sum(m['quantity']*m['absent_sessions'] for m in result['matches'])/
            sum(m['quantity'] for m in result['matches'])) if result['matches'] else None)
