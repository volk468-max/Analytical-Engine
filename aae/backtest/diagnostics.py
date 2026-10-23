"""Offline diagnostic features and retrospective labels; no strategy changes."""
import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from math import isfinite
from .cli import load_bars, write_csv
from .simulator import Observation, OverlayPolicy, BuyAndHold, TacticalRiskConfig, simulate, utc, visible
from aae.engines.technical_analysis import TechnicalAnalysisEngine

SYMBOLS = ('AMD', 'NVDA', 'MU')
START = '2026-09-01'
END = '2026-10-22'


def change(current, previous):
    return (current / previous - 1) * 100


def features(bars, markets, benchmark=()):
    """Each row uses only closes/publications visible at its decision time."""
    bars = sorted(bars, key=lambda b: b.open_at)
    if len({b.open_at for b in bars}) != len(bars):
        raise ValueError('Duplicate stock sessions')
    if len({b.open_at.date() for b in benchmark}) != len(benchmark):
        raise ValueError('Duplicate benchmark sessions')
    policy = OverlayPolicy(TacticalRiskConfig(), markets)
    rows = []
    for bar in bars:
        at = bar.available_at
        history = [b for b in bars if b.available_at <= at and b.close_at <= at]
        # Restrict to this observation even if a malformed pack publishes out of order.
        history = [b for b in history if b.close_at <= bar.close_at]
        closes = [b.close for b in history]
        prior = closes[:-1]
        if not closes or history[-1] != bar:
            raise ValueError('Current candle is not visible')
        stock_date = bar.close_at.date()
        known_qqq = {b.close_at.date(): b for b in benchmark if b.available_at <= at and b.close_at <= at}
        market = visible(markets, at)
        vix = market.value.get('vix') if market else None
        known_vix = [m for m in markets if m.observed_at <= at and m.available_at <= at]
        # Latest vintage per observation time; revisions are gated by publication.
        vintages = {}
        for m in sorted(known_vix, key=lambda m: m.available_at):
            vintages[m.observed_at] = m
        vix_history = [vintages[t] for t in sorted(vintages)]
        config = policy.config
        result = policy(bar, history, at)
        support_rows = history[:-1][-config.support_lookback:]
        support = min(b.low for b in support_rows) if len(support_rows) == config.support_lookback else None
        ma = {period: mean(closes[-period:]) if len(closes) >= period else None for period in (20, 50, 200)}
        previous_ma = {period: mean(prior[-period:]) if len(prior) >= period else None for period in (20, 50)}
        market_age = (at - market.observed_at).total_seconds()/3600 if market else None
        quote_age = (at - bar.close_at).total_seconds()/3600
        valid_price_support = support is not None and support > 0 and bar.close > 0
        valid_vix = isinstance(vix, (int, float)) and isfinite(vix) and vix > 0
        quote_fresh = 0 <= quote_age <= config.max_quote_age_hours
        market_fresh = market_age is not None and 0 <= market_age <= config.max_market_age_hours
        inputs_valid = valid_price_support and valid_vix and quote_fresh and market_fresh
        broken = bar.close < support * (1 - config.support_break_buffer_pct/100) if support else None
        stress = vix >= config.stress_vix if valid_vix else None
        severe = vix >= config.severe_vix if valid_vix else None
        blockers = []
        if not inputs_valid:
            blockers.append('input_validation_failed')
        if not severe:
            blockers.append('severe_VIX_branch_not_met')
        if not broken:
            blockers.append('support_break_branch_not_met')
        if not stress:
            blockers.append('stress_confirmation_not_met')
        blockers.append('defensive_regime_unavailable_not_assumed')
        row = dict(symbol=bar.symbol, date=stock_date.isoformat(), decision_at=at.isoformat(),
            observed_at=bar.close_at.isoformat(), close=bar.close,
            day_change_pct=change(bar.close, prior[-1]) if prior else None,
            ma20=ma[20], ma50=ma[50], ma200=ma[200],
            rsi14=TechnicalAnalysisEngine._rsi(closes, 14) if len(closes) > 14 else None,
            vix=vix, vix_observed_at=market.observed_at.isoformat() if market else None,
            vix_available_at=market.available_at.isoformat() if market else None,
            support=support, distance_to_support_pct=change(bar.close, support) if support else None,
            support_break_price=support*(1-config.support_break_buffer_pct/100) if support else None,
            market_regime='UNAVAILABLE', market_breadth='UNAVAILABLE',
            action=result['action'], actionable=result['actionable'], reasons='; '.join(result['reasons']),
            price_support_valid=valid_price_support, vix_valid=valid_vix,
            quote_age_hours=quote_age, market_age_hours=market_age,
            quote_fresh=quote_fresh, market_fresh=market_fresh,
            inputs_valid=inputs_valid, risk_conditions_evaluated=inputs_valid,
            support_broken=broken, market_stress=stress, severe_market_stress=severe,
            regime_fresh=False, defensive_regime=False,
            support_and_stress=bool(broken and stress), support_and_defensive=False,
            trim_formula=bool(severe or (broken and stress)),
            trim_blockers='; '.join(blockers) if result['action'] != 'TRIM' else '',
            observed_history_rows=len(history), history_latest_available_at=history[-1].available_at.isoformat(),
            stock_source=bar.source, publication_verified=bar.verified)
        for period in (20, 60, 120):
            peak = max(prior[-period:]) if len(prior) >= period else None
            row[f'prior_peak_{period}'] = peak
            row[f'drawdown_{period}_pct'] = min(0, change(bar.close, peak)) if peak else None
        for period in (5, 10, 20):
            row[f'return_{period}_pct'] = change(bar.close, closes[-period-1]) if len(closes) > period else None
        previous_5 = change(closes[-6], closes[-11]) if len(closes) > 10 else None
        row['fall_acceleration_5_pp'] = row['return_5_pct']-previous_5 if previous_5 is not None else None
        for period in (20, 50):
            row[f'below_ma{period}'] = bar.close < ma[period] if ma[period] is not None else None
            row[f'cross_below_ma{period}'] = (prior[-1] >= previous_ma[period] and bar.close < ma[period]) if previous_ma[period] is not None else None
        qqq = known_qqq.get(stock_date)
        old_qqq = known_qqq.get(history[-21].close_at.date()) if len(history) >= 21 else None
        qqq_return = change(qqq.close, old_qqq.close) if qqq and old_qqq else None
        row.update(qqq_close=qqq.close if qqq else None,
                   qqq_observed_at=qqq.close_at.isoformat() if qqq else None,
                   qqq_available_at=qqq.available_at.isoformat() if qqq else None,
                   relative_return_20_pp=row['return_20_pct']-qqq_return if qqq_return is not None else None,
                   vix_change_5= vix_history[-1].value['vix']-vix_history[-6].value['vix'] if len(vix_history)>5 else None)
        row['technical_deterioration'] = bool((row['below_ma20'] and row['return_5_pct'] is not None and row['return_5_pct'] < 0) or row['below_ma50'])
        rows.append(row)
    return rows


