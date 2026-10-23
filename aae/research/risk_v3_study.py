"""Offline fixed-catalogue and expanding-window Risk Signal Engine v3 study."""
import gzip,hashlib,json
from dataclasses import asdict
from pathlib import Path
from statistics import mean
from aae.backtest.cli import write_csv
from .risk_signal_v3 import evaluate,catalogue,LEVELS
from .risk_v3_features import load_pack,build_features
from .risk_v3_evaluation import score_run,training_objective

ROOT=Path('reports/risk-signal-v3')
SYMBOLS=('AMD','NVDA','MU')
START='2021-01-01';END='2026-10-22'


def run(rows,variant,config,previous=None):
    output=[]
    for row in rows:
        signal=evaluate(row['symbol'],row['decision_at'],row['indicators_v3'],row['quality_v3'],
                        variant=variant,config=config,previous=previous)
        signal.update(date=row['date'],v2_overlay_action=row['action'])
        output.append(signal);previous=signal
    return output


def flat_signal(signal,mode,training_end=None):
    result=dict(symbol=signal['symbol'],date=signal['date'],decision_at=signal['decision_at'],mode=mode,
        variant=signal['variant'],configuration=signal['configuration'],training_end=training_end,
        risk_level=signal['risk_level'],data_status=signal['data_status'],score=signal['score'],
        **signal['indicators'],active_conditions='; '.join(signal['active_conditions']),
        change_reasons='; '.join(signal['change_reasons']),
        optional_source_status=json.dumps(signal['quality']['optional_sources'],sort_keys=True),
        quote_observed_at=signal['quality'].get('quote_observed_at'),qqq_observed_at=signal['quality'].get('qqq_observed_at'),
        publication_vintage_verified=signal['quality']['publication_vintage_verified'],
        v2_overlay_action=signal['v2_overlay_action'],confidence=signal['confidence'])
    result.update({'condition_'+k:v for k,v in signal['conditions'].items()})
    result.update({'group_'+k:v for k,v in signal.get('confirmation_groups',{}).items()})
    for group,values in signal['score_contributions'].items():
        result['score_'+group]=values['points'];result['raw_score_'+group]=values['raw_points']
    for key,value in (signal.get('decision_predicates') or {}).items():result['decision_'+key]=value
    return result


def choose(metrics_by_config):
    ranking=[]
    for name,metrics in metrics_by_config.items():
        value=training_objective(metrics)
        if value is not None:ranking.append((value,{'conservative':2,'balanced':1,'sensitive':0}[name],name))
    return max(ranking)[2] if ranking else 'balanced'


def quarter_regimes(features):
    regimes={}
    for symbol,rows in features.items():
        quarters={}
        for r in rows:
            if r['date']<START:continue
            year=int(r['date'][:4]);month=int(r['date'][5:7]);key=f'{year}Q{(month-1)//3+1}'
            quarters.setdefault(key,[]).append(r)
        for key,group in quarters.items():
            net=(group[-1]['close']/group[0]['close']-1)*100
            span=(max(r['close'] for r in group)/min(r['close'] for r in group)-1)*100
            label='strong_uptrend' if net>=20 else 'deep_decline' if net<=-20 else 'sideways_oscillation' if abs(net)<=10 and span>=15 else 'mixed'
            regimes[(symbol,key)]=(label,group[0]['date'],group[-1]['date'])
    return regimes


