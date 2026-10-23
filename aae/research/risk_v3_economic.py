"""Offline share-based execution of frozen v3 signals; no signal generation/API calls."""
from dataclasses import dataclass, field
from math import isfinite, sqrt
from statistics import mean, stdev
from aae.backtest.simulator import ExecutionConfig, utc
from .risk_signal_v3 import LEVELS


@dataclass(frozen=True)
class EconomicConfig:
    recovery: str = 'HOLD3'
    tranche: float = .10
    critical_extra: bool = True
    min_shares_fraction: float = .50
    include_dividends: bool = True
    execution: ExecutionConfig = field(default_factory=lambda: ExecutionConfig(initial_cash=100000))

    def __post_init__(self):
        if self.recovery not in ('HOLD3', 'TREND3', 'TIME10'):
            raise ValueError('Unknown recovery policy')
        if not isfinite(self.tranche) or not 0 < self.tranche <= .5:
            raise ValueError('Invalid original-share tranche')
        if not 0 <= self.min_shares_fraction <= 1:
            raise ValueError('Invalid share floor')
        if type(self.critical_extra) is not bool or type(self.include_dividends) is not bool:
            raise ValueError('Boolean policy required')


def simulate(bars, signals, start, end, config=None, *, buy_hold=False, dividends=None):
    """One account. Bars use ONE split-adjusted unit basis; never reapply splits.

    Signals are externally frozen inputs, observed only at their publication time.
    For this daily-open model publication must precede the next session open;
    inconsistent/late input calendars are rejected rather than silently replayed.
    """
    cfg = config or EconomicConfig()
    bars = sorted(bars, key=lambda b: b.open_at)
    if not bars or len({b.symbol for b in bars}) != 1 or len({b.open_at for b in bars}) != len(bars):
        raise ValueError('One symbol, unique sessions required')
    if any(a.available_at >= b.open_at for a, b in zip(bars, bars[1:])):
        raise ValueError('Publication must precede next session open for daily execution')
    sample = [b for b in bars if start <= b.close_at.date().isoformat() <= end]
    if not sample:
        raise ValueError('Empty period')
    lookup = {}
    for s in signals:
        if s['symbol'] != bars[0].symbol:
            raise ValueError('Signal symbol mismatch')
        if s['date'] in lookup:
            raise ValueError('Duplicate signal session')
        lookup[s['date']] = s
    for b in sample:
        s = lookup.get(b.close_at.date().isoformat())
        if s and (utc(s['decision_at']) < b.available_at or
                  utc(s['decision_at']) < b.close_at):
            raise ValueError('Signal predates completed/published candle')
    dividends = dividends or {}
    fee = cfg.execution.commission_bps / 10000
    slip = cfg.execution.slippage_bps / 10000
    cash = cfg.execution.initial_cash
    receivable = shares = original = 0.0
    trades, daily, decisions, lots, matches, cancellations = [], [], [], [], [], []
    pending = None
    previous = None
    episode = 0
    reduced = critical_used = False
    low_streak = hold_streak = trend_streak = 0
    order_counter = 0

    def cancel(reason, at):
        nonlocal pending
        cancellations.append(dict(order_id=pending['order_id'], signal_date=pending['signal_date'],
                                  cancelled_at=at, reason=reason))
        pending = None

    def execute(bar, order, index):
        nonlocal cash, shares, original
        before = shares
        mid = bar.open
        fill = mid * (1 + slip if order['side'] == 'BUY' else 1 - slip)
        if order['side'] == 'BUY':
            wanted = order['quantity'] if original else float('inf')
            qty = min(wanted, cash / (fill * (1 + fee)))
            if original:
                qty = min(qty, max(0, original - shares))
        else:
            qty = min(order['quantity'], max(0, shares - original * cfg.min_shares_fraction))
        if qty <= 1e-10:
            return None
        commission = qty * fill * fee
        slippage = qty * abs(fill - mid)
        if order['side'] == 'BUY':
            cash -= qty * fill + commission
            shares += qty
        else:
            cash += qty * fill - commission
            shares -= qty
        if abs(cash) < 1e-8:
            cash = 0.0
        if original == 0:
            original = shares
        trade = dict(trade_id=len(trades) + 1, order_id=order['order_id'], symbol=bar.symbol,
            date=bar.open_at.date().isoformat(), executed_at=bar.open_at.isoformat(),
            signal_date=order['signal_date'], signal_at=order['signal_at'], signal_close=order.get('signal_close'),
            side=order['side'], reason=order['reason'], quantity=qty, requested_quantity=order['quantity'],
            mid=mid, fill=fill, commission=commission, slippage=slippage,
            cash=cash, dividend_receivable=receivable, total_cash=cash + receivable,
            shares=shares, original_shares=original, shares_fraction=shares/original,
            share_deficit=original-shares, bar_index=index)
        trades.append(trade)
        for decision in decisions:
            if decision['order_id']==order['order_id']:
                decision.update(status='FILLED' if qty>=order['quantity']-1e-8 else 'PARTIAL_AT_SHARE_FLOOR',
                                executed_at=trade['executed_at'],executed_quantity=qty)
        if order['side'] == 'SELL':
            remaining = qty
            for component in order['components']:
                units = min(component['quantity'], remaining)
                if units <= 1e-10:
                    continue
                lot = dict(lot_id=len(lots) + 1, signal_id=component['signal_id'],
                    reason=component['reason'], sale_date=trade['date'], sale_index=index,
                    sale_fill=fill, sale_mid=mid, sale_net=fill*(1-fee), sale_trade_id=trade['trade_id'],
                    signal_date=order['signal_date'], signal_close=order.get('signal_close'),
                    quantity=units, remaining=units, realized_contribution=0.0,
                    missed_dividends=0.0, missed_dividends_remaining=0.0,
                    sale_commission=commission*units/qty, sale_slippage=slippage*units/qty,
                    matches=[], dividend_events=[])
                lots.append(lot)
                remaining -= units
        elif before > 0:
            remaining = qty
            for lot in lots:
                units = min(lot['remaining'], remaining)
                if units <= 1e-10:
                    continue
                missed = lot['missed_dividends_remaining'] * units / lot['remaining']
                pnl = units * (lot['sale_net'] - fill*(1+fee)) - missed
                match = dict(lot_id=lot['lot_id'], sale_trade_id=lot['sale_trade_id'],
                    buy_trade_id=trade['trade_id'], sale_date=lot['sale_date'], buy_date=trade['date'],
                    sale_fill=lot['sale_fill'], buy_fill=fill, quantity=units,
                    price_difference=fill-lot['sale_fill'], buy_commission=commission*units/qty,
                    buy_slippage=slippage*units/qty, missed_dividends=missed,
                    net_contribution=pnl, missed_growth=max(0, units*(fill-lot['sale_fill'])),
                    absent_sessions=index-lot['sale_index'], buy_index=index,
                    cash_after_buy=cash, shares_after_buy=shares, share_deficit=original-shares)
                matches.append(match)
                lot['matches'].append(match)
                lot['remaining'] -= units
                lot['missed_dividends_remaining'] -= missed
                lot['realized_contribution'] += pnl
                remaining -= units
        return trade

    for i, bar in enumerate(sample):
        date = bar.close_at.date().isoformat()
        # Ex-date entitlement belongs to pre-open holders, before ex-date trades.
        entitlement = shares * dividends.get(date, 0) if cfg.include_dividends else 0
        receivable += entitlement
        for lot in lots:
            missed = lot['remaining'] * dividends.get(date, 0) if cfg.include_dividends else 0
            lot['missed_dividends'] += missed
            lot['missed_dividends_remaining'] += missed
            if missed:
                lot['dividend_events'].append((date, missed))
        if i == 0:
            execute(bar, dict(side='BUY', quantity=0, order_id=0, signal_date=None,
                             signal_at=None, reason='INITIAL'), i)
        elif pending and pending['due_index'] <= i:
            if utc(pending['signal_at']) >= bar.open_at:
                raise ValueError('Attempt to fill before signal availability')
            execute(bar, pending, i)
            pending = None
        # Closing NAV never uses a subsequent session price.
        daily.append(dict(symbol=bar.symbol, date=date, close=bar.close,
            equity=cash+receivable+shares*bar.close, cash=cash, dividend_receivable=receivable,
            total_cash=cash+receivable, shares=shares, original_shares=original,
            share_deficit=original-shares, shares_fraction=shares/original,
            stock_weight=shares*bar.close/(cash+receivable+shares*bar.close),
            dividend_entitlement=entitlement))
        if buy_hold:
            continue
        s = lookup.get(date)
        valid = bool(s and s.get('data_status') == 'OK' and s.get('risk_level') in LEVELS)
        level = s['risk_level'] if valid else None
        if s and i+1 < len(sample) and utc(s['decision_at']) >= sample[i+1].open_at:
            raise ValueError('Signal publication after next daily open unsupported')
        high = valid and LEVELS[level] >= 2
        if pending and pending['side'] == 'BUY' and (high or not valid):
            cancel('New high risk or unavailable data', s['decision_at'] if s else bar.available_at.isoformat())
        low_streak = low_streak + 1 if valid and not high else 0
        hold_streak = hold_streak + 1 if valid and level == 'HOLD' else 0
        indicators = s.get('indicators', {}) if s else {}
        trend = valid and not high and indicators.get('ma20') is not None and indicators.get('ma20_slope_5_pct') is not None and bar.close > indicators['ma20'] and indicators['ma20_slope_5_pct'] > 0
        trend_streak = trend_streak + 1 if trend else 0
        if low_streak >= 3:
            reduced = critical_used = False
        components = []
        entry = high and (previous not in ('REDUCE','CRITICAL'))
        if high:
            if not reduced:
                episode += 1
                components.append(('REDUCE', cfg.tranche*original))
                reduced = True
            if level == 'CRITICAL' and cfg.critical_extra and not critical_used:
                components.append(('CRITICAL', cfg.tranche*original))
                critical_used = True
        # Record every observed high-state transition, including exhausted permissions.
        event = high and (entry or level != previous or bool(components))
        decision = None
        if event:
            decision = dict(signal_id=len(decisions)+1, symbol=bar.symbol, date=date,
                decision_at=s['decision_at'], close=bar.close, level=level, episode=episode,
                initial_observation=i==0, new_high_entry=entry, requested_quantity=sum(x[1] for x in components),
                status='EPISODE_PERMISSION_SPENT', order_id=None, shares=shares, cash=cash)
            decisions.append(decision)
        if components:
            if pending:
                decision['status'] = 'PENDING_ORDER_CONFLICT'
            elif shares <= original*cfg.min_shares_fraction + 1e-10:
                decision['status'] = 'SHARE_FLOOR'
            else:
                order_counter += 1
                pending = dict(order_id=order_counter, side='SELL', quantity=sum(x[1] for x in components),
                    due_index=i+cfg.execution.delay_sessions, signal_date=date, signal_at=s['decision_at'],
                    signal_close=bar.close, reason='+'.join(x[0] for x in components),
                    components=[dict(reason=k, quantity=q, signal_id=decision['signal_id']) for k,q in components])
                decision.update(status='SCHEDULED', order_id=order_counter)
        recover = {'HOLD3':hold_streak>=3, 'TREND3':trend_streak>=3, 'TIME10':low_streak>=10}[cfg.recovery]
        if not pending and recover and shares < original-1e-9 and cash > 1e-8:
            order_counter += 1
            pending = dict(order_id=order_counter, side='BUY', quantity=min(original-shares,cfg.tranche*original),
                due_index=i+cfg.execution.delay_sessions, signal_date=date, signal_at=s['decision_at'],
                signal_close=bar.close, reason='RECOVER_'+cfg.recovery)
        previous = level
        if cash < -1e-7 or shares < original*cfg.min_shares_fraction-1e-7 or shares > original+1e-7:
            raise AssertionError('Cash/share bound violation')
    if pending:
        for d in decisions:
            if d['order_id'] == pending['order_id']:
                d['status'] = 'UNFILLED_AT_CUTOFF'
    return dict(symbol=bars[0].symbol, config=cfg, daily=daily, trades=trades, decisions=decisions,
                lots=lots, matches=matches, cancellations=cancellations, pending=pending,
                original_shares=original, bars=sample)