def drawdown_events(rows, start=START, end=END, reference_window=120):
    """Peak-to-recovery excursions seeded by the highest prior 120 closes.

    One row per episode/threshold; no double counting repeated threshold crossings.
    Episode trough/outcome are retrospective labels, never fed into features/policy.
    """
    rows = sorted([r for r in rows if r['date'] <= end], key=lambda r:r['date'])
    study = [i for i,r in enumerate(rows) if r['date'] >= start]
    if not study:
        return []
    first = study[0]
    warmup_start = max(0, first-reference_window)
    seed = max(range(warmup_start, first+1), key=lambda i: rows[i]['close'])
    episodes = []
    peak = seed
    for i in range(seed+1, len(rows)):
        if rows[i]['close'] >= rows[peak]['close']:
            if i > peak+1:
                episodes.append((peak, i, True))
            peak=i
    if peak < len(rows)-1:
        episodes.append((peak, len(rows)-1, False))
    output = []
    for episode_id, (p, last, recovered) in enumerate(episodes, 1):
        sample = rows[p+1:last+1]
        if not sample or sample[-1]['date'] < start:
            continue
        peak_price = rows[p]['close']
        trough = min(sample, key=lambda r:r['close'])
        for threshold in (10,15,20):
            crossings = [r for r in sample if r['close'] <= peak_price*(1-threshold/100)]
            if not crossings:
                continue
            crossing = crossings[0]
            # An already-underwater episode is retained and explicitly marked left-censored.
            first_review = next((r for r in sample if r['action']=='REVIEW'), None)
            first_trim = next((r for r in sample if r['action']=='TRIM'), None)
            deterioration = next((r for r in sample if r['technical_deterioration']), None)
            observable = [r for r in sample if start <= r['date'] <= end]
            counts = Counter(r['trim_blockers'] for r in observable if r['action']!='TRIM')
            output.append(dict(symbol=rows[p]['symbol'], episode_id=episode_id, threshold_pct=threshold,
                peak_date=rows[p]['date'], peak_close=peak_price, decline_start=sample[0]['date'],
                first_technical_deterioration=deterioration['date'] if deterioration else None,
                first_threshold_date=crossing['date'], threshold_predates_window=crossing['date']<start,
                first_review=first_review['date'] if first_review else None,
                first_trim=first_trim['date'] if first_trim else None, trim_occurred=first_trim is not None,
                end_date=rows[last]['date'], recovered_to_peak=recovered,
                trough_date=trough['date'], max_drawdown_pct=change(trough['close'],peak_price),
                crossing_action=crossing['action'], crossing_close=crossing['close'],
                crossing_support=crossing['support'], crossing_support_broken=crossing['support_broken'],
                crossing_vix=crossing['vix'], crossing_market_stress=crossing['market_stress'],
                crossing_severe_stress=crossing['severe_market_stress'],
                crossing_information_cutoff=crossing['decision_at'],
                crossing_quote_observed_at=crossing['observed_at'],
                crossing_vix_observed_at=crossing['vix_observed_at'],
                crossing_vix_available_at=crossing['vix_available_at'],
                crossing_information_json=json.dumps({key:crossing[key] for key in (
                    'ma20','ma50','ma200','rsi14','distance_to_support_pct','relative_return_20_pp',
                    'inputs_valid','market_regime','market_breadth','quote_age_hours','market_age_hours')},sort_keys=True),
                crossing_blockers=crossing['trim_blockers'],
                blocker_day_counts=json.dumps(counts,sort_keys=True),
                interpretation='Signal absence; decision inefficiency is not established'))
    return output