def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    configs={c.name:c for c in catalogue()}
    (ROOT/'catalogue.json').write_text(json.dumps({k:asdict(v) for k,v in configs.items()},indent=2)+'\n')
    bars,markets,manifest=load_pack()
    features={symbol:build_features([b for b in bars if b.symbol==symbol],markets,
        [b for b in bars if b.symbol=='QQQ'],[b for b in bars if b.symbol=='^SOX']) for symbol in SYMBOLS}
    cached={(variant,name):{symbol:run(rows,variant,config) for symbol,rows in features.items()}
            for variant in ('A','B','C') for name,config in configs.items()}
    summaries=[];events=[];outcomes=[];daily=[];full_payloads=[];annual=[];folds=[];regime_rows=[]
    def record(mode,variant,signals,start,end,training_end=None):
        metrics,labels,entries=score_run(features,signals,start,end)
        summaries.append(dict(metrics,mode=mode,variant=variant,training_end=training_end))
        events.extend(dict(r,mode=mode,variant=variant,training_end=training_end) for r in labels)
        outcomes.extend(dict(r,mode=mode,variant=variant,training_end=training_end) for r in entries)
        for symbol,series in signals.items():
            for s in series:
                if start<=s['date']<=end:
                    daily.append(flat_signal(s,mode,training_end))
                    full_payloads.append(dict(s,mode=mode,training_end=training_end))
        for year in range(int(start[:4]),int(end[:4])+1):
            for symbol in SYMBOLS:
                m,_,_=score_run(features,{symbol:signals[symbol]},max(start,f'{year}-01-01'),min(end,f'{year}-12-31'))
                annual.append(dict(m,mode=mode,variant=variant,symbol=symbol,year=year))
    for variant in ('A','B','C'):
        record('fixed_balanced',variant,cached[(variant,'balanced')],START,END)
        same_period,_,_=score_run(features,cached[(variant,'balanced')],'2023-01-01',END)
        summaries.append(dict(same_period,mode='fixed_balanced_test_period',variant=variant,training_end=None))
    walk={variant:{symbol:[] for symbol in SYMBOLS} for variant in ('A','B','C')}
    train_candidates=[]
    for test_year in (2023,2024,2025,2026):
        train_end=f'{test_year-1}-12-31';test_start=f'{test_year}-01-01';test_end=min(f'{test_year}-12-31',END)
        for variant in ('A','B','C'):
            training={name:score_run(features,cached[(variant,name)],START,train_end)[0] for name in configs}
            selected=choose(training)
            for name,m in training.items():
                train_candidates.append(dict(m,variant=variant,configuration=name,training_end=train_end,
                    test_start=test_start,test_end=test_end,objective=training_objective(m),selected=name==selected))
            test_signals={}
            for symbol,rows in features.items():
                subset=[r for r in rows if test_start<=r['date']<=test_end]
                previous=walk[variant][symbol][-1] if walk[variant][symbol] else None
                test_signals[symbol]=run(subset,variant,configs[selected],previous)
                if test_signals[symbol]:test_signals[symbol][0]['change_reasons'].append('Configuration frozen from '+train_end+': '+selected)
                walk[variant][symbol].extend(test_signals[symbol])
            m,_,_=score_run(features,test_signals,test_start,test_end)
            folds.append(dict(m,variant=variant,configuration=selected,training_end=train_end,test_year=test_year,
                              training_objective=training_objective(training[selected])))
    # Only genuinely generated test-fold signals enter walk-forward evaluation.
    for variant in ('A','B','C'):
        record('walk_forward',variant,walk[variant],'2023-01-01',END,training_end='expanding; see fold-selection.csv')
    # Mandatory diagnostic is a separately labelled subset, never used for tuning.
    diagnostic=[]
    for mode,source in (('fixed_balanced',{v:cached[(v,'balanced')] for v in ('A','B','C')}),('walk_forward',walk)):
        for variant in ('A','B','C'):
            for symbol in SYMBOLS:
                m,e,_=score_run(features,{symbol:source[variant][symbol]},'2026-09-01',END)
                diagnostic.append(dict(m,mode=mode,variant=variant,symbol=symbol))
                # Separate labels preserve nested local events in this window.
                events.extend(dict(r,mode=mode+'_SepOct',variant=variant) for r in e)
    regimes=quarter_regimes(features)
    for (symbol,key),(label,start,end) in regimes.items():
        for variant in ('A','B','C'):
            m,_,_=score_run(features,{symbol:cached[(variant,'balanced')][symbol]},start,end)
            regime_rows.append(dict(m,symbol=symbol,quarter=key,regime=label,variant=variant))
    recommendation=max([r for r in train_candidates if r['training_end']=='2025-12-31' and r['selected']],
                       key=lambda r: (r['objective'] if r['objective'] is not None else -1e9,r['variant']))
    for name,rows in (('daily-signals.csv',daily),('summary.csv',summaries),('events.csv',events),
        ('entry-outcomes.csv',outcomes),('annual-metrics.csv',annual),('fold-selection.csv',folds),
        ('training-candidates.csv',train_candidates),('diagnostic-SepOct.csv',diagnostic),('regime-metrics.csv',regime_rows)):
        write_csv(ROOT/name,rows)
    payload='\n'.join(json.dumps(s,sort_keys=True,separators=(',',':')) for s in full_payloads)+'\n'
    (ROOT/'daily-signals.jsonl.gz').write_bytes(gzip.compress(payload.encode(),mtime=0))
    write_report(summaries,events,folds,diagnostic,features,cached,walk,recommendation,manifest,regime_rows)
    paths=[Path(__file__),Path('aae/research/risk_signal_v3.py'),Path('aae/research/risk_v3_features.py'),
        Path('aae/research/risk_v3_evaluation.py'),Path('aae/backtest/diagnostics.py'),Path('scripts/fetch_risk_v3_data.py'),
        Path('data/risk-signal-v3/manifest.json')]
    metadata=dict(schema_version=1,research_only=True,recommendation_from_training_only=dict(variant=recommendation['variant'],configuration=recommendation['configuration'],training_end='2025-12-31'),
        source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        output_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.iterdir() if p.name!='run.json'},
        daily_rows=len(daily),event_rows=len(events),entry_outcomes=len(outcomes),folds=len(folds))
    (ROOT/'run.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(json.dumps({k:metadata[k] for k in ('daily_rows','event_rows','entry_outcomes','folds','recommendation_from_training_only')}))


def fmt(value,digits=1):return '—' if value is None else f'{value:.{digits}f}'


def write_report(summaries,events,folds,diagnostic,features,cached,walk,recommendation,manifest,regimes):
    lines=['# Risk Signal Engine v3 — research prototype','',
        '**Signals only. No position sizes, weights, trades, orders or production integration. V2 and Decision Engine remain unchanged.**','',
        '## Data and historical limits','',
        'AMD, NVDA, MU, QQQ and semiconductor index ^SOX: 2020 warm-up, evaluation 2021–22 October 2026. CBOE VIX is supplemental. Source responses, OHLCV, reported corporate actions, retrieval times, version and hashes: data/risk-signal-v3/manifest.json. 23 October is excluded. PR #2 supplies the publication-gated schema and PR #3 supplies causal diagnostic features; neither is modified.', '',
        'This is retrospective split-adjusted provider OHLC, not an independently verified point-in-time publication archive. Dividend-adjusted closes are not mixed in. Ratios/drawdowns/MA slopes/RSI/log-return volatility are invariant to a constant future split scaling of an earlier prefix; this does not prove historical price-vintage accuracy. Publication is conservatively inferred as next UTC midnight; early closes are delayed. Missing/late required prices or QQQ observations suppress the risk level (DATA_UNAVAILABLE/STALE). Optional stale/missing VIX or SOX are excluded and explicitly labelled; they never become a mandatory risk gate. All outputs say RESEARCH_RULE_MATCH_ONLY.', '',
        '## Fixed transparent variants and candidate catalogue','',
        '- **A, drawdown + trend:** WATCH at prior-20-close drawdown 5% (or fast five-session loss with price below MA20); REDUCE at 8% with price below falling MA20; CRITICAL at prior-60-close drawdown 20% below falling MA50. Balanced defaults shown.',
        '- **B, grouped confirmation:** price-path stress (DD20 >=8% or five-session loss >=7%) plus at least three of four groups: price path, trend, relative weakness, volatility. Trend requires below falling MA20 plus below MA50 or RSI<45; relative weakness is <=-3 pp versus QQQ or SOX over 20 matched sessions; volatility is RV20/RV60 >=1.25, RV20 growth >=25% in five sessions, or VIX>=25. Four groups (or severe DD60 with three) yield CRITICAL. Groups are conceptually distinct, not statistically independent.',
        '- **C, capped score:** price-path up to 3 points, trend up to 3, relative up to 2, volatility up to 2, prior-support break 1. WATCH/REDUCE/CRITICAL at 3/6/9 balanced points. Every predicate and raw/capped family contribution is retained. Correlated MA/RSI conditions cannot accumulate unlimited votes. VIX alone is insufficient; support is optional.',
        'catalogue.json freezes sensitive/balanced/conservative alternatives. It is a small predeclared policy catalogue, not an October fit. MA20/50 slopes are five-session percentage changes and their change versus the preceding five-session slope. RSI is Wilder14 (the unchanged PR #3 simple RSI remains separately computed). Realized volatility uses sample SD of 20/60 daily log returns, annualized sqrt(252). Support excludes the current bar, and rolling maxima use exactly the prior 20/60 closes. No future returns or extrema enter any signal.', '',
        '## Comparison','',
        '| Mode | Variant | Eligible drops | REDUCE before 10% / 15% / 20%, % | Median lead to 10%, sessions | False REDUCE after growth, % (n) | High-risk time % | Late after half the observed fall % |',
        '|---|---|---|---|---|---|---|---|']
    for r in summaries:
        lines.append(f"| {r['mode']} | {r['variant']} | {r['eligible_events']} | {fmt(r['recall_before_10_pct'])} / {fmt(r['recall_before_15_pct'])} / {fmt(r['recall_before_20_pct'])} | {fmt(r['median_lead_10_sessions'])} | {fmt(r['false_reduce_rate_pct'])} ({r['complete_reduce_horizons']}) | {fmt(r['reduce_time_pct']+r['critical_time_pct'])} | {fmt(r['late_after_half_fall_pct'])} |")
    lines += ['', 'Coverage recall includes an already-active warning at the event peak; carried_high_risk_events and recall_before_10_new_entry_pct separately show inherited versus newly initiated warnings. first_reduce_entry_date records the actual high-risk entry, which can precede the peak. First REDUCE in event tables means first high-risk observation within the excursion, not necessarily a new signal. Lead is positive only if the warning preceded the threshold session; zero is same-session, negative is late. Median lead includes late detections and excludes completely missed events; recall includes misses. False REDUCE is a new high-risk entry followed by a higher close at +20 sessions with no >=10% additional closing decline in the horizon. It is a descriptive false-warning label, not proof that a risk decision was economically wrong. Complete horizons and censored entries are reported separately. Five/ten/twenty-session returns and adverse excursions are in entry-outcomes.csv and summary.csv.', '',
        '## Walk-forward selection','',
        'Expanding training: 2021–2022 -> 2023, 2021–2023 -> 2024, 2021–2024 -> 2025, 2021–2025 -> 2026. A single configuration per variant is selected across all three stocks using earlier-period labels only, then frozen throughout the next test year. Training outcomes never extend past the training cutoff. Training objective = recall-before-10% - 0.5*false-growth rate - 0.25*high-risk time fraction - 0.01*switches per symbol-year. Ties prefer conservative, then balanced. No optimization of weights or October outcomes; all training candidates are exported.', '',
        '| Test year | Variant | Frozen configuration | Training end | Recall before 10% % | False REDUCE % |', '|---|---|---|---|---|---|']
    for r in folds:lines.append(f"| {r['test_year']} | {r['variant']} | {r['configuration']} | {r['training_end']} | {fmt(r['recall_before_10_pct'])} | {fmt(r['false_reduce_rate_pct'])} |")
    lines += ['', 'The expanding-window experiment prevents computational label leakage; it is not an untouched prospective study because the catalogue and retrospective source vintage were assembled after history was observable. Parameter changes occur only at fold boundaries; chronological risk states are carried into change explanations. First entries are not duplicated merely because a reporting year starts.', '',
        '## September–October 2026 diagnostic (not a tuning sample)','',
        '| Symbol | Variant | First WATCH | First REDUCE or CRITICAL | VIX at first REDUCE | Support broken then |', '|---|---|---|---|---|---|']
    for symbol in SYMBOLS:
        for variant in ('A','B','C'):
            sample=[s for s in walk[variant][symbol] if '2026-09-01'<=s['date']<=END]
            watch=next((s for s in sample if s['risk_level']=='WATCH'),None)
            reduce=next((s for s in sample if LEVELS.get(s['risk_level'],0)>=2),None)
            lines.append(f"| {symbol} | {variant} | {watch['date'] if watch else '—'} | {reduce['date'] if reduce else '—'} | {fmt(reduce['indicators'].get('vix')) if reduce else '—'} | {reduce['conditions'].get('support_broken') if reduce else '—'} |")
    lines += ['', 'This table uses walk-forward frozen configurations. The first high-risk date in a window can be a carried state from before the window; it is not automatically a new entry. Event-specific leads below are measured from each event peak, and left-censored peaks are excluded from recall denominators.', '']
    lines += ['', '### October peak-linked events (walk-forward)', '',
        '| Symbol | Peak | Variant | First high-risk observation / actual entry | Carried at peak | Lead before 10% / 15% / 20%, sessions |',
        '|---|---|---|---|---|---|']
    for r in events:
        if r['mode']=='walk_forward_SepOct' and r['peak_date']>='2026-10-01':
            leads=' / '.join(fmt(r[f'reduce_lead_{t}_sessions'],0) for t in (10,15,20))
            lines.append(f"| {r['symbol']} | {r['peak_date']} | {r['variant']} | {r['first_reduce'] or '—'} / {r['first_reduce_entry_date'] or '—'} | {r['reduce_carried_at_peak']} | {leads} |")
    for symbol in SYMBOLS:
        lines += [f'## {symbol}: complete fixed-balanced event table','',
            '| Peak | First 10% / 15% / 20% date | A first REDUCE (lead10) | B first REDUCE (lead10) | C first REDUCE (lead10) |', '|---|---|---|---|---|']
        groups={}
        for r in events:
            if r['mode']=='fixed_balanced' and r['symbol']==symbol:groups.setdefault(r['peak_date'],{})[r['variant']]=r
        for peak,group in sorted(groups.items()):
            r=next(iter(group.values()));thresholds=' / '.join(r[f'drawdown_{n}_date'] or '—' for n in (10,15,20))
            vals=[(group[v]['first_reduce'] or '—')+' ('+fmt(group[v]['reduce_lead_10_sessions'],0)+')' for v in ('A','B','C')]
            lines.append('| '+peak+' | '+thresholds+' | '+' | '.join(vals)+' |')
    wf_c=next(r for r in summaries if r['mode']=='walk_forward' and r['variant']=='C')
    lines += ['', '## Main finding','',
        f"The walk-forward C model detects REDUCE before 10% in {fmt(wf_c['recall_before_10_pct'])}% of eligible excursions, with median lead {fmt(wf_c['median_lead_10_sessions'])} sessions among detected events. Its false-growth warning rate is {fmt(wf_c['false_reduce_rate_pct'])}% and high-risk duty cycle {fmt(wf_c['reduce_time_pct']+wf_c['critical_time_pct'])}%. This supports feasibility of VIX-independent detection, but does not establish sufficiently reliable warnings: false alerts and late detections remain substantial. October C warnings precede 10% by two sessions for each studied stock; this diagnostic alone cannot validate the model.", '']
    lines += ['', '## Regimes, recommendation and interpretation','',
        'All calendar quarters are retained in regime-metrics.csv: strong uptrend >=20% close return, deep decline <=-20%, sideways |return|<=10% with >=15% closing range, otherwise mixed. These are retrospective descriptions, never input regime labels. The full event set includes deep 2022/2024–2025 corrections and fast drawdown/recovery episodes; no favorable episodes are selected.', '',
        f"Training-only candidate for further testing: **variant {recommendation['variant']} / {recommendation['configuration']}**, selected from 2021–2025 training metrics, not from 2026 or full-history rankings. This is a provisional research choice under the explicit objective, not a validated live recommendation. Inspect false warnings, late detections, duty cycle and switching alongside recall before retaining it.", '',
        'A price-local risk signal can fire with low VIX and intact long-term support by construction; the diagnostic tests whether it actually did so and how often it warned too late or during later growth. Not every decline is predictable. Correlated repeated events/horizons, low sample sizes and retrospective revisions prevent strong reliability claims. No position-size or profitability inference is made.', '',
        '## Definitions and reproduction','',
        '- Run `python scripts/fetch_risk_v3_data.py` only to refresh documented source responses; `python -m aae.research.risk_v3_study` reproduces the offline study. The source pack is frozen through 22 October; 2020 observations warm up all indicators.',
        '- Significant-event rule: excursion since a known trailing-20 closing high, ending on the next trailing-20 high (which need not recover an older all-time peak). Every event reaching 10% is retained; 15/20% labels are added when observed. Nested old peak drawdowns are not treated as independent predictions. Left-censored peaks and still-open episodes are explicit. Trough/fraction-of-fall and future-return fields are labels only, in separate evaluation files.',
        '- first_watch means actual WATCH; a direct jump to REDUCE does not invent an earlier WATCH. first_warning_at_least_watch records either. REDUCE detection includes CRITICAL. Over-half-fall timing uses the observed eventual trough; reduce_after_trough is separately counted. These are retrospective quality diagnostics, never decision inputs.',
        '- Aggregate fixed-balanced results use 2021–2026; walk-forward results use only generated test signals in 2023–2026. Their different periods must not be compared as like-for-like performance. Rows fixed_balanced_test_period provide the same 2023–2026 dates as walk-forward; annual CSVs give further detail. Invalid mandatory data produce no risk level, not HOLD. Optional source gaps are disclosed. Switches count valid risk-level transitions; yearly tables show raw observed counts, with 2026 incomplete and no extrapolation.',
        '- Daily CSV is compact; daily-signals.jsonl.gz retains full ticker/time/state, all indicator values, every condition, capped contributions, change reasons and source-quality metadata. It contains no sizing or execution fields. New REDUCE episode outcomes are isolated in entry-outcomes.csv; each 5/10/20 horizon is independently censored at its evaluation endpoint.',
        '- Source/code/output hashes, frozen catalogue, fold-selection and training-candidates record reproducibility. Existing production modules and services are untouched; test results/limits are in validation.md.']
    (ROOT/'report.md').write_text('\n'.join(lines)+'\n')


if __name__=='__main__':main()
