"""Event-time simulator. Inputs carry observation AND publication timestamps."""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from math import isfinite
from typing import Callable
from aae.engines.tactical_risk_overlay import TacticalRiskConfig, TacticalRiskOverlay
from aae.engines.decision_engine import DecisionEngine
from .legacy_decision_engine import DecisionEngine as LegacyDecisionEngine


def utc(value):
    result = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('Explicit timezone required')
    return result.astimezone(timezone.utc)


def positive(value):
    return isinstance(value, (int, float)) and isfinite(value) and value > 0


@dataclass(frozen=True)
class Bar:
    symbol: str
    open_at: datetime
    close_at: datetime
    available_at: datetime
    open: float
    high: float
    low: float
    close: float
    source: str
    verified: bool = True

    def __post_init__(self):
        for name in ('open_at', 'close_at', 'available_at'):
            object.__setattr__(self, name, utc(getattr(self, name)))
        if type(self.verified) is not bool:
            raise ValueError('verified must be a boolean')
        if not self.open_at < self.close_at <= self.available_at:
            raise ValueError('Bar must close before publication')
        if not all(positive(x) for x in (self.open, self.high, self.low, self.close)):
            raise ValueError('Prices must be finite and positive')
        if self.low > min(self.open, self.close) or self.high < max(self.open, self.close):
            raise ValueError('Inconsistent OHLC')
        if not self.source:
            raise ValueError('Source provenance required')

    def history(self):
        return dict(trade_date=self.close_at.isoformat(), low=self.low, high=self.high, close=self.close)


@dataclass(frozen=True)
class Observation:
    observed_at: datetime
    available_at: datetime
    value: dict
    source: str
    verified: bool = True

    def __post_init__(self):
        object.__setattr__(self, 'observed_at', utc(self.observed_at))
        object.__setattr__(self, 'available_at', utc(self.available_at))
        if type(self.verified) is not bool:
            raise ValueError('verified must be a boolean')
        if self.available_at < self.observed_at or not self.source:
            raise ValueError('Invalid observation provenance/times')


@dataclass(frozen=True)
class ExecutionConfig:
    initial_cash: float = 10000
    commission_bps: float = 5
    slippage_bps: float = 5
    delay_sessions: int = 1
    restore_hold_sessions: int = 3
    repeat_trim: str = 'once_per_episode'
    min_weight: float = .25
    false_signal_horizon: int = 5

    def __post_init__(self):
        if not positive(self.initial_cash):
            raise ValueError('Invalid initial capital')
        for value in (self.commission_bps, self.slippage_bps):
            if not isfinite(value) or not 0 <= value < 10000:
                raise ValueError('Invalid costs')
        for value in (self.delay_sessions, self.restore_hold_sessions, self.false_signal_horizon):
            if type(value) is not int or value < 1:
                raise ValueError('Session counts must be positive integers')
        if self.repeat_trim not in {'once_per_episode', 'compound'} or not 0 <= self.min_weight <= 1:
            raise ValueError('Invalid position policy')


def visible(observations, at):
    candidates = [o for o in observations if o.observed_at <= at and o.available_at <= at]
    return max(candidates, key=lambda o: (o.observed_at, o.available_at)) if candidates else None


class OverlayPolicy:
    name = 'risk_overlay_only'

    def __init__(self, config=None, markets=()):
        self.config = config or TacticalRiskConfig()
        self.markets = list(markets)

    def __call__(self, bar, history, at):
        # Bars already have validated UTC times, unique sessions and finite OHLC.
        prior = [b for b in history if b.close_at < bar.close_at][-self.config.support_lookback:]
        support = min(b.low for b in prior) if len(prior) == self.config.support_lookback else None
        market = visible(self.markets, at)
        values = dict(market.value, snapshot_time=market.observed_at.isoformat()) if market else {}
        return TacticalRiskOverlay(self.config).evaluate(
            price=bar.close, support=support, price_as_of=bar.close_at.isoformat(), market=values, now=at)