def fifo_recovery_costs(trades, terminal_price):
    """Exactly reconcile the simulator's matched/terminal sold-unit diagnostic."""
    lots=[]
    costs={}
    for index, trade in enumerate(trades):
        if trade['side']=='SELL':
            costs[index]=dict(matched_repurchase_cost_dollars=0.0, terminal_unreacquired_units=trade['units'])
            lots.append([index, trade['units'], trade['mid_price']])
        else:
            remaining=trade['units']
            while lots and remaining>1e-10:
                key,qty,mid=lots[0]
                used=min(remaining,qty)
                costs[key]['matched_repurchase_cost_dollars']+=used*max(0,trade['mid_price']-mid)
                costs[key]['terminal_unreacquired_units']-=used
                remaining-=used
                if used>=qty-1e-10:
                    lots.pop(0)
                else:
                    lots[0][1]-=used
    for index,cost in costs.items():
        cost['terminal_unreacquired_units']=max(0,cost['terminal_unreacquired_units'])
        cost['terminal_mark_cost_dollars']=cost['terminal_unreacquired_units']*max(0,terminal_price-trades[index]['mid_price'])
        cost['missed_recovery_fifo_dollars']=cost['matched_repurchase_cost_dollars']+cost['terminal_mark_cost_dollars']
    return costs


