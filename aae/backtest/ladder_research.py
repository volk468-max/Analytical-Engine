"""Reproduce the frozen AMD Core + Tactical Ladder research pack offline."""
import csv
import hashlib
import json
from dataclasses import replace
from datetime import datetime, timezone
from itertools import product
from pathlib import Path
from statistics import mean
from collections import Counter
from .simulator import Bar, utc
from .cli import write_csv
from .ladder import LadderConfig, simulate_ladder, metrics, recovery_costs

ROOT=Path('reports/core-tactical-ladder')
DATA=Path('data/core-tactical-ladder')
CUT='2023-12-31'


def load_data():
    manifest=json.loads((DATA/'manifest.json').read_text())
    for name,digest in manifest['artifact_sha256'].items():
        if hashlib.sha256((DATA/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('Source checksum mismatch: '+name)
    actions=json.loads((DATA/'corporate-actions.json').read_text())
    if actions.get('splits') or actions.get('dividends'):
        raise ValueError('Use a verified nominal-price action conversion/pay-date ledger before running action-bearing data')
    rows=list(csv.DictReader((DATA/'amd.csv').open()))
    if {r['price_basis'] for r in rows}!={'provider_ohlc_no_in_window_adjustments'}:
        raise ValueError('Mixed/unsupported price bases')
    bars=[Bar(r['symbol'],r['open_at'],r['close_at'],r['available_at'],
              *[float(r[k]) for k in ('open','high','low','close')],r['source'],False) for r in rows]
    if any(b.close_at.date().isoformat()>'2026-10-22' for b in bars):
        raise ValueError('Frozen study excludes October 23')
    return bars,manifest


def select_episodes(bars):
    """All completed >=10% closing peak-to-recovery cycles, never strategy inputs."""
    peak=0; trough=0; qualifying=False; episodes=[]
    for i,b in enumerate(bars[1:],1):
        if b.close>=bars[peak].close:
            if qualifying:
                episodes.append(dict(name='cycle_'+str(len(episodes)+1),start=peak,end=i,completed=True,
                    selection='all_peak_to_recovery_10pct',drawdown_pct=(bars[trough].close/bars[peak].close-1)*100))
            peak=i; trough=i; qualifying=False
        else:
            if b.close<bars[trough].close:
                trough=i
            if b.close<=bars[peak].close*.9:
                qualifying=True
    if qualifying:
        episodes.append(dict(name='open_cycle',start=peak,end=len(bars)-1,completed=False,
            selection='right_censored_peak_to_recovery',drawdown_pct=(bars[trough].close/bars[peak].close-1)*100))
    # Include EVERY calendar quarter: no profit-based choice of trend/chop examples.
    quarters={}
    for i,b in enumerate(bars):
        key=(b.close_at.year,(b.close_at.month-1)//3+1)
        quarters.setdefault(key,[]).append(i)
    for (year,quarter),indices in quarters.items():
        first,last=indices[0],indices[-1]
        net=bars[last].close/bars[first].open-1
        span=max(b.close for b in bars[first:last+1])/min(b.close for b in bars[first:last+1])-1
        regime='strong_growth' if net>=.2 else 'deep_decline' if net<=-.2 else 'sideways_oscillation' if abs(net)<=.1 and span>=.15 else 'mixed'
        episodes.append(dict(name=f'{year}Q{quarter}',start=first,end=last,
            completed=(last<len(bars)-1 or bars[last].close_at.month in (3,6,9,12)),
            selection='all_calendar_quarters',regime=regime,drawdown_pct=None))
    indices=[i for i,b in enumerate(bars) if '2026-09-01'<=b.close_at.date().isoformat()<='2026-10-22']
    if indices:
        episodes.append(dict(name='Sep_Oct_2026_diagnostic',start=indices[0],end=indices[-1],
                             completed=False,selection='mandated_diagnostic',drawdown_pct=None))
    for e in episodes:
        if 'regime' not in e:
            length=e['end']-e['start']+1
            e['regime']='deep_decline_recovery' if e['drawdown_pct'] is not None and e['drawdown_pct']<=-30 else 'prolonged_correction' if length>=126 else 'correction_recovery'
    return episodes


def summarize(result,bars,tag,*,initial=None,first=0,last=None,benchmark=None):
    last=len(result['daily'])-1 if last is None else last
    marks=result['daily'][first:last+1]
    at_start=utc(result['daily'][first-1]['close_at']) if first else bars[first].open_at
    initial=initial if initial is not None else (result['daily'][first-1]['equity'] if first else result['config']['capital'])
    selected=[t for t in result['trades'] if bars[first].open_at<=utc(t['executed_at'])<=bars[last].close_at]
    output=dict(scenario=tag,**metrics(marks,selected,initial,at_start))
    output.update(recovery_costs(selected,marks[-1]['close'],marks[-1]['base_shares']))
    end_prefix=[t for t in result['trades'] if utc(t['executed_at'])<=bars[last].close_at]
    end_cost=recovery_costs(end_prefix,marks[-1]['close'],marks[-1]['base_shares'])['missed_recovery_dollars']
    if first:
        before=result['daily'][first-1]
        start_prefix=[t for t in result['trades'] if utc(t['executed_at'])<bars[first].open_at]
        start_cost=recovery_costs(start_prefix,before['close'],before['base_shares'])['missed_recovery_dollars']
    else:
        start_cost=0
    output.update(inherited_missed_recovery_at_start=start_cost,inherited_missed_recovery_at_end=end_cost,
                  inherited_missed_recovery_change=end_cost-start_cost)
    output['pending_at_end']=result['state'].pending is not None if last==len(result['daily'])-1 else marks[-1]['pending_order'] is not None
    output['source_validity']='retrospective_provider_price_replay'
    if benchmark is not None:
        bh_initial=benchmark['daily'][first-1]['equity'] if first else benchmark['config']['capital']
        bh_end=benchmark['daily'][last]['equity']
        bh=metrics(benchmark['daily'][first:last+1],[],bh_initial,at_start)
        output.update(relative_return_pp=output['return_pct']-bh['return_pct'],
            drawdown_reduction_pp=output['max_drawdown_pct']-bh['max_drawdown_pct'],
            relative_final_dollars=marks[-1]['equity']-bh_end,
            relative_final_wealth_pct=(marks[-1]['equity']/bh_end-1)*100,
            average_cash_vs_missing_shares_dollars=mean(r['cash']-(r['base_shares']-r['shares'])*r['close'] for r in marks),
            final_cash_vs_missing_shares_dollars=marks[-1]['cash']-(marks[-1]['base_shares']-marks[-1]['shares'])*marks[-1]['close'])
    return output


def charts(bh,ladder):
    import matplotlib
    matplotlib.use('Agg')
    matplotlib.rcParams['svg.hashsalt']='alpha-core-tactical-ladder-v1'
    import matplotlib.pyplot as plt
    dates=[utc(row['close_at']) for row in bh['daily']]
    fig,axes=plt.subplots(3,1,figsize=(12,10),sharex=True)
    for result,label,color in ((bh,'Buy & Hold','#64748b'),(ladder,'Core + Tactical Ladder','#2563eb')):
        nav=[r['equity'] for r in result['daily']]
        peak=result['config']['capital']; dd=[]
        for value in nav:
            peak=max(peak,value); dd.append((value/peak-1)*100)
        axes[0].plot(dates,nav,label=label,color=color)
        axes[1].plot(dates,dd,label=label,color=color)
        axes[2].plot(dates,[r['share_fraction']*100 for r in result['daily']],label=label+' shares / original',color=color)
    axes[2].plot(dates,[r['equity_weight']*100 for r in ladder['daily']],label='Ladder equity value / NAV',color='#f59e0b',alpha=.8)
    axes[0].set_ylabel('Capital, USD'); axes[1].set_ylabel('Drawdown, %'); axes[2].set_ylabel('Stock allocation, %')
    for ax in axes:
        ax.legend(loc='best'); ax.grid(alpha=.2)
    fig.suptitle('AMD 2021–2026: last executed-fill anchor, 2% / 5% / 50% / 2%\nRetrospective price replay; no claim of verified strategy effectiveness')
    fig.tight_layout()
    fig.savefig(ROOT/'capital-drawdown-position.png',dpi=160)
    fig.savefig(ROOT/'capital-drawdown-position.svg',metadata={'Date':None})
    svg=ROOT/'capital-drawdown-position.svg'
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    plt.close(fig)


def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    bars,manifest=load_data(); cfg=LadderConfig()
    bh=simulate_ladder(bars,cfg,ladder=False); base=simulate_ladder(bars,cfg)
    split=next(i for i,b in enumerate(bars) if b.close_at.year==2024)
    summary=[]; all_trades=[]; all_daily=[]; all_events=[]; episode_rows=[]; sensitivity=[]
    def record(result,tag,include_daily=False):
        all_trades.extend(dict(t,scenario=tag) for t in result['trades'])
        if include_daily:
            all_daily.extend(dict(r,scenario=tag) for r in result['daily'])
            all_events.extend(dict(e,scenario=tag) for e in result['events'])
    for result,name in ((bh,'buy_hold'),(base,'ladder_base')):
        summary.append(summarize(result,bars,name+'_continuous',benchmark=bh))
        summary.append(summarize(result,bars,name+'_development_2021_2023',last=split-1,benchmark=bh))
        summary.append(summarize(result,bars,name+'_validation_carry_2024_2026',first=split,benchmark=bh))
        independent=simulate_ladder(bars[split:],cfg,ladder=name!='buy_hold')
        ref=simulate_ladder(bars[split:],cfg,ladder=False)
        summary.append(summarize(independent,bars[split:],name+'_validation_independent',benchmark=ref))
        record(result,name+'_continuous',True)
        record(independent,name+'_validation_independent',True)
    selected=select_episodes(bars)
    for episode in selected:
        first,last=episode['start'],episode['end']; subset=bars[first:last+1]
        independent_bh=simulate_ladder(subset,cfg,ladder=False)
        for method in ('independent','continuous'):
            for strategy in ('buy_hold','ladder'):
                if method=='independent':
                    result=independent_bh if strategy=='buy_hold' else simulate_ladder(subset,cfg)
                    row=summarize(result,subset,episode['name']+'_'+method+'_'+strategy,benchmark=independent_bh)
                    record(result,row['scenario'],True)
                else:
                    result=bh if strategy=='buy_hold' else base
                    row=summarize(result,bars,episode['name']+'_'+method+'_'+strategy,first=first,last=last,benchmark=bh)
                # Continuous windows have different inherited capital; compare RETURNS, not nominal dollars.
                row.update(episode=episode['name'],method=method,strategy=strategy,
                    start=subset[0].open_at.date().isoformat(),end=subset[-1].close_at.date().isoformat(),
                    completed=episode['completed'],selection=episode['selection'],regime=episode['regime'],
                    inherited_anchor=result['daily'][first-1]['anchor'] if first and method=='continuous' else None,
                    inherited_cash=result['daily'][first-1]['cash'] if first and method=='continuous' else None,
                    inherited_shares=result['daily'][first-1]['shares'] if first and method=='continuous' else None,
                    inherited_pending_order=result['daily'][first-1]['pending_order'] if first and method=='continuous' else None)
                episode_rows.append(row)
    # Fixed complete grid. No winner is picked, and no threshold is fitted on October.
    for sell,fraction,minimum,buy in product((.01,.02,.03,.04),(.025,.05,.1),(.4,.5,.6,.7),(.02,.03,.04)):
        variant=replace(cfg,sell_step=sell,trade_fraction=fraction,min_fraction=minimum,buy_step=buy)
        tag=f'grid_s{sell}_q{fraction}_m{minimum}_b{buy}'
        result=simulate_ladder(bars,variant); independent=simulate_ladder(bars[split:],variant)
        for window,run,series,first,last in (
            ('full',result,bars,0,len(bars)-1),('development',result,bars,0,split-1),
            ('validation_carry',result,bars,split,len(bars)-1),('validation_independent',independent,bars[split:],0,len(bars)-split-1)):
            ref=bh if window!='validation_independent' else simulate_ladder(bars[split:],variant,ladder=False)
            row=summarize(run,series,tag+'_'+window,first=first,last=last,benchmark=ref)
            sensitivity.append(dict(row,family='parameters',window=window,**run['config']))
        record(result,tag+'_full'); record(independent,tag+'_validation_independent')
    for commission,slippage,delay in product((0,5,10,25),(0,5,10,25),(1,2,3)):
        variant=replace(cfg,commission_bps=commission,slippage_bps=slippage,delay_sessions=delay)
        tag=f'execution_c{commission}_s{slippage}_d{delay}'
        result=simulate_ladder(bars,variant); ref=simulate_ladder(bars,variant,ladder=False)
        sensitivity.append(dict(summarize(result,bars,tag,benchmark=ref),family='execution',window='full',**result['config']))
        record(result,tag)
    for tag,changes in (('whole_shares',{'lot_size':1}),('lots_of_10',{'lot_size':10}),
                        ('half_fill_cancel',{'fill_fraction':.5}),('whole_half_fill',{'lot_size':1,'fill_fraction':.5}),
                        ('reject_unaffordable_partial',{'partial_cash':False})):
        variant=replace(cfg,**changes); result=simulate_ladder(bars,variant); ref=simulate_ladder(bars,variant,ladder=False)
        row=dict(summarize(result,bars,tag,benchmark=ref),family='rounding_partial',window='full',**result['config'])
        sensitivity.append(row); summary.append(row); record(result,tag,True)
    cash_impact=[]
    for r,b in zip(base['daily'],bh['daily']):
        cash_delta=r['cash']-b['cash']
        share_delta=(r['shares']-b['shares'])*r['close']
        cash_impact.append(dict(date=r['date'],ladder_cash=r['cash'],buy_hold_cash=b['cash'],
            cash_delta_dollars=cash_delta,share_market_value_delta_dollars=share_delta,
            equity_delta_dollars=r['equity']-b['equity']))
    write_csv(ROOT/'cash-impact.csv',cash_impact)
    write_csv(ROOT/'summary.csv',summary)
    write_csv(ROOT/'trades.csv',all_trades)
    write_csv(ROOT/'daily-equity.csv',[{k:r[k] for k in ('scenario','date','close_at','close','equity','cash','equity_weight','cash_weight')} for r in all_daily])
    write_csv(ROOT/'position-history.csv',all_daily)
    write_csv(ROOT/'events.csv',all_events)
    write_csv(ROOT/'episodes.csv',episode_rows)
    regime_rows=regime_summary(episode_rows)
    write_csv(ROOT/'regime-summary.csv',regime_rows)
    write_csv(ROOT/'sensitivity.csv',sensitivity)
    charts(bh,base)
    report(summary,episode_rows,sensitivity,base,bh,manifest)
    sources=[Path(__file__),Path('aae/backtest/ladder.py'),Path('aae/backtest/simulator.py'),
             Path('aae/backtest/cli.py'),Path('scripts/fetch_ladder_data.py'),DATA/'manifest.json',DATA/'amd.csv']
    import platform,matplotlib
    run=dict(schema_version=1,python_version=platform.python_version(),matplotlib_version=matplotlib.__version__,
        config=base['config'],development='2021-2023',chronological_validation='2024-2026',
        completed_cycles=sum(e['completed'] and e['selection']=='all_peak_to_recovery_10pct' for e in selected),
        source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        output_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.iterdir() if p.name!='run.json'})
    (ROOT/'run.json').write_text(json.dumps(run,indent=2)+'\n')
    print(json.dumps(dict(sessions=len(bars),completed_cycles=run['completed_cycles'],summary=len(summary),episodes=len(episode_rows),sensitivity=len(sensitivity),trades=len(all_trades))))


def regime_summary(episodes):
    output=[]
    for method in ('independent','continuous'):
        regimes=sorted({r['regime'] for r in episodes if r['selection']=='all_calendar_quarters' and r['completed']})
        for regime in regimes:
            rows=[r for r in episodes if r['method']==method and r['strategy']=='ladder'
                  and r['selection']=='all_calendar_quarters' and r['completed'] and r['regime']==regime]
            output.append(dict(method=method,regime=regime,quarters=len(rows),
                mean_relative_return_pp=mean(r['relative_return_pp'] for r in rows),
                mean_drawdown_reduction_pp=mean(r['drawdown_reduction_pp'] for r in rows)))
    return output


def report(summary,episodes,sensitivity,base,bh,manifest):
    main=[r for r in summary if r['scenario'] in ('buy_hold_continuous','ladder_base_continuous')]
    lines=['# AMD — Alpha Core + Tactical Ladder v1','',
        '**Research only. No changes to Decision Engine, Tactical Risk Overlay, production services or live trading. No merges.**','',
        f"Coverage: {manifest['first']}–{manifest['last']}, {manifest['rows']} completed OHLCV sessions. 1 January 2021 was a market holiday; first entry is 4 January. 23 October 2026 is deliberately excluded. Source: Yahoo chart, retrieved {manifest['retrieved_at']}. Raw source, normalized OHLCV, action metadata and SHA-256 hashes are committed in data/core-tactical-ladder.", '',
        '## Fixed control and main comparison','',
        'Control: sale step 2%, sale/buy quantity 5% of initial executed shares, core floor 50%, buy step 2%; $100,000 initial capital, 5 bps commission and 5 bps adverse slippage each side. One next-eligible-open execution after a completed-bar signal. No leverage, shorting, cash interest, external cash top-ups or forced terminal liquidation.', '',
        '| Metric | Buy & Hold | Ladder control |','|---|---|---|']
    for key in ('initial_equity','final_equity','return_pct','cagr_pct','max_drawdown_pct','max_drawdown_duration_sessions',
                'annualized_volatility_pct','sharpe_rf_zero','sortino_rf_zero','buys','sells','commissions','slippage_dollars',
                'turnover_initial_capital','average_share_fraction','minimum_share_fraction','average_equity_weight',
                'maximum_cash_weight','average_cash','final_cash','final_shares','initial_capital_recovery_date',
                'initial_capital_first_loss_date','initial_capital_recovery_after_loss_date','initial_capital_recovery_after_loss_sessions'):
        vals=[f'{r[key]:.4f}' if isinstance(r.get(key),(float,int)) else str(r.get(key)) for r in main]
        lines.append('| '+key+' | '+' | '.join(vals)+' |')
    control=main[1]
    lines += ['',f"Ladder minus Buy & Hold: {control['relative_return_pp']:.2f} percentage points of total return; maximum-drawdown change {control['drawdown_reduction_pp']:.2f} percentage points (positive = shallower drawdown). Positive FIFO missed-recovery diagnostic including modeled trade costs: ${control['missed_recovery_dollars']:.2f}; this is not additive net P&L attribution.", '',
        '![Capital, drawdown and allocation](capital-drawdown-position.png)', '',
        '## Exact state machine and boundary behavior','',
        'PR #2 provides the shared Bar/time schema and cost/next-open assumptions. Its executor targets NAV weights and restores after HOLDs, which does not implement a fixed-original-quantity ladder; this isolated quantity executor is therefore separate and does not modify that executor. The reference is the actual adverse fill price of the initial purchase, then of each nonzero tactical execution. Commission is a separate cash debit. Price thresholds are inclusive. At a lower or upper quantity boundary the reference freezes; it is never moved to a later-known peak/trough. A rising fully invested position therefore does not trail a new high, and a falling core-only position does not trail a new low. This path dependence can leave the ladder inactive through large peak-relative moves or delay repurchase far into a recovery.', '',
        'At most one outstanding order and one fill per session. Close-time orders execute at the next available open strictly after publication; delayed variants wait additional eligible opens. Orders are not revalidated against the new open. The daily adapter requires publication before the following session open; it rejects late feeds instead of reordering decisions across an intervening fill. A general asynchronous event-clock adapter is outside this v1. A gap fills one quantity step at the actual available open, never a sequence of fictional threshold fills. Further signals wait for a later completed bar. Unfilled terminal orders remain pending.', '',
        'Share limits concern quantity, not portfolio weight: keeping 50% of original shares may leave less than 50% of NAV in AMD after a deep decline. Buy quantities cannot exceed previously sold units or available cash including costs. The control allows affordable fractional partial buys; it cancels any unfilled remainder. Any nonzero partial fill updates the reference to that fill. No-fill rejection freezes it. Partial-liquidity sensitivity caps tactical orders only; the initial benchmark package remains fully funded. It uses deterministic one-shot quantity caps, not a realistic order-book model.', '',
        '## Cycles and inherited state','',
        'All >=10% closing-peak drawdowns that subsequently recover their prior closing peak are included. These are retrospective episode labels only; no extrema enter trading signals. Open cycles are right-censored. All calendar quarters are also included, without profit-based selection: strong growth = >=20% open-to-last-close return; deep decline = <=-20%; sideways oscillation = absolute return <=10% and closing range >=15%. Long corrections are identified by cycle duration >=126 sessions. Nested shorter drawdowns inside an unrecovered peak excursion are not independent complete cycles.', '',
        'Every episode has A: independent $100,000/full-position entry; B: slices of the same uninterrupted 2021 state, including pending orders, cash and last executed reference. Continuous returns use the previous close NAV as entry capital; independent returns include fresh entry costs. Peak-boundary independent entries are ex-post diagnostic windows, not an executable peak-timing strategy. Inherited accounts can have different initial NAV, so compare their percentage returns rather than dollar endpoints.', '',
        '| Episode | Regime | Complete | A Ladder / B&H return % | B Ladder / B&H return % |','|---|---|---|---|---|']
    names=list(dict.fromkeys(r['episode'] for r in episodes))
    for name in names:
        group=[r for r in episodes if r['episode']==name]
        first=group[0]
        values=[]
        for method in ('independent','continuous'):
            lr=next(r for r in group if r['method']==method and r['strategy']=='ladder')
            br=next(r for r in group if r['method']==method and r['strategy']=='buy_hold')
            values.append(f"{lr['return_pct']:.2f} / {br['return_pct']:.2f}")
        lines.append(f"| {name} | {first['regime']} | {first['completed']} | {values[0]} | {values[1]} |")
    deep=[r for r in episodes if r['episode']=='cycle_4' and r['strategy']=='ladder']
    if len(deep)==2:
        independent=next(r for r in deep if r['method']=='independent')
        continuous=next(r for r in deep if r['method']=='continuous')
        lines += ['', f"Reset effect example, cycle_4 (2024–2025): independent entry reduces local maximum drawdown by {independent['drawdown_reduction_pp']:.2f} pp, while the inherited strategy changes it by {continuous['drawdown_reduction_pp']:.2f} pp. Resetting the executed reference near an ex-post peak is materially different from carrying the old reference and exhausted cash; independent-cycle protection must not be attributed to the uninterrupted strategy."]
    lines += ['', '### Completed-quarter regime aggregates', '',
        'Arithmetic means of non-overlapping completed calendar quarters only; labels are retrospective, not strategy signals.', '',
        '| Method | Regime | Quarters | Mean relative return pp | Mean drawdown reduction pp |',
        '|---|---|---|---|---|']
    for r in regime_summary(episodes):
        lines.append(f"| {r['method']} | {r['regime']} | {r['quarters']} | {r['mean_relative_return_pp']:.2f} | {r['mean_drawdown_reduction_pp']:.2f} |")
    lines += ['', '## Parameters, costs and execution','',
        'All 144 parameter combinations are retained: sell step 1/2/3/4%, quantity 2.5/5/10%, minimum 40/50/60/70%, buy step 2/3/4%. The 50% core promise applies to the fixed control; experimental floors explicitly redefine the untouched quantity. sensitivity.csv contains full history, development 2021–2023, validation 2024–2026 independently funded, and validation with inherited state for every combination. No parameter winner is selected. This chronological split is not an unseen prospective holdout: the research was specified after historical markets were observable.', '',
        'Execution grid: commission 0/5/10/25 bps × slippage 0/5/10/25 bps × delays 1/2/3 sessions, plus whole-share/10-share lots, half-sized one-shot partial fills, and rejection rather than affordable partial filling. Lot sizes floor trade quantities and never force the core below its limit. Initial strategic shares are defined by the actual fully funded initial lot; initial order is an ex-ante benchmark commitment, not a decision based on its future close.', '',
        '| Family/window | Count | Relative return range pp | Drawdown reduction range pp |','|---|---|---|---|']
    for family,window in (('parameters','full'),('parameters','development'),('parameters','validation_carry'),('parameters','validation_independent'),('execution','full'),('rounding_partial','full')):
        rows=[r for r in sensitivity if r['family']==family and r['window']==window]
        lines.append(f"| {family}/{window} | {len(rows)} | {min(r['relative_return_pp'] for r in rows):.2f} to {max(r['relative_return_pp'] for r in rows):.2f} | {min(r['drawdown_reduction_pp'] for r in rows):.2f} to {max(r['drawdown_reduction_pp'] for r in rows):.2f} |")
    lines += ['', '### Rounding and one-shot partial execution', '',
        '| Variant | Final capital $ | Return % | Max drawdown % | Final shares | Buys / sells |',
        '|---|---|---|---|---|---|']
    for row in [control]+[r for r in summary if r.get('family')=='rounding_partial']:
        lines.append(f"| {row['scenario']} | {row['final_equity']:.2f} | {row['return_pct']:.2f} | {row['max_drawdown_pct']:.2f} | {row['final_shares']:.4f} | {row['buys']} / {row['sells']} |")
    lines += ['', '### Execution sensitivity examples (full grid retained)', '',
        '| Commission / slippage bps | Delay sessions | Return % | Relative return pp | Max drawdown % |',
        '|---|---|---|---|---|']
    for commission,slippage,delay in ((0,0,1),(5,5,1),(10,10,1),(25,25,1),(5,5,2),(5,5,3)):
        row=next(r for r in sensitivity if r['family']=='execution' and r['commission_bps']==commission
                 and r['slippage_bps']==slippage and r['delay_sessions']==delay)
        lines.append(f"| {commission} / {slippage} | {delay} | {row['return_pct']:.2f} | {row['relative_return_pp']:.2f} | {row['max_drawdown_pct']:.2f} |")
    lines += ['', 'Delays change the sequence of actual fills and references, not just a fixed return haircut. These examples and the grid do not select a preferable execution setting.']
    lines += ['', '### Cash and missing shares', '',
        f"At the endpoint, cash contributes ${base['daily'][-1]['cash']-bh['daily'][-1]['cash']:.2f} to relative NAV, while the share-value difference contributes ${(base['daily'][-1]['shares']-bh['daily'][-1]['shares'])*base['daily'][-1]['close']:.2f}. Their sum exactly equals the strategy-minus-benchmark capital difference. cash-impact.csv gives this daily identity. Final wealth is {control['relative_final_wealth_pct']:.2f}% below the benchmark; this is distinct from the {control['relative_return_pp']:.2f} percentage-point difference in total return. Idle cash can cushion a decline, but cash depletion and smaller repurchased quantities can leave a permanent share deficit with no remaining cash buffer."]
    counts=Counter(e['event'] for e in base['events'])
    lines += ['', '### Control state constraints', '',
        f"No-cash BUY blocks: {counts['BUY_BLOCKED_NO_CASH_ANCHOR_FROZEN']}; frozen lower-bound observations: {counts['LOWER_BOUND_ANCHOR_FROZEN']}; frozen upper-bound observations: {counts['UPPER_BOUND_ANCHOR_FROZEN']}. A quantity deficit can persist while equity weight is 100%: this means the account owns fewer shares after costly repurchases, not that tactical cash is still available."]
    full_grid=[r for r in sensitivity if r['family']=='parameters' and r['window']=='full']
    lines += ['', f"Across the predeclared full-history grid, {sum(r['relative_return_pp']<-1e-8 for r in full_grid)} of {len(full_grid)} configurations underperform Buy & Hold by total return; {sum(r['drawdown_reduction_pp']>1e-8 for r in full_grid)} reduce maximum drawdown. This documents a trade-off, not a selected best strategy or an independent success test."]
    lines += ['', '## Five research questions','',
        f"1. **Drawdown:** the control changes maximum drawdown by {control['drawdown_reduction_pp']:.2f} pp; see the table for its duration and volatility. Core retention and cash reserves can cushion losses, but a frozen upper reference is not a trailing risk stop.",
        f"2. **Recovery cost:** matched repurchase price/cost gaps total ${control['matched_repurchase_gap_dollars']:.2f}; remaining sold-unit terminal marking is ${control['terminal_share_gap_mark_dollars']:.2f}. The separate net return difference is {control['relative_return_pp']:.2f} pp. Cash earns zero; repurchases may be cash-starved and cannot magically restore the original shares.",
        f"3. **Adverse round trips:** {control['adverse_buy_sequences']} of {control['matched_buy_sequences']} buy executions matching earlier sales cost more per matched unit than FIFO sale proceeds (including modeled fees/slippage). A buy can match several sales; this is a descriptive execution-sequence count, not an independent statistical trial.",
        '4. **Robustness:** all neighboring configurations and costs are published, with development/validation segments separated. Ranges above quantify sensitivity rather than proving stability. Repeated inspection of this history prevents claims of independent optimization success.',
        f"5. **Usefulness:** on this dataset the fixed control does not demonstrate a more favorable overall profile: its Sharpe is {control['sharpe_rf_zero']:.3f} versus {main[0]['sharpe_rf_zero']:.3f} for Buy & Hold, while a {control['drawdown_reduction_pp']:.2f} pp shallower worst drawdown costs {abs(control['relative_return_pp']):.2f} pp of total return. An investor may value a different point on this trade-off, but the 50% share floor is not a 50% drawdown cap. Retrospective prices and simplified execution prevent an effectiveness claim; no production recommendation follows.", '',
        'Regime comparisons are in the complete episode table, including strong growth, falling markets, prolonged recovery, sideways oscillation and the separately mandated September–October 2026 slice. Static boundaries can miss strong growth after cash becomes exhausted and can also avoid buying a still-declining position. Episode labels are not predictive market-regime inputs.', '',
        '## Metric definitions, data limits and reproduction','',
        '- Run `python scripts/fetch_ladder_data.py` only to refresh the frozen research source, then `python -m aae.backtest.ladder_research`. Report reproduction itself is offline. Install requirements-research.txt for matplotlib; numerical accounting uses the standard library.',
        '- OHLCV and reported actions use one provider vintage and one consistent price basis. AMD reports no in-window splits or dividends; adjusted close equals close for every retained row. Adjusted close is not mixed into signals. Action completeness and nominal-price fidelity are not independently attested. The importer refuses action-bearing/mismatched adjusted data rather than silently mixing prices. The simulator applies known splits prospectively to holdings, original-unit limits, pending quantities and the reference. Dividend-bearing data require an ex-date entitlement/payment-date ledger and are explicitly refused by this data adapter.',
        '- Availability is inferred as next UTC midnight after the session; fixed open+6.5h close attribution delays early closes conservatively. Prices/volumes are retrospective and can be revised. Missing sessions are not interpolated. No historical broker quotes, capacity constraints, partial-fill probabilities, taxes, dividend reinvestment, cash yield or independent exchange calendar are available.',
        '- Maximum drawdown uses daily-close NAV including entry costs; duration is the longest consecutive run below the previous NAV high, including right-censored runs. No intraday drawdown claim. initial_capital_recovery_date is the first close >= initial NAV; additionally, recovery_after_loss records the first recapture after an actual underwater close and its session wait. Blank after-loss fields mean no such recapture (or no initial-capital loss); flags distinguish these cases. None is a synthetic future peak-recovery date.',
        '- CAGR uses actual elapsed calendar days and is blank for periods shorter than a year. Sample standard deviation of daily simple NAV returns is annualized by sqrt(252). Sharpe uses zero risk-free rate; Sortino uses zero target and root-mean-square negative returns over all observations. Zero/insufficient denominators yield blank, never infinity. These are descriptive annualized ratios, without normality/independence claims.',
        '- Turnover is total absolute filled notional / episode initial capital, including initial entry where applicable. Average cash is actual idle dollars; stock value and cash sum to NAV each day. share_fraction and equity_weight are separately reported. Continuous period loss/return comparisons use each strategy own inherited capital. Episode drawdown peaks reset to that window initial NAV; full-history drawdown is measured separately without resetting account state.',
        '- FIFO missed-recovery cost is positive buy cost minus matched sale proceeds plus positive terminal value of unmatched sold units. It can persist after invested weight rises, and is not exact causal return attribution. Positive and negative matched sequences are not netted into this diagnostic. For continuous subwindows missed_recovery_dollars describes new within-window sales. Additional inherited_missed_recovery_at_start/end/change fields use the full prior FIFO ledger at both boundaries, retaining earlier sold lots; the change can be negative when terminal marks decline. NAV, returns and trading state remain fully inherited.',
        '- trades.csv includes fills for controls, independent episodes, full/validation parameter variants and execution variants. daily-equity.csv, position-history.csv and events.csv record controls, independent episodes and rounding/partial variants; grid daily paths are reproducible from the recorded configuration rather than duplicating hundreds of large paths in Git. episodes.csv continuous slices refer to the corresponding full-history journals.',
        '- Source/output/code hashes, fixed configuration, chronological split and completed-cycle count are in run.json; validation.md records tests. All values for incomplete episodes stop at observed last marks, not fictional future recovery.']
    (ROOT/'report.md').write_text('\n'.join(lines)+'\n')


if __name__=='__main__':
    main()