class ArchivedDecisionPolicy:
    """Replay exact v1/v2 only with atomic, verified point-in-time input archives."""
    def __init__(self, version, snapshots, config=None):
        if version not in {'alpha_v1', 'risk_v2'}:
            raise ValueError('Unknown version')
        self.name = version
        self.snapshots = list(snapshots)
        self.engine = LegacyDecisionEngine() if version == 'alpha_v1' else DecisionEngine(config)

    def __call__(self, bar, history, at):
        archived = visible(self.snapshots, at)
        if archived is None or not archived.verified:
            raise ValueError('Verified historical decision inputs missing')
        payload = archived.value
        snapshot = payload['snapshot']
        technical = snapshot['technical']
        if (utc(technical['price_as_of']) != bar.close_at
                or technical['current_price'] != bar.close or snapshot['symbol'] != bar.symbol):
            raise ValueError('Archive does not match decision candle')
        # Archive producer must attest point-in-time vintage for every payload field.
        if payload.get('point_in_time_attested') is not True:
            raise ValueError('Point-in-time input attestation missing')
        def reject_future_fields(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    if key in {'snapshot_time', 'created_at', 'trade_date', 'price_as_of',
                               'published_at', 'available_at', 'as_of', 'evaluated_at'} and item:
                        if utc(item) > at:
                            raise ValueError('Archive contains a future timestamp: ' + key)
                    elif isinstance(item, (dict, list)):
                        reject_future_fields(item)
            elif isinstance(value, list):
                for item in value:
                    reject_future_fields(item)
        reject_future_fields(payload)
        args = dict(snapshot=snapshot, history=[b.history() for b in history],
                    market_regime=payload.get('market_regime'), long_term_thesis=payload.get('long_term_thesis'))
        if self.name == 'risk_v2':
            args['now'] = at
        decision = self.engine.evaluate(**args)
        return dict(action=decision['action'], reasons=decision['reason'],
                    actionable=decision.get('tactical_risk', {}).get('actionable', True),
                    position_multiplier=decision['position_multiplier'])


class BuyAndHold:
    name = 'buy_hold'
    def __call__(self, bar, history, at):
        return dict(action='HOLD', reasons=['Buy and hold baseline.'], actionable=True, position_multiplier=1)


def simulate(bars, policy: Callable, start, end, execution=None, allow_assumed=False):
    """Buy at first eligible open, decide after publication, execute at later opens.

    Each symbol has an independent account; no universe aggregation or leverage.
    end is a timestamp, never an implicit end-of-day on an incomplete session.
    """
    cfg = execution or ExecutionConfig()
    start, end = utc(start), utc(end)
    if start >= end:
        raise ValueError('Invalid study interval')
    bars = sorted(bars, key=lambda b: b.open_at)
    if len({b.symbol for b in bars}) != 1 or len({b.open_at for b in bars}) != len(bars):
        raise ValueError('One symbol and unique sessions required')
    if any(a.close_at >= b.open_at or a.available_at >= b.available_at for a, b in zip(bars, bars[1:])):
        raise ValueError('Overlapping bars or non-increasing publication times')
    if not allow_assumed and any(not b.verified for b in bars):
        raise ValueError('Strict mode requires verified point-in-time bars')
    observations = getattr(policy, 'markets', [])
    if not allow_assumed and any(not o.verified for o in observations):
        raise ValueError('Strict mode requires verified market vintages')
    eligible = [b for b in bars if start <= b.open_at and b.available_at <= end]
    if not eligible:
        raise ValueError('No completed bars in study interval')
    cash, shares = cfg.initial_cash, 0.0
    pending = None
    trades, signals, equity = [], [], []
    episode, holds = False, 0
    lots, missed_recovery = [], 0.0
    fee, slip = cfg.commission_bps / 10000, cfg.slippage_bps / 10000

    def rebalance(bar, target, reason, signal_at):
        nonlocal cash, shares, missed_recovery
        mid = bar.open
        nav = cash + shares * mid
        delta = target * nav / mid - shares
        if abs(delta) < 1e-10:
            return
        before = shares * mid / nav
        fill = mid * (1 + slip if delta > 0 else 1 - slip)
        if delta > 0:
            units = min(delta, cash / (fill * (1 + fee)))
            cash -= units * fill * (1 + fee)
            shares += units
            remaining = units
            while lots and remaining > 1e-10:
                qty, sale_mid = lots[0]
                used = min(remaining, qty)
                missed_recovery += used * max(0, mid - sale_mid)
                remaining -= used
                if used >= qty - 1e-10:
                    lots.pop(0)
                else:
                    lots[0] = (qty - used, sale_mid)
        else:
            units = min(-delta, shares)
            cash += units * fill * (1 - fee)
            shares -= units
            lots.append((units, mid))
        nav_after = cash + shares * mid
        trades.append(dict(symbol=bar.symbol, executed_at=bar.open_at.isoformat(), signal_at=signal_at,
                           side='BUY' if delta > 0 else 'SELL', units=units, mid_price=mid, fill_price=fill,
                           commission=units * fill * fee, weight_before=before,
                           weight_after=shares * mid / nav_after, reason=reason))

    rebalance(eligible[0], 1, 'initial_entry', None)
    for index, bar in enumerate(eligible):
        if pending:
            # Signal time is strictly before execution open, including after-hours publications.
            if bar.open_at > pending['at']:
                pending['wait'] -= 1
                if pending['wait'] == 0:
                    rebalance(bar, pending['target'], pending['reason'], pending['at'].isoformat())
                    pending = None
        at = bar.available_at
        known = [b for b in bars if b.close_at <= at and b.available_at <= at]
        result = policy(bar, known, at)
        action = result['action']
        if action not in {'HOLD', 'REVIEW', 'TRIM', 'SELL', 'ADD'}:
            raise ValueError('Unsupported strategy action')
        nav = cash + shares * bar.close
        weight = shares * bar.close / nav
        target = None
        if pending and pending['reason'] == 'restore' and action != 'HOLD':
            pending = None
        if result.get('actionable', True):
            if action == 'TRIM' and (not episode or cfg.repeat_trim == 'compound') and pending is None:
                target = max(cfg.min_weight, weight * result['position_multiplier'])
                if target >= weight:
                    target = None
                episode, holds = True, 0
            elif action == 'SELL' and pending is None:
                target, episode, holds = 0, True, 0
            elif action == 'ADD' and pending is None:
                target = min(1, weight * result['position_multiplier'])
                holds = 0
            elif action == 'HOLD':
                holds += 1
                if holds >= cfg.restore_hold_sessions and pending is None and weight < 1 - 1e-8:
                    target = 1
                    episode = False
            else:
                holds = 0
        else:
            holds = 0
            # Unverified input cancels any queued discretionary trade, including restoration.
            pending = None
        if target is not None:
            pending = dict(at=at, wait=cfg.delay_sessions, target=target,
                           reason='restore' if target == 1 else action)
        signals.append(dict(symbol=bar.symbol, strategy=policy.name, decision_at=at.isoformat(),
                            observed_at=bar.close_at.isoformat(), action=action,
                            actionable=result.get('actionable', True), reasons='; '.join(result.get('reasons', [])),
                            weight=weight, queued_target=target))
        equity.append(dict(symbol=bar.symbol, strategy=policy.name, date=bar.close_at.isoformat(),
                           equity=nav, cash=cash, shares=shares, weight=weight))
    terminal = eligible[-1].close
    missed_recovery += sum(qty * max(0, terminal - mid) for qty, mid in lots)
    peak, drawdown = cfg.initial_cash, 0
    for row in equity:
        peak = max(peak, row['equity'])
        drawdown = min(drawdown, row['equity'] / peak - 1)
    false_signals, censored = 0, 0
    for trade in trades:
        if trade['side'] != 'SELL':
            continue
        idx = next(i for i, b in enumerate(eligible) if b.open_at.isoformat() == trade['executed_at'])
        horizon = idx + cfg.false_signal_horizon
        if horizon >= len(eligible):
            censored += 1
        elif eligible[horizon].close > trade['mid_price']:
            false_signals += 1
    metrics = dict(symbol=eligible[0].symbol, strategy=policy.name,
                   start=eligible[0].open_at.isoformat(), end=eligible[-1].close_at.isoformat(),
                   return_pct=(equity[-1]['equity'] / cfg.initial_cash - 1) * 100,
                   max_drawdown_pct=drawdown * 100, trades=len(trades), false_signals=false_signals,
                   censored_false_signals=censored, missed_recovery_dollars=missed_recovery,
                   pending_at_end=pending is not None,
                   validation='assumed_availability_price_replay' if allow_assumed else 'verified_input_replay')
    return dict(metrics=metrics, signals=signals, trades=trades, equity=equity, execution=asdict(cfg))