def recovery_analysis(result, rows):
    """Use actual simulator executions; all trough metrics are ex-post diagnostics."""
    by_signal = {r['decision_at']:r for r in rows}
    output=[]
    trades=result['trades']
    terminal=next(r['close'] for r in rows if r['observed_at']==result['metrics']['end'])
    fifo=fifo_recovery_costs(trades,terminal)
    shares=0
    for i, sale in enumerate(trades):
        before=shares
        shares += sale['units'] if sale['side']=='BUY' else -sale['units']
        if sale['side']!='SELL':
            continue
        buy = next((t for t in trades[i+1:] if t['side']=='BUY' and t['reason']=='restore'),None)
        end_at=utc(buy['executed_at']) if buy else utc(result['metrics']['end'])
        holding=[r for r in rows if utc(sale['executed_at']) <= utc(r['observed_at']) < end_at]
        trough_price=min([sale['mid_price']]+[r['close'] for r in holding])
        trough=next((r['date'] for r in holding if r['close']==trough_price),sale['executed_at'][:10])
        last=by_signal.get(buy['signal_at']) if buy else None
        trigger=by_signal[sale['signal_at']]
        exit_mid=buy['mid_price'] if buy else next(r['close'] for r in rows if r['observed_at']==result['metrics']['end'])
        holds=[r for r in holding if r['action']=='HOLD' and r['actionable']]
        hold_dates=[r['date'] for r in rows if last and r['decision_at']<=last['decision_at']][-3:] if last else []
        output.append(dict(**fifo[i], terminal_price=terminal,
            restoration_hold_dates='; '.join(hold_dates), symbol=sale['symbol'], trim_signal_date=trigger['date'], trim_decision_at=sale['signal_at'],
            sale_at=sale['executed_at'], sale_mid=sale['mid_price'], sold_units=sale['units'],
            weight_before=sale['weight_before'], weight_after=sale['weight_after'],
            trim_vix=trigger['vix'], trim_support_broken=trigger['support_broken'], trim_reason=trigger['reasons'],
            first_actionable_hold=holds[0]['date'] if holds else None,
            restoration_signal_date=last['date'] if last else None,
            restored_at=buy['executed_at'] if buy else None, restored=buy is not None,
            restoration_mid=buy['mid_price'] if buy else None,
            sessions_reduced=len(holding), post_sale_trough_date=trough, post_sale_trough_close_or_sale_open=trough_price,
            rebound_before_restore_pct=change(exit_mid,trough_price),
            price_rise_sale_to_restore_pct=change(exit_mid,sale['mid_price']),
            missed_recovery_vs_sale_dollars=sale['units']*max(0,exit_mid-sale['mid_price']),
            sold_units_rebound_dollars=sale['units']*max(0,exit_mid-trough_price),
            reduced_share_fraction_pct=sale['units']/before*100,
            reacquired_units=buy['units'] if buy else None,
            restored_below_ma20=last['below_ma20'] if last else None,
            restored_below_ma50=last['below_ma50'] if last else None,
            restoration_vix=last['vix'] if last else None,
            price_recovery_confirmed_by_rule=False,
            interpretation='HOLD means no overlay reduction condition; not a trend recovery confirmation'))
    return output


FLAGS = {
    'fall_accelerating_5': lambda r: None if r['fall_acceleration_5_pp'] is None else r['fall_acceleration_5_pp']<0 and r['return_5_pct']<0,
    'local_drawdown_10': lambda r:None if r['drawdown_20_pct'] is None else r['drawdown_20_pct']<=-10+1e-10,
    'below_ma20':lambda r:r['below_ma20'], 'below_ma50':lambda r:r['below_ma50'],
    'cross_below_ma20':lambda r:r['cross_below_ma20'], 'cross_below_ma50':lambda r:r['cross_below_ma50'],
    'relative_weak_qqq20':lambda r:None if r['relative_return_20_pp'] is None else r['relative_return_20_pp']<0,
    'vix_rising5':lambda r:None if r['vix_change_5'] is None else r['vix_change_5']>0,
}


