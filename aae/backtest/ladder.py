"""Quantity-based Core + Tactical Ladder, isolated from Alpha OS engines.

Close-time decisions, later-open fills; one pending order and at most one fill/session.
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from math import ceil, floor, isfinite, sqrt
from statistics import mean, stdev
from copy import deepcopy
from .simulator import Bar, utc


@dataclass(frozen=True)
class LadderConfig:
    sell_step: float = .02
    trade_fraction: float = .05
    min_fraction: float = .5
    buy_step: float = .02
    capital: float = 100000
    commission_bps: float = 5
    slippage_bps: float = 5
    delay_sessions: int = 1
    lot_size: float | None = None
    fill_fraction: float = 1
    partial_cash: bool = True

    def __post_init__(self):
        for name in ('sell_step','trade_fraction','min_fraction','buy_step','fill_fraction'):
            value=getattr(self,name)
            if not isfinite(value) or not 0<value<=(1 if name=='fill_fraction' else .999999):
                raise ValueError('Invalid '+name)
        if not isfinite(self.capital) or self.capital<=0:
            raise ValueError('Capital must be positive')
        for name in ('commission_bps','slippage_bps'):
            value=getattr(self,name)
            if not isfinite(value) or not 0<=value<10000:
                raise ValueError('Invalid '+name)
        if type(self.delay_sessions) is not int or self.delay_sessions<1:
            raise ValueError('Delay must be positive integer sessions')
        if self.lot_size is not None and (not isfinite(self.lot_size) or self.lot_size<=0):
            raise ValueError('Invalid lot size')
        if type(self.partial_cash) is not bool:
            raise ValueError('partial_cash must be boolean')


@dataclass(frozen=True)
class Split:
    effective_at: datetime
    available_at: datetime
    ratio: float
    def __post_init__(self):
        object.__setattr__(self,'effective_at',utc(self.effective_at))
        object.__setattr__(self,'available_at',utc(self.available_at))
        if not isfinite(self.ratio) or self.ratio<=0 or self.available_at>self.effective_at:
            raise ValueError('Split must have a positive ratio and be known by ex-date open')


@dataclass
class LadderState:
    cash: float
    shares: float
    base_shares: float
    anchor: float
    pending: dict | None = None
    last_close_at: datetime | None = None
    last_close: float | None = None
    last_available_at: datetime | None = None
    order_sequence: int = 0
    applied_splits: set = field(default_factory=set)


def rounded(quantity, lot):
    return max(0, floor((quantity+1e-10)/lot)*lot) if lot else max(0,quantity)


def simulate_ladder(bars, config=None, *, ladder=True, state=None, splits=()):
    cfg=config or LadderConfig()
    bars=sorted(bars,key=lambda b:b.open_at)
    if not bars or len({b.symbol for b in bars})!=1 or len({b.open_at for b in bars})!=len(bars):
        raise ValueError('Nonempty single-symbol unique sessions required')
    if any(a.close_at>=b.open_at or a.available_at>=b.available_at for a,b in zip(bars,bars[1:])):
        raise ValueError('Invalid session/publication ordering')
    if any(a.available_at>=b.open_at for a,b in zip(bars,bars[1:])):
        raise ValueError('Publication must precede the following session open; late feeds require an event-clock adapter')
    if len({s.effective_at for s in splits})!=len(splits):
        raise ValueError('Duplicate split events')
    opens={b.open_at for b in bars}
    if any(bars[0].open_at<=s.effective_at<=bars[-1].open_at and s.effective_at not in opens for s in splits):
        raise ValueError('Split event must align with its session open')
    if state is not None and (not all(isfinite(v) for v in (state.cash,state.shares,state.base_shares,state.anchor))
        or state.cash<0 or state.base_shares<=0 or state.anchor<=0
        or not state.base_shares*cfg.min_fraction-1e-8<=state.shares<=state.base_shares+1e-8):
        raise ValueError('Invalid inherited state')
    if state is not None and state.last_close_at and bars[0].open_at<=state.last_close_at:
        raise ValueError('Continuation cannot replay a processed session')
    if state is not None and state.last_available_at and bars[0].open_at<=state.last_available_at:
        raise ValueError('Continuation open precedes the previous data publication')
    state=deepcopy(state) if state else None
    fee,slip=cfg.commission_bps/10000,cfg.slippage_bps/10000
    trades=[]; events=[]; daily=[]
    def event(at,kind,**extra):
        events.append(dict(at=at.isoformat(),event=kind,cash=state.cash,shares=state.shares,
                           base_shares=state.base_shares,anchor=state.anchor,**extra))
    if state is None:
        price=bars[0].open*(1+slip)
        qty=rounded(cfg.capital/(price*(1+fee)),cfg.lot_size)
        if qty<=0:
            raise ValueError('Initial lot unaffordable')
        commission=qty*price*fee
        state=LadderState(max(0,cfg.capital-qty*price-commission),qty,qty,price)
        trades.append(dict(order_id=0,side='BUY',reason='initial',signal_at=None,
            executed_at=bars[0].open_at.isoformat(),units=qty,requested_units=qty,
            mid_price=bars[0].open,fill_price=price,commission=commission,
            slippage_dollars=qty*abs(price-bars[0].open),notional=qty*price,
            anchor_before=None,anchor_after=price,shares_after=qty,cash_after=state.cash,
            fill_status='FULL',base_shares=qty))
        event(bars[0].open_at,'INITIAL_BUY',order_id=0)
    for bar in bars:
        for action in sorted(splits,key=lambda a:a.effective_at):
            key=action.effective_at.isoformat()
            if action.effective_at==bar.open_at and key not in state.applied_splits:
                # Initial entry already buys post-split units at that day's nominal open.
                if not (state.last_close_at is None and len(trades)==1 and trades[0]['reason']=='initial'):
                    state.shares*=action.ratio; state.base_shares*=action.ratio; state.anchor/=action.ratio
                    if state.pending:
                        state.pending['units']*=action.ratio
                state.applied_splits.add(key)
                event(bar.open_at,'SPLIT',ratio=action.ratio)
        order=state.pending
        if order and bar.open_at>order['at']:
            order['wait']-=1
            if order['wait']==0:
                mid=bar.open
                side=order['side']
                fill=mid*(1+slip if side=='BUY' else 1-slip)
                capacity=max(0,state.base_shares-state.shares) if side=='BUY' else max(0,state.shares-state.base_shares*cfg.min_fraction)
                qty=rounded(min(order['units']*cfg.fill_fraction,capacity),cfg.lot_size)
                if side=='BUY':
                    affordable=rounded(state.cash/(fill*(1+fee)),cfg.lot_size)
                    qty=min(qty,affordable) if cfg.partial_cash else (qty if affordable+1e-10>=qty else 0)
                anchor_before=state.anchor
                if qty>1e-10:
                    commission=qty*fill*fee
                    if side=='BUY':
                        state.cash-=qty*fill+commission; state.shares+=qty
                    else:
                        state.cash+=qty*fill-commission; state.shares-=qty
                    state.cash=max(0,state.cash)
                    state.anchor=fill
                    status='FULL' if abs(qty-order['units'])<1e-9 else 'PARTIAL_REMAINDER_CANCELLED'
                    trades.append(dict(order_id=order['id'],side=side,reason='ladder',
                        signal_at=order['at'].isoformat(),executed_at=bar.open_at.isoformat(),
                        units=qty,requested_units=order['units'],mid_price=mid,fill_price=fill,
                        commission=commission,slippage_dollars=qty*abs(fill-mid),notional=qty*fill,
                        anchor_before=anchor_before,anchor_after=fill,shares_after=state.shares,
                        cash_after=state.cash,fill_status=status,base_shares=state.base_shares))
                    event(bar.open_at,'FILL',order_id=order['id'],side=side,units=qty,status=status)
                else:
                    event(bar.open_at,'REJECT_NO_AFFORDABLE_LOT',order_id=order['id'],side=side)
                # One-shot partial fill: never leave an incompatible residual order alive.
                state.pending=None
        at=bar.available_at
        if state.pending:
            event(at,'PENDING_NO_NEW_ORDER',order_id=state.pending['id'])
        elif ladder:
            side=None
            if bar.close<=state.anchor*(1-cfg.sell_step):
                if state.shares>state.base_shares*cfg.min_fraction+1e-10:
                    side='SELL'
                else:
                    event(at,'LOWER_BOUND_ANCHOR_FROZEN')
            elif bar.close>=state.anchor*(1+cfg.buy_step):
                if state.shares>=state.base_shares-1e-10:
                    event(at,'UPPER_BOUND_ANCHOR_FROZEN')
                elif state.cash<=1e-8:
                    event(at,'BUY_BLOCKED_NO_CASH_ANCHOR_FROZEN')
                else:
                    side='BUY'
            else:
                event(at,'HOLD')
            if side:
                capacity=(state.base_shares-state.shares) if side=='BUY' else (state.shares-state.base_shares*cfg.min_fraction)
                units=rounded(min(cfg.trade_fraction*state.base_shares,capacity),cfg.lot_size)
                if units>1e-10:
                    state.order_sequence+=1
                    state.pending=dict(id=state.order_sequence,side=side,units=units,at=at,wait=cfg.delay_sessions)
                    event(at,'SIGNAL',order_id=state.order_sequence,side=side,requested_units=units,
                          trigger_close=bar.close)
                else:
                    event(at,'LOT_ROUNDING_BLOCK_ANCHOR_FROZEN')
        else:
            event(at,'BUY_HOLD')
        nav=state.cash+state.shares*bar.close
        assert state.cash>=-1e-7 and state.base_shares*cfg.min_fraction-1e-7<=state.shares<=state.base_shares+1e-7
        daily.append(dict(date=bar.close_at.date().isoformat(),close_at=bar.close_at.isoformat(),
            decision_at=at.isoformat(),close=bar.close,equity=nav,cash=state.cash,shares=state.shares,
            base_shares=state.base_shares,core_shares=state.base_shares*cfg.min_fraction,
            tactical_shares=state.shares-state.base_shares*cfg.min_fraction,
            share_fraction=state.shares/state.base_shares,equity_weight=state.shares*bar.close/nav,
            cash_weight=state.cash/nav,anchor=state.anchor,
            pending_order=state.pending['id'] if state.pending else None))
        state.last_close_at=bar.close_at; state.last_close=bar.close; state.last_available_at=bar.available_at
    return dict(daily=daily,trades=trades,events=events,state=state,config=asdict(cfg))


def metrics(daily, trades, initial_value, start_at, *, benchmark_daily=None):
    if not daily:
        raise ValueError('No marks')
    peak=initial_value; max_dd=0; dd_length=0; max_dd_length=0; recovery=None
    returns=[]; previous=initial_value; path=[]; first_loss=None; recovery_after_loss=None
    for i,row in enumerate(daily):
        nav=row['equity']; returns.append(nav/previous-1); previous=nav
        if nav>=peak-1e-8:
            peak=max(peak,nav); dd_length=0
        else:
            dd_length+=1; max_dd_length=max(max_dd_length,dd_length)
        dd=nav/peak-1; max_dd=min(max_dd,dd); path.append(dd)
        if recovery is None and nav>=initial_value:
            recovery=row['date']
        if first_loss is None and nav<initial_value-1e-8:
            first_loss=i
        if first_loss is not None and recovery_after_loss is None and nav>=initial_value:
            recovery_after_loss=i
    elapsed=(utc(daily[-1]['close_at'])-utc(start_at)).total_seconds()/86400
    vol=stdev(returns)*sqrt(252) if len(returns)>1 else None
    downside=sqrt(mean(min(r,0)**2 for r in returns))*sqrt(252)
    sharpe=mean(returns)*252/vol if vol and vol>1e-15 else None
    sortino=mean(returns)*252/downside if downside>1e-15 else None
    end=daily[-1]['equity']
    result=dict(initial_equity=initial_value,final_equity=end,return_pct=(end/initial_value-1)*100,
        cagr_pct=((end/initial_value)**(365.25/elapsed)-1)*100 if elapsed>=365 else None,
        max_drawdown_pct=max_dd*100,max_drawdown_duration_sessions=max_dd_length,
        annualized_volatility_pct=vol*100 if vol is not None else None,sharpe_rf_zero=sharpe,sortino_rf_zero=sortino,
        buys=sum(t['side']=='BUY' for t in trades),sells=sum(t['side']=='SELL' for t in trades),
        commissions=sum(t['commission'] for t in trades),slippage_dollars=sum(t['slippage_dollars'] for t in trades),
        turnover_initial_capital=sum(t['notional'] for t in trades)/initial_value,
        average_share_fraction=mean(r['share_fraction'] for r in daily),minimum_share_fraction=min(r['share_fraction'] for r in daily),
        average_equity_weight=mean(r['equity_weight'] for r in daily),minimum_equity_weight=min(r['equity_weight'] for r in daily),
        maximum_cash_weight=max(r['cash_weight'] for r in daily),average_cash=mean(r['cash'] for r in daily),
        final_cash=daily[-1]['cash'],final_shares=daily[-1]['shares'],
        initial_capital_recovery_date=recovery,initial_capital_not_recovered=recovery is None,
        initial_capital_first_loss_date=daily[first_loss]['date'] if first_loss is not None else None,
        initial_capital_recovery_after_loss_date=daily[recovery_after_loss]['date'] if recovery_after_loss is not None else None,
        initial_capital_recovery_after_loss_sessions=recovery_after_loss-first_loss if recovery_after_loss is not None else None,
        initial_capital_loss_unrecovered=first_loss is not None and recovery_after_loss is None,
        sessions=len(daily),last_session=daily[-1]['date'])
    if benchmark_daily:
        bh_initial=benchmark_daily[0].get('comparison_initial',initial_value)
        bh_return=(benchmark_daily[-1]['equity']/bh_initial-1)*100
        result['relative_return_pp']=result['return_pct']-bh_return
        result['relative_final_dollars']=end-benchmark_daily[-1]['equity']
    return result


def recovery_costs(trades, terminal_price, terminal_base=None):
    """FIFO opportunity cost on sold units; diagnostic, not net profit attribution."""
    lots=[]; realized=0; losing=0; matched_sequences=0
    for trade in trades:
        scale=terminal_base/trade['base_shares'] if terminal_base is not None else 1
        units=trade['units']*scale
        commission_per_unit=trade.get('commission',0)/trade['units']
        net_price=(trade['fill_price']-commission_per_unit if trade['side']=='SELL' else trade['fill_price']+commission_per_unit)/scale
        if trade['side']=='SELL':
            lots.append([units,net_price,trade['order_id']])
        elif trade['reason']!='initial':
            remaining=units
            sequence_loss=0
            while lots and remaining>1e-10:
                qty,price,key=lots[0]; used=min(qty,remaining)
                difference=net_price-price
                realized+=used*max(0,difference)
                sequence_loss+=used*difference
                remaining-=used
                if used>=qty-1e-10:
                    lots.pop(0)
                else:
                    lots[0][0]-=used
            if units-remaining>1e-10:
                matched_sequences+=1
                losing+=sequence_loss>0
    unrealized=sum(qty*max(0,terminal_price-price) for qty,price,key in lots)
    return dict(missed_recovery_dollars=realized+unrealized,matched_repurchase_gap_dollars=realized,
                terminal_share_gap_mark_dollars=unrealized,matched_buy_sequences=matched_sequences,
                adverse_buy_sequences=losing,unreacquired_units=sum(qty for qty,price,key in lots))