def performance(daily, initial, start_at, *, trades=()):
    values = [initial] + [r['equity'] for r in daily]
    returns = [b/a-1 for a,b in zip(values, values[1:])]
    peak = values[0]
    max_dd = 0
    for value in values:
        peak = max(peak,value)
        max_dd = min(max_dd,value/peak-1)
    from datetime import datetime
    days = (datetime.fromisoformat(daily[-1]['date'])-datetime.fromisoformat(start_at[:10])).days
    reduced = [r['shares_fraction'] < 1-1e-8 for r in daily]
    durations=[];run=0
    for absent in reduced:
        if absent:run+=1
        elif run:durations.append(run);run=0
    observed_duration=durations+[run] if run else durations
    result=dict(initial_equity=initial,final_equity=values[-1],return_pct=(values[-1]/initial-1)*100,
        cagr_pct=((values[-1]/initial)**(365.25/days)-1)*100 if days>=365 else None,
        max_drawdown_pct=max_dd*100,
        sharpe=mean(returns)/stdev(returns)*sqrt(252) if len(returns)>1 and stdev(returns)>0 else None,
        trades=len(trades), buys=sum(t['side']=='BUY' and t['reason']!='INITIAL' for t in trades),
        sells=sum(t['side']=='SELL' for t in trades), commissions=sum(t['commission'] for t in trades),
        slippage=sum(t['slippage'] for t in trades), trading_costs=sum(t['commission']+t['slippage'] for t in trades),
        reduced_time_pct=mean(reduced)*100, average_reduced_spell_sessions=mean(observed_duration) if observed_duration else 0,
        average_completed_reduced_spell_sessions=mean(durations) if durations else None,
        closed_reduced_spells=len(durations), open_reduced_spell_sessions=run,
        final_share_deficit=daily[-1]['share_deficit'], final_cash=daily[-1]['cash'],
        final_dividend_receivable=daily[-1]['dividend_receivable'],
        mean_shares_fraction=mean(r['shares_fraction'] for r in daily),
        minimum_shares_fraction=min(r['shares_fraction'] for r in daily))
    return result
