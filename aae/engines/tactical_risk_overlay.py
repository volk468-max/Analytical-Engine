"""Independent, advisory risk rules. Defaults are policy examples, not calibrated alpha."""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from math import isfinite
import os


def timestamp(value):
    try:
        result = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        return result.replace(tzinfo=timezone.utc) if result.tzinfo is None else result.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def number(value):
    try:
        result = float(value)
        return result if isfinite(result) else None
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True)
class TacticalRiskConfig:
    support_lookback: int = 120
    support_break_buffer_pct: float = 1.0
    stress_vix: float = 25.0
    severe_vix: float = 30.0
    trim_fraction: float = 0.25
    max_quote_age_hours: float = 96.0
    max_market_age_hours: float = 36.0

    @classmethod
    def from_env(cls):
        values = {}
        for name in cls.__dataclass_fields__:
            raw = os.environ.get("ALPHA_RISK_" + name.upper())
            if raw is not None:
                values[name] = int(raw) if name == "support_lookback" else float(raw)
        return cls(**values)

    def __post_init__(self):
        if not isinstance(self.support_lookback, int) or self.support_lookback < 1:
            raise ValueError('support_lookback must be a positive integer')
        for key, value in asdict(self).items():
            if number(value) is None or isinstance(value, bool) or value < 0:
                raise ValueError(f'{key} must be finite and nonnegative')
        if self.max_quote_age_hours <= 0 or self.max_market_age_hours <= 0:
            raise ValueError("Freshness limits must be positive")
        if not 0 <= self.support_break_buffer_pct < 100:
            raise ValueError('support_break_buffer_pct must be in [0, 100)')
        if not 0 < self.trim_fraction < 1:
            raise ValueError('trim_fraction must be in (0, 1)')
        if not 0 < self.stress_vix <= self.severe_vix:
            raise ValueError('VIX thresholds must be positive and ordered')


def historical_levels(history, price_as_of, lookback=120):
    """Strictly prior candles only; no current candle or future rows."""
    cutoff = timestamp(price_as_of)
    records = history.get('records', []) if isinstance(history, dict) else history
    if cutoff is None or not isinstance(records, list):
        return None, None
    rows = []
    for row in records:
        if not isinstance(row, dict):
            continue
        date = timestamp(row.get('trade_date') or row.get('date') or row.get('timestamp'))
        low, high = number(row.get('low')), number(row.get('high'))
        if date and date < cutoff and low is not None and high is not None and 0 < low <= high:
            rows.append((date, low, high))
    # Duplicate dates cannot increase the apparent history coverage.
    if len({row[0] for row in rows}) != len(rows):
        return None, None
    rows.sort()
    if len(rows) < lookback:
        return None, None
    rows = rows[-lookback:]
    return min(row[1] for row in rows), max(row[2] for row in rows)


class TacticalRiskOverlay:
    VERSION = 'Tactical-Risk-Overlay-v1'

    def __init__(self, config=None):
        self.config = config or TacticalRiskConfig.from_env()

    def evaluate(self, *, price, support, price_as_of, market, market_regime=None, now=None):
        now = now or datetime.now(timezone.utc)
        now = timestamp(now)
        if now is None:
            raise ValueError('Invalid evaluation time')
        config = self.config
        market = market or {}
        market_regime = market_regime or {}
        quote_time = timestamp(price_as_of)
        market_time = timestamp(market.get('trade_date') or market.get('snapshot_time'))
        reasons = []
        for label, observed, limit in (
            ('Quote', quote_time, config.max_quote_age_hours),
            ('Market', market_time, config.max_market_age_hours),
        ):
            if observed is None or not 0 <= (now - observed).total_seconds() / 3600 <= limit:
                reasons.append(f'{label} data are stale, missing or future-dated; refresh before trading.')
        price, support = number(price), number(support)
        vix = number(market.get('vix') if market.get('vix') is not None else market.get('VIX'))
        if price is None or price <= 0 or support is None or support <= 0:
            reasons.append('Valid price and historical support are required.')
        if vix is None or vix <= 0:
            reasons.append('A valid market volatility observation is required.')
        if reasons:
            return self._result('REVIEW', reasons, False)

        broken = price < support * (1 - config.support_break_buffer_pct / 100)
        stress = vix >= config.stress_vix
        severe = vix >= config.severe_vix
        # Regime is used only when its constituent observations passed freshness checks.
        regime_quality = market_regime.get('data_freshness') or {}
        regime_time = timestamp(regime_quality.get('evaluated_at'))
        regime_fresh = (regime_quality.get('status') == 'FRESH' and regime_time is not None
                        and 0 <= (now - regime_time).total_seconds() / 3600 <= config.max_market_age_hours)
        defensive = regime_fresh and market_regime.get('regime') in {'RISK_OFF', 'BEARISH_TREND', 'BEAR_MARKET'}
        if broken:
            reasons.append('Price broke historical support beyond the configured buffer.')
        if stress:
            reasons.append('Market volatility exceeds the configured stress threshold.')
        if defensive:
            reasons.append('Fresh market regime indicates defensive conditions.')
        action = 'TRIM' if severe or (broken and (stress or defensive)) else 'REVIEW' if broken or stress or defensive else 'HOLD'
        if not reasons:
            reasons.append('No tactical reduction condition is present in the observed data.')
        return self._result(action, reasons, True)

    def _result(self, action, reasons, actionable):
        return {
            'action': action, 'reasons': reasons, 'actionable': actionable,
            'position_multiplier': 1 - self.config.trim_fraction if action == 'TRIM' else 1.0,
            'config': asdict(self.config), 'engine_version': self.VERSION,
        }
