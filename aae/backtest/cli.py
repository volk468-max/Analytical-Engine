"""Run offline: python -m aae.backtest.cli --help."""
import argparse
import csv
import json
import hashlib
from dataclasses import replace
from itertools import product
from pathlib import Path
from .simulator import (Bar, Observation, OverlayPolicy, BuyAndHold, ArchivedDecisionPolicy,
                        ExecutionConfig, TacticalRiskConfig, simulate)

SYMBOLS = 'AMD NVDA MU TSM AVGO AMAT AMZN META PLTR LRCX NBIS'.split()


def write_csv(path, rows, fields=()):
    names = list(fields) or list(dict.fromkeys(key for row in rows for key in row))
    with path.open('w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=names, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def load_bars(path):
    rows = []
    with path.open() as file:
        for row in csv.DictReader(file):
            basis = row.pop('price_basis', 'unknown')
            # Nominal, unrevised prices with verified timestamps are required in strict mode.
            row['verified'] = row['verified'].lower() == 'true' and basis == 'nominal_unadjusted'
            for name in ('open', 'high', 'low', 'close'):
                row[name] = float(row[name])
            rows.append(Bar(**row))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=Path('data/backtest'))
    parser.add_argument('--output', type=Path, default=Path('reports/risk-backtest-v1'))
    parser.add_argument('--snapshots', type=Path, help='Verified atomic decision input archives (JSON)')
    parser.add_argument('--allow-assumed-availability', action='store_true', help='Explicit limited price replay; not a verified PIT backtest')
    parser.add_argument('--sensitivity', action='store_true')
    parser.add_argument('--start', default='2026-09-01T00:00:00+00:00')
    parser.add_argument('--end', default='2026-10-24T00:00:00+00:00', help='Inclusive bars by publication timestamp')
    parser.add_argument('--extended', action='store_true', help='Also replay 2024-01-01 onward separately')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    manifest_path = args.data/'manifest.json'
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        for name, expected in manifest.get('artifact_sha256', {}).items():
            artifact = args.data/name
            if hashlib.sha256(artifact.read_bytes()).hexdigest() != expected:
                raise ValueError('Input artifact checksum mismatch: ' + name)
    bars = load_bars(args.data/'bars.csv') if (args.data/'bars.csv').exists() else []
    markets = [Observation(**row) for row in json.loads((args.data/'markets.json').read_text())] if (args.data/'markets.json').exists() else []
    snapshots = [Observation(**row) for row in json.loads(args.snapshots.read_text())] if args.snapshots else []
    metrics, signals, trades, equity, coverage, sensitivity = [], [], [], [], [], []
    config = TacticalRiskConfig()  # fixed declared defaults, never selected from outcomes
    execution = ExecutionConfig()
    windows = [('requested', args.start, args.end)]
    if args.extended:
        windows.append(('extended_2024_2026', '2024-01-01T00:00:00+00:00', args.end))
    for symbol in SYMBOLS:
        selected = [bar for bar in bars if bar.symbol == symbol]
        coverage.append(dict(symbol=symbol, rows=len(selected), first=selected[0].close_at.isoformat() if selected else '',
                             last=selected[-1].close_at.isoformat() if selected else '',
                             verified_bars=all(b.verified for b in selected) if selected else False,
                             archived_snapshots=sum(o.value.get('snapshot', {}).get('symbol') == symbol for o in snapshots),
                             completeness='See source manifest; missing sessions are not synthesized'))
        for window, start, end in windows:
            policies = [BuyAndHold(), OverlayPolicy(config, markets)]
            for version in ('alpha_v1', 'risk_v2'):
                archived = [o for o in snapshots if o.value.get('snapshot', {}).get('symbol') == symbol]
                if not archived:
                    metrics.append(dict(symbol=symbol, strategy=version, window=window, status='UNAVAILABLE',
                                        reason='No verified historical fundamentals/revisions/decision input archive'))
                elif args.allow_assumed_availability:
                    metrics.append(dict(symbol=symbol, strategy=version, window=window, status='UNAVAILABLE',
                                        reason='Full Alpha OS comparison requires strict verified-price mode'))
                else:
                    policies.append(ArchivedDecisionPolicy(version, archived, config))
            for policy in policies:
                try:
                    result = simulate(selected, policy, start, end, execution,
                                      allow_assumed=args.allow_assumed_availability)
                    metrics.append(dict(result['metrics'], window=window, status='LIMITED_REPLAY' if args.allow_assumed_availability else 'INPUT_VERIFIED'))
                    for kind, rows in (('signals', signals), ('trades', trades), ('equity', equity)):
                        rows.extend(dict(item, window=window, strategy=policy.name) for item in result[kind])
                except (ValueError, KeyError) as exc:
                    metrics.append(dict(symbol=symbol, strategy=policy.name, window=window, status='UNAVAILABLE', reason=str(exc)))
        if args.sensitivity and selected:
            for stress, lookback, trim in product((20, 25, 30), (60, 120, 200), (.1, .25, .5)):
                variant = replace(config, stress_vix=stress, severe_vix=stress + 5,
                                  support_lookback=lookback, trim_fraction=trim)
                row = dict(symbol=symbol, stress_vix=stress, severe_vix=stress+5, support_lookback=lookback, trim_fraction=trim)
                try:
                    result = simulate(selected, OverlayPolicy(variant, markets), args.start, args.end,
                                      execution, allow_assumed=args.allow_assumed_availability)
                    row.update(result['metrics'], status='LIMITED_REPLAY' if args.allow_assumed_availability else 'INPUT_VERIFIED')
                except ValueError as exc:
                    row.update(status='UNAVAILABLE', reason=str(exc))
                sensitivity.append(row)
    for name, rows, fields in (
        ('summary.csv', metrics, ()), ('signals.csv', signals, ('symbol','strategy','window','decision_at','observed_at','action','actionable','reasons','weight','queued_target')),
        ('trades.csv', trades, ('symbol','strategy','window','executed_at','signal_at','side','units','mid_price','fill_price','commission','weight_before','weight_after','reason')),
        ('equity.csv', equity, ('symbol','strategy','window','date','equity','cash','shares','weight')),
        ('coverage.csv', coverage, ()), ('sensitivity.csv', sensitivity, ('symbol','stress_vix','severe_vix','support_lookback','trim_fraction','status'))):
        write_csv(args.output/name, rows, fields if not rows or name in {'signals.csv', 'trades.csv', 'equity.csv'} else ())
    (args.output/'run.json').write_text(json.dumps(dict(start=args.start, end=args.end, extended=args.extended,
        assumed_availability=args.allow_assumed_availability, execution=result_execution(execution),
        risk_config=result_execution(config), input_manifest=str(args.data/'manifest.json'),
        source_sha256={str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in
            [Path(__file__), Path(__file__).with_name('simulator.py'),
             Path(__file__).with_name('legacy_decision_engine.py'),
             Path('aae/engines/tactical_risk_overlay.py'), Path('aae/engines/decision_engine.py'),
             args.data/'bars.csv', args.data/'markets.json'] + ([args.snapshots] if args.snapshots else []) if path.exists()}), indent=2)+'\n')
    full_runs = sum(row.get('strategy') in {'alpha_v1', 'risk_v2'} and 'return_pct' in row for row in metrics)
    lines = ['# Alpha OS historical research v1', '',
        ('**No full Alpha OS v1 versus v2 performance comparison is available without archived point-in-time decision inputs.**' if not full_runs else f'Archive-backed strategy runs: {full_runs}; input provenance remains the producer responsibility.'), '',
        'The price-only overlay below is NOT the full Risk Engine v2 Decision Engine. Public prices are retrospective provider vintages; publication times are assumed. These results do not establish strict point-in-time strategy effectiveness.', '',
        f'Requested window: {args.start} through {args.end}. Actual per-symbol coverage appears below. No missing sessions or future bars are invented.', '',
        '| Symbol | First obtained bar | Last completed obtained bar | Rows |', '|---|---|---|---|']
    lines += [f"| {r['symbol']} | {r['first']} | {r['last']} | {r['rows']} |" for r in coverage]
    lines += ['', '## Limited price replay', '', '| Window | Symbol | Strategy | Return % | Max drawdown % | False/censored sells | Missed recovery $ |', '|---|---|---|---|---|---|---|']
    for row in metrics:
        if 'return_pct' in row:
            lines.append(f"| {row['window']} | {row['symbol']} | {row['strategy']} | {row['return_pct']:.2f} | {row['max_drawdown_pct']:.2f} | {row['false_signals']}/{row['censored_false_signals']} | {row['missed_recovery_dollars']:.2f} |")
    short_signals = [row for row in signals if row['window'] == 'requested' and row['strategy'] == 'risk_overlay_only']
    from collections import Counter
    counts = dict(Counter(row['action'] for row in short_signals))
    lines += ['', 'Observed short-window overlay action counts: ' + str(counts) + '.',
              'No claim about a full Alpha OS strategy follows from these limited results.', '',
              '## Sensitivity ranges (all variants retained)', '',
              '| Symbol | Variants | Return range % | Drawdown range % |', '|---|---|---|---|']
    for symbol in SYMBOLS:
        variants = [row for row in sensitivity if row['symbol'] == symbol and 'return_pct' in row]
        if variants:
            returns = [row['return_pct'] for row in variants]
            drawdowns = [row['max_drawdown_pct'] for row in variants]
            lines.append(f"| {symbol} | {len(variants)} | {min(returns):.2f} to {max(returns):.2f} | {min(drawdowns):.2f} to {max(drawdowns):.2f} |")
    lines += ['', '## Unavailable comparisons', '',
        'For each symbol/window summary.csv records missing full alpha_v1 and risk_v2 results as UNAVAILABLE with empty metrics, never zero-filled. Strict mode also refuses retrospective price vintages.', '',
        '## Assumptions and interpretation', '',
        '- Each symbol: independent $10,000 long-only account; first eligible open entry, no leverage or shorting.',
        '- 5 bps commission and 5 bps adverse slippage per side; zero cash interest, taxes and liquidity impact. No forced terminal liquidation.',
        '- Signals after bar publication; one later eligible session open delay. No same-close fills. Terminal pending orders remain unfilled.',
        '- Default TRIM once per risk episode; additional TRIM signals are logged but suppressed. Compound mode is explicit and has a 25% exposure floor.',
        '- Restore to full exposure after three consecutive actionable HOLD sessions, at a later open. REVIEW interrupts the sequence; unverified data cancel queued orders.',
        '- False signal: executed sell followed by a higher close five sessions after its execution. Insufficient follow-up is censored, not counted as correct.',
        '- Missed recovery: positive price appreciation on sold FIFO units through their repurchase or terminal mark; dollars, gross of costs. Not a causal attribution or total strategy underperformance.',
        '- Maximum drawdown includes initial capital and close marks; intraday drawdown is not measured. No dividends or corporate-action cash flows: returns are provider-price replay only, not total returns.',
        '- Predeclared sensitivity grid: VIX stress 20/25/30 (severe=stress+5), prior support 60/120/200 bars, trim 10/25/50%. All variants retained; no best setting selected. Extended window is a robustness exploration, not an untouched validation set.',
        ('The requested full period is incomplete: obtained bars end before 2026-10-23.' if any(row['last'] and row['last'][:10] < '2026-10-23' for row in coverage) else 'See actual per-symbol coverage above.'), '',
        'See docs/risk-backtest-v1.md and data/backtest/manifest.json for provenance, strict input contract, missing inputs and reproduction.']
    (args.output/'report.md').write_text('\n'.join(lines)+'\n')
    print(f'Report: {args.output}/report.md; comparisons: {len(metrics)}; sensitivity rows: {len(sensitivity)}')


def result_execution(config):
    from dataclasses import asdict
    return asdict(config)


if __name__ == '__main__':
    main()