def indicator_evaluation(rows):
    """Forward outcomes live only in this separate retrospective evaluation table."""
    output=[]
    for period,start,end in (('pre_window','2024-01-01','2026-08-31'),('requested',START,END)):
        sample=[r for r in rows if start<=r['date']<=end]
        for name,flag in FLAGS.items():
            for active in (True,False):
                selected=[i for i,r in enumerate(sample) if flag(r) is not None and bool(flag(r))==active]
                complete=[i for i in selected if i+20<len(sample)]
                drawdowns=[min(change(sample[j]['close'],sample[i]['close']) for j in range(i+1,i+21)) for i in complete]
                output.append(dict(symbol=rows[0]['symbol'], period=period, indicator=name, active=active,
                    observations=len(selected), missing_observations=sum(flag(r) is None for r in sample), complete_horizons=len(complete), censored=len(selected)-len(complete),
                    forward_20_loss_10_count=sum(dd<=-10+1e-10 for dd in drawdowns),
                    forward_20_loss_10_rate_pct=mean(dd<=-10+1e-10 for dd in drawdowns)*100 if drawdowns else None,
                    mean_forward_20_min_return_pct=mean(drawdowns) if drawdowns else None,
                    interpretation='Overlapping retrospective associations, not independent predictive trials'))
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('reports/risk-diagnostics'))
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    inputs=[Path('data/backtest/bars.csv'),Path('data/backtest/markets.json'),Path('data/risk-diagnostics/qqq.csv')]
    for folder in ('data/backtest','data/risk-diagnostics'):
        manifest=json.loads((Path(folder)/'manifest.json').read_text())
        for name,digest in manifest['artifact_sha256'].items():
            if hashlib.sha256((Path(folder)/name).read_bytes()).hexdigest()!=digest:
                raise ValueError('Input checksum mismatch: '+name)
    bars=load_bars(inputs[0])
    markets=[Observation(**item) for item in json.loads(inputs[1].read_text())]
    benchmark=load_bars(inputs[2])
    daily,events,recoveries,evaluation=[],[],[],[]
    extended={}
    for symbol in SYMBOLS:
        selected=[b for b in bars if b.symbol==symbol]
        rows=features(selected,markets,benchmark)
        daily.extend(r for r in rows if START<=r['date']<=END)
        distinct={}
        for reference_window in (20,60,120):
            for event in drawdown_events(rows,reference_window=reference_window):
                key=(event['peak_date'],event['threshold_pct'])
                if key in distinct:
                    distinct[key]['reference_windows']+='; '+str(reference_window)
                else:
                    event['reference_windows']=str(reference_window)
                    event['episode_id']=symbol+':'+event['peak_date']
                    distinct[key]=event
        events.extend(sorted(distinct.values(),key=lambda r:(r['peak_date'],r['threshold_pct'])))
        result=simulate(selected,OverlayPolicy(TacticalRiskConfig(),markets),
                        '2024-01-01T00:00:00+00:00','2026-10-23T23:59:59+00:00',allow_assumed=True)
        extended[symbol]=result
        extended[symbol]['baseline_metrics']=simulate(selected,BuyAndHold(),
            '2024-01-01T00:00:00+00:00','2026-10-23T23:59:59+00:00',allow_assumed=True)['metrics']
        recovered=recovery_analysis(result,rows)
        if abs(sum(r['missed_recovery_fifo_dollars'] for r in recovered)-result['metrics']['missed_recovery_dollars'])>1e-6:
            raise ValueError('Recovery diagnostics do not reconcile simulator metric')
        recoveries.extend(recovered)
        evaluation.extend(indicator_evaluation(rows))
    for name,rows in (('daily-signals.csv',daily),('drawdown-events.csv',events),
                      ('recovery-analysis.csv',recoveries),('indicator-evaluation.csv',evaluation)):
        write_csv(args.output/name,rows)
    lines=['# Risk signal diagnostics: AMD, NVDA, MU','',
        '## Scope and causal limits','',
        'Daily decisions: 1 September–22 October 2026. Extended recovery study: 2024–22 October 2026. All calculations gate observations by publication time; no future candles enter features or Overlay decisions. The underlying provider-price vintages and inferred availability are still NOT verified point-in-time data. This is the limited price/VIX overlay replay from PR #2, not a reconstructed full Alpha OS decision system.', '',
        'Risk Engine v2, thresholds and execution/restoration policy are unchanged. Diagnostics call the existing Overlay. Market regime and broad-market breadth are UNAVAILABLE: neither trustworthy constituent histories nor archived regime inputs exist. QQQ is a relative-price benchmark, not fabricated breadth or a reconstructed regime.', '',
        '## Why TRIM did not occur','',
        'When input validity and freshness checks pass under the replay assumptions, the unchanged formula is `VIX >= 30 OR (price < prior_120_bar_low * 0.99 AND (VIX >= 25 OR fresh_defensive_regime))`. A falling stock, a 10–20% decline from a recent peak, MA breakdown, weak RSI or relative weakness is not by itself a TRIM input. An unavailable defensive regime is not a bullish observation; the replay simply cannot exercise that branch. For these observed rows support was not broken, so a defensive regime alone could add REVIEW but could not activate the conjunctive TRIM branch. Full Alpha OS decisions could still differ through other Decision Engine inputs that are unavailable historically.', '',
        '| Symbol | Sessions | HOLD / REVIEW / TRIM | Max VIX | Min (close/support - 1) % | Worst DD20 / DD60 / DD120 % |',
        '|---|---|---|---|---|---|']
    for symbol in SYMBOLS:
        rows=[r for r in daily if r['symbol']==symbol]
        counts=Counter(r['action'] for r in rows)
        lines.append(f"| {symbol} | {len(rows)} | {counts['HOLD']} / {counts['REVIEW']} / {counts['TRIM']} | {max(r['vix'] for r in rows):.2f} | {min(r['distance_to_support_pct'] for r in rows):.2f} | " + ' / '.join(f"{min(r[f'drawdown_{p}_pct'] for r in rows):.2f}" for p in (20,60,120))+' |')
    for symbol in SYMBOLS:
        rows=[r for r in daily if r['symbol']==symbol]
        symbol_events=[r for r in events if r['symbol']==symbol]
        symbol_recoveries=[r for r in recoveries if r['symbol']==symbol]
        lines += ['',f'## {symbol}','',
            f"Prior-support breaks beyond 1%: {sum(r['support_broken'] for r in rows)}; VIX stress days (>=25): {sum(r['market_stress'] for r in rows)}; severe days (>=30): {sum(r['severe_market_stress'] for r in rows)}. Below MA20/MA50: {sum(r['below_ma20'] for r in rows)}/{sum(r['below_ma50'] for r in rows)} sessions.", '',
            '| Peak date | Threshold | First crossing | Technical deterioration | First REVIEW | TRIM | Trough / loss % | Crossing blockers |',
            '|---|---|---|---|---|---|---|---|']
        for r in symbol_events:
            lines.append(f"| {r['peak_date']} | {r['threshold_pct']}% | {r['first_threshold_date']} | {r['first_technical_deterioration'] or 'none'} | {r['first_review'] or 'none'} | {r['first_trim'] or 'none'} | {r['trough_date']} / {r['max_drawdown_pct']:.2f} | {r['crossing_blockers']} |")
        if not symbol_events:
            lines.append('| — | No >=10% episode under the declared convention | — | — | — | — | — | — |')
        lines += ['',f"Extended period: {len(symbol_recoveries)} executed reduction episodes; FIFO missed recovery including residual units marked at period end ${sum(r['missed_recovery_fifo_dollars'] for r in symbol_recoveries):.2f} per $10,000 initial account (gross diagnostic, not total strategy underperformance).", '',
            '| Sale | Restore | Sessions reduced | Sale / restore price | Rebound from post-sale low before restoration % | Missed rise vs sale $ |',
            '|---|---|---|---|---|---|']
        for r in symbol_recoveries:
            lines.append(f"| {r['sale_at'][:10]} | {(r['restored_at'] or 'pending')[:10]} | {r['sessions_reduced']} | {r['sale_mid']:.2f} / {r['restoration_mid']:.2f} | {r['rebound_before_restore_pct']:.2f} | {r['missed_recovery_vs_sale_dollars']:.2f} |")
        metrics=extended[symbol]['metrics']
        baseline=extended[symbol]['baseline_metrics']
        lines += ['', f"Extended limited price replay return: Overlay {metrics['return_pct']:.2f}%, Buy & Hold {baseline['return_pct']:.2f}%; difference {metrics['return_pct']-baseline['return_pct']:.2f} percentage points, including modeled costs. This is separate from the gross FIFO diagnostic."]
    lines += ['', '## Alternative indicators: descriptive evidence, not strategy tuning','',
        'Fixed, conventional features are calculated before inspecting outcomes: last-5-session return minus previous-5-session return (fall acceleration); prior-20-close drawdown <= -10%; below/crossing MA20 or MA50; 20-session return relative to QQQ < 0; positive five-observation VIX change. None is added to the running engine. No October-specific threshold fitting or parameter selection is performed.', '',
        'indicator-evaluation.csv separates 2024–August 2026 from the requested window. It reports both active and inactive observations, full/censored forward-20-session horizons and the frequency of a subsequent >=10% decline measured from the signal close. Labels never cross the period boundary. Daily-signals.csv contains no forward outcomes. These overlapping observations are descriptive and correlated; they are not independent trials, an untouched holdout or proof of predictive value. Missing broad-market breadth cannot be tested. Most late-October signals lack a full follow-up horizon and are censored rather than assigned an invented outcome.', '',
        '| Symbol | Indicator | Pre-window active / inactive next-20 loss >=10% rate | Requested active / inactive rate |',
        '|---|---|---|---|']
    for symbol in SYMBOLS:
        for name in FLAGS:
            values=[]
            for period in ('pre_window','requested'):
                rates=[]
                for active in (True,False):
                    r=next(r for r in evaluation if r['symbol']==symbol and r['indicator']==name and r['period']==period and r['active']==active)
                    rate=r['forward_20_loss_10_rate_pct']
                    rates.append(f"{rate:.1f}% (n={r['complete_horizons']})" if rate is not None else 'unavailable (n=0)')
                values.append(' / '.join(rates))
            lines.append(f"| {symbol} | {name} | {values[0]} | {values[1]} |")
    lines += ['', '## Restoration interpretation and candidates for later tests','',
        'The recovery CSV explicitly reconciles the prior simulator diagnostic: matched_repurchase_cost_dollars + terminal_mark_cost_dollars = missed_recovery_fifo_dollars. Rebuying a full portfolio weight at a higher price may leave a smaller share count. The simulator carries unmatched sold FIFO units into later repurchases or terminal marking even after exposure returns to 100%. This is a counterfactual share-deficit diagnostic, not evidence that cash literally remained uninvested. It can greatly exceed the simple price rise up to the first restoration; both are shown separately.', '',
        'HOLD means the reduction formula is false, not that the price has regained MA20/MA50, relative strength or its prior peak. Three consecutive actionable HOLDs therefore form a risk-clearance delay rather than technical recovery confirmation. Daily-close publication and next-open execution add latency; a rebound can occur while 25% of shares remain sold. Returning at a higher price also buys fewer shares after costs. Conversely, waiting can avoid a continuing decline; a positive missed-recovery diagnostic alone does not establish that earlier entry was better.', '',
        'Candidate rules deserving separate predeclared walk-forward tests: one actionable HOLD versus three (speed/whipsaw trade-off); staged 1/3 restoration after each cleared-risk session; a close back above MA20 with positive relative strength; volatility normalization with hysteresis. A candidate should retain freshness checks, next-open fills and full cost accounting. Price confirmation can delay entry further; none is recommended as an improvement here and none has been substituted into the engine or simulator.', '',
        '## Definitions, provenance and reproducibility','',
        '- Run `python -m aae.backtest.diagnostics`. Input/output hashes and fixed configuration are in run.json. QQQ source: data/risk-diagnostics/manifest.json; original stocks/VIX: data/backtest/manifest.json.',
        '- Daily change uses the previous available close. MA20/50/200 include the current completed candle, which is available at decision time. RSI14 matches the existing TechnicalAnalysisEngine simple last-14-change RSI (including its flat-window convention), not Wilder smoothing.',
        '- DD20/60/120 use the maximum CLOSE of exactly the prior N trading rows, excluding the current candle. Positive distances above a peak are clipped to zero drawdown. Support is the minimum LOW of the prior 120 available candles, not a recent high; a large drawdown need not be near that low.',
        '- Technical deterioration is the first close below MA50, or below MA20 with negative five-session momentum, after the episode peak. It is a fixed diagnostic definition, not an engine input.',
        '- Episodes are peak-to-recovery closing-price excursions, separately seeded at the highest close in the prior 20, 60 and 120 sessions (also considering the study start close). Identical peak/threshold pairs are deduplicated and reference_windows records the contributing windows. This retains a recent local excursion even when an older, higher peak remains unrecovered (notably MU). Each 10/15/20 threshold is counted once per excursion, not every recross. Nested excursions are descriptive and are not independent system errors. Pre-window threshold crossings and unrecovered episodes are explicitly marked; rolling daily drawdowns provide the complementary continuous view.',
        '- Episode troughs, forward outcome rates and recovery minima are retrospective descriptions only. They never feed indicators or trading decisions. At a threshold crossing, the CSV records the actual known support, VIX, action, blockers and decision cutoff.',
        '- Recovery minima use sale-open and completed closes before the restoration open. Rebound percentage describes the stock; sold_units_rebound_dollars describes the foregone upside on sold units. missed_recovery_vs_sale_dollars measures only positive sale-to-repurchase price change, excluding fees; it is not a full counterfactual profit attribution. Reduced exposure and fee/slippage treatment are unchanged from PR #2.',
        '- Unavailable regime/breadth and retrospective price vintages prevent inference about the full historical Alpha OS system. Absence of TRIM under these rules is an observed signal gap, not proof of an ineffective decision. No production endpoints, databases, deployments or merges were used.']
    (args.output/'report.md').write_text('\n'.join(lines)+'\n')
    paths=inputs+[Path('data/backtest/manifest.json'),Path('data/risk-diagnostics/manifest.json'),
                 Path(__file__),Path('scripts/fetch_diagnostics_benchmark.py'),
                 Path('aae/engines/tactical_risk_overlay.py'),Path('aae/engines/technical_analysis.py'),Path('aae/backtest/simulator.py')]
    from dataclasses import asdict
    manifest=dict(overlay_config=asdict(TacticalRiskConfig()),
                  source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
                  output_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in args.output.iterdir() if p.suffix in {'.csv','.md'}},
                  counts=dict(daily=len(daily),events=len(events),recoveries=len(recoveries),indicator_groups=len(evaluation)))
    (args.output/'run.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest['counts']))


if __name__=='__main__':
    main()
