"""Reproduce frozen v3 economic research offline; no optimization or service calls."""
import csv
import gzip
import hashlib
import json
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from aae.backtest.cli import write_csv
from aae.backtest.simulator import ExecutionConfig
from .risk_v3_features import load_pack
from .risk_v3_evaluation import entry_outcomes
from .risk_v3_economic import EconomicConfig, simulate, performance
from .risk_v3_economic_analysis import signal_economics, economic_metrics

ROOT=Path('reports/risk-v3-economic')
SOURCE=Path('reports/risk-signal-v3')
SYMBOLS=('AMD','NVDA','MU')
END='2026-10-22'
PERIODS={'2023-2026':('2023-01-01',END),'2023-2024':('2023-01-01','2024-12-31'),
         '2025':('2025-01-01','2025-12-31'),'2026':('2026-01-01',END),
         'SepOct2026':('2026-09-01',END)}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_inputs():
    bars,_,manifest=load_pack()
    provenance=json.loads((SOURCE/'run.json').read_text())
    for name,digest in provenance['source_sha256'].items():
        path=Path(name)
        if not path.exists() and '/aae/' in name:path=Path('aae/'+name.split('/aae/',1)[1])
        if sha(path)!=digest:raise ValueError('Changed frozen v3 source: '+name)
    for name in ('daily-signals.jsonl.gz','fold-selection.csv','entry-outcomes.csv','events.csv'):
        if sha(SOURCE/name)!=provenance['output_sha256'][name]:raise ValueError('Changed v3 output: '+name)
    folds={int(r['test_year']):r for r in csv.DictReader((SOURCE/'fold-selection.csv').open()) if r['variant']=='C'}
    if set(folds)!={2023,2024,2025,2026}:raise ValueError('Missing frozen walk-forward fold')
    for year,fold in folds.items():
        if fold['training_end']>=f'{year}-01-01':raise ValueError('Training label leakage')
    if folds[2026]['configuration']!='sensitive' or folds[2026]['training_end']!='2025-12-31':
        raise ValueError('2026 configuration not frozen C/sensitive')
    signals={s:[] for s in SYMBOLS}
    with gzip.open(SOURCE/'daily-signals.jsonl.gz','rt') as stream:
        for line in stream:
            s=json.loads(line)
            if s['mode']=='walk_forward' and s['variant']=='C':
                if s['configuration']!=folds[int(s['date'][:4])]['configuration']:
                    raise ValueError('Signal disagrees with frozen fold')
                signals[s['symbol']].append(s)
    stocks={s:[b for b in bars if b.symbol==s] for s in SYMBOLS}
    dividends={s:{} for s in SYMBOLS};checks=[]
    normalized=list(csv.DictReader(Path('data/risk-signal-v3/bars.csv').open()))
    for symbol in SYMBOLS:
        entry=next(x for x in manifest['sources'] if x['symbol']==symbol)
        raw=json.loads((Path('data/risk-signal-v3')/entry['raw_file']).read_text())['chart']['result'][0]
        if raw.get('events',{})!=entry['reported_corporate_actions']:
            raise ValueError('Corporate-action manifest mismatch')
        by_date={datetime.fromtimestamp(t,timezone.utc).date().isoformat():i for i,t in enumerate(raw['timestamp'])}
        q=raw['indicators']['quote'][0]
        normalized_symbol=[r for r in normalized if r['symbol']==symbol]
        for row in normalized_symbol:
            i=by_date[row['open_at'][:10]]
            for key in ('open','high','low','close','volume'):
                if float(row[key])!=q[key][i]:raise ValueError('Raw/normalized OHLCV mismatch')
        series=stocks[symbol];lookup={b.close_at.date().isoformat():b for b in series}
        if len(lookup)!=len(series):raise ValueError('Duplicate stock session')
        for b in series:
            local=b.open_at.astimezone(ZoneInfo('America/New_York'))
            if local.weekday()>=5 or (local.hour,local.minute)!=(9,30):
                raise ValueError('Invalid regular session open')
            if b.available_at.date()<=b.close_at.date():raise ValueError('Publication not next date')
        for s in signals[symbol]:
            b=lookup[s['date']]
            if abs(s['indicators']['close']-b.close)>1e-8 or s['decision_at']!=b.available_at.isoformat():
                raise ValueError('Signal/price timestamp mismatch')
        for action in raw.get('events',{}).get('dividends',{}).values():
            date=datetime.fromtimestamp(action['date'],timezone.utc).date().isoformat()
            if not isinstance(action['amount'],(int,float)) or action['amount']<0:
                raise ValueError('Invalid dividend')
            if series[0].close_at.date().isoformat()<=date<=END:
                if date not in lookup:raise ValueError('Dividend has no session')
                dividends[symbol][date]=action['amount']
        split_checks=[]
        for action in raw.get('events',{}).get('splits',{}).values():
            date=datetime.fromtimestamp(action['date'],timezone.utc).date().isoformat()
            if date not in lookup:continue
            i=next(i for i,b in enumerate(series) if b.close_at.date().isoformat()==date)
            ratio=series[i].open/series[i-1].close
            if not .4<ratio<2.5:raise ValueError('Potential unadjusted split jump')
            split_checks.append(dict(date=date,split_ratio=action['splitRatio'],adjusted_open_to_previous_close=ratio,
                share_multiplier_applied=1,check='No obvious split-sized discontinuity; not independent verification'))
        checks.append(dict(symbol=symbol,bars=len(series),signals=len(signals[symbol]),
            dividends=len(dividends[symbol]),splits=split_checks,raw_ohlcv_reconciled=True,
            opens_checked_new_york=True,payment_dates_available=False,
            early_closes='Original PR5 +6.5h close assumption retained; early-close availability conservatively delayed',
            independent_price_or_dividend_vintage_verified=False))
    false_labels=outcome_labels(signals,'2023-01-01',END)
    return stocks,signals,dividends,false_labels,checks,folds


def outcome_labels(signals,start,end):
    # Reuse the unchanged PR #5 label rule, censoring at THIS account's endpoint.
    # Labels remain evaluation-only; simulate never receives this mapping.
    return {(symbol,r['date']):r for symbol,series in signals.items()
            for r in entry_outcomes(series,start,end)}


def scenario_id(cfg):
    return f'{cfg.recovery}-size{cfg.tranche*100:g}-critical{int(cfg.critical_extra)}-delay{cfg.execution.delay_sessions}-div{int(cfg.include_dividends)}'


def tag(rows,**context):
    return [dict(r,**context) for r in rows]


def run_metrics(result,baseline,false_labels=None):
    cfg=result['config'];d=result['daily'];b=baseline['daily']
    p=performance(d,cfg.execution.initial_cash,result['bars'][0].open_at.isoformat(),trades=result['trades'])
    bp=performance(b,cfg.execution.initial_cash,baseline['bars'][0].open_at.isoformat(),trades=baseline['trades'])
    economics=economic_metrics(result,baseline)
    rows=signal_economics(result,false_labels)
    false=[r for r in rows if r.get('sale_date') and r.get('reason')=='REDUCE' and r.get('false_reduce_followed_by_growth') is True]
    complete_false=[r for r in rows if r.get('sale_date') and r.get('reason')=='REDUCE' and r.get('false_reduce_followed_by_growth') is not None]
    growth=[r for r in rows if r.get('sale_date') and r.get('reason')=='REDUCE' and r.get('forward_20_pct') is not None]
    return dict(p,**economics,return_difference_pp=p['return_pct']-bp['return_pct'],
        max_drawdown_reduction_pp=p['max_drawdown_pct']-bp['max_drawdown_pct'],
        sold_before_growth_20_pct=sum(r['forward_20_pct']>0 for r in growth)/len(growth)*100 if growth else None,
        sold_before_growth_20_classified_lots=len(growth),
        false_reduce_lots=len(false),false_reduce_classified_lots=len(complete_false),
        false_reduce_lot_pct=len(false)/len(complete_false)*100 if complete_false else None,
        loss_from_false_reduce_usd=sum(max(0,-r['total_net_contribution']) for r in false),
        incomplete_recovery=bool(d[-1]['share_deficit']>1e-8))




def drawdown_rows(results):
    events=[r for r in csv.DictReader((SOURCE/'events.csv').open()) if r['mode']=='walk_forward' and r['variant']=='C']
    output=[]
    for (symbol,scenario),result in results.items():
        if scenario=='BUY_HOLD':continue
        baseline=results[(symbol,'BUY_HOLD')]
        ds={r['date']:r for r in result['daily']};bs={r['date']:r for r in baseline['daily']}
        for event in [r for r in events if r['symbol']==symbol]:
            start=max(event['peak_date'],result['daily'][0]['date']);end=event['end_date']
            d=[r for r in result['daily'] if start<=r['date']<=end]
            b=[r for r in baseline['daily'] if start<=r['date']<=end]
            if not d:continue
            peak=float(event['peak_close']);trough=event['trough_date']
            recovery=next((x['date'] for x in result['daily'] if x['date']>trough and x['close']>=peak),None)
            m=performance(d,d[0]['equity'],d[0]['date']+'T00:00:00+00:00')
            bm=performance(b,b[0]['equity'],b[0]['date']+'T00:00:00+00:00')
            output.append(dict(symbol=symbol,scenario=scenario,peak_date=event['peak_date'],
                first_reduce=event['first_reduce'],first_10pct_date=event['drawdown_10_date'],
                price_trough_date=trough,price_drawdown_pct=event['observed_drawdown_pct'],
                price_peak_recovery_date=recovery,price_recovery_censored=recovery is None,
                event_end=end,left_censored=event['left_censored'],
                tactical_event_return_pct=m['return_pct'],buy_hold_event_return_pct=bm['return_pct'],
                tactical_event_max_drawdown_pct=m['max_drawdown_pct'],buy_hold_event_max_drawdown_pct=bm['max_drawdown_pct'],
                drawdown_reduction_pp=m['max_drawdown_pct']-bm['max_drawdown_pct'],
                peak_share_fraction=ds[start]['shares_fraction'],trough_share_fraction=ds.get(trough,ds[start])['shares_fraction']))
    return output


def plots(results):
    import os
    os.environ.setdefault('MPLCONFIGDIR','/tmp/alpha-risk-economic-mpl')
    os.environ.setdefault('XDG_CACHE_HOME','/tmp/alpha-risk-economic-cache')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(3,2,figsize=(14,11))
    ddfig,ddaxes=plt.subplots(3,1,figsize=(12,10))
    for i,symbol in enumerate(SYMBOLS):
        for scenario,color in [('BUY_HOLD','black')]+[(scenario_id(EconomicConfig(recovery=r)),c) for r,c in zip(('HOLD3','TREND3','TIME10'),('tab:blue','tab:orange','tab:green'))]:
            result=results[(symbol,scenario)];d=result['daily'];dates=[datetime.fromisoformat(r['date']) for r in d]
            label='Buy & Hold' if scenario=='BUY_HOLD' else result['config'].recovery
            axes[i,0].plot(dates,[r['equity'] for r in d],label=label,color=color,lw=1)
            axes[i,1].plot(dates,[r['shares_fraction']*100 for r in d],label=label,color=color,lw=.8)
            peak=100000;dd=[]
            for r in d:peak=max(peak,r['equity']);dd.append((r['equity']/peak-1)*100)
            ddaxes[i].plot(dates,dd,label=label,color=color,lw=1)
        axes[i,0].set_title(symbol+' total equity ($)');axes[i,1].set_title(symbol+' original shares held (%)')
        ddaxes[i].set_title(symbol+' equity drawdown (%)')
        for ax in (*axes[i],ddaxes[i]):ax.grid(alpha=.25);ax.legend(fontsize=8)
    for figure in (fig,ddfig):figure.autofmt_xdate();figure.tight_layout()
    fig.savefig(ROOT/'equity-and-position.png',dpi=140);ddfig.savefig(ROOT/'drawdowns.png',dpi=140)
    plt.close('all')


def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    stocks,signals,dividends,false,quality,folds=load_inputs()
    (ROOT/'data-quality.json').write_text(json.dumps(quality,indent=2)+'\n')
    configs=[EconomicConfig(recovery=r,critical_extra=c) for r in ('HOLD3','TREND3','TIME10') for c in (True,False)]
    summary=[];trades=[];daily=[];economics=[];matches=[];decisions=[];cancelled=[];full={}
    for period,(start,end) in PERIODS.items():
        period_labels=outcome_labels(signals,start,end)
        for symbol in SYMBOLS:
            base=simulate(stocks[symbol],signals[symbol],start,end,buy_hold=True,dividends=dividends[symbol])
            context=dict(account_mode='independent',symbol=symbol,period=period,scenario='BUY_HOLD',recovery=None,tranche=0,critical_extra=False,delay_sessions=1)
            bm=performance(base['daily'],100000,base['bars'][0].open_at.isoformat(),trades=base['trades'])
            summary.append(dict(bm,**context,equity_difference_vs_buy_hold=0,return_difference_pp=0,max_drawdown_reduction_pp=0))
            trades.extend(tag(base['trades'],**context));daily.extend(tag(base['daily'],**context))
            if period=='2023-2026':full[(symbol,'BUY_HOLD')]=base
            for cfg in configs:
                result=simulate(stocks[symbol],signals[symbol],start,end,cfg,dividends=dividends[symbol])
                context=dict(account_mode='independent',symbol=symbol,period=period,scenario=scenario_id(cfg),recovery=cfg.recovery,tranche=cfg.tranche,critical_extra=cfg.critical_extra,delay_sessions=cfg.execution.delay_sessions)
                summary.append(dict(run_metrics(result,base,period_labels),**context))
                trades.extend(tag(result['trades'],**context));daily.extend(tag(result['daily'],**context))
                economics.extend(tag(signal_economics(result,period_labels),**context))
                matches.extend(tag(result['matches'],**context));decisions.extend(tag(result['decisions'],**context))
                cancelled.extend(tag(result['cancellations'],**context))
                if period=='2023-2026':full[(symbol,scenario_id(cfg))]=result
    # Slices retain original account quantities, cash, queued policy state and earlier costs.
    # Their initial capitals differ; retain endpoint delta AND period P&L delta explicitly.
    for period,(start,end) in PERIODS.items():
        if period=='2023-2026':continue
        for (symbol,scenario),result in full.items():
            d=[r for r in result['daily'] if start<=r['date']<=end]
            prior=[r for r in result['daily'] if r['date']<start]
            initial=prior[-1]['equity'] if prior else 100000
            t=[t for t in result['trades'] if start<=t['date']<=end]
            m=performance(d,initial,d[0]['date']+'T00:00:00+00:00',trades=t)
            baseline=full[(symbol,'BUY_HOLD')]
            bd=[r for r in baseline['daily'] if start<=r['date']<=end]
            bp=[r for r in baseline['daily'] if r['date']<start]
            binit=bp[-1]['equity'] if bp else 100000
            bm=performance(bd,binit,bd[0]['date']+'T00:00:00+00:00')
            cfg=result['config']
            summary.append(dict(m,account_mode='inherited',symbol=symbol,period=period,scenario=scenario,
                recovery=None if scenario=='BUY_HOLD' else cfg.recovery,tranche=0 if scenario=='BUY_HOLD' else cfg.tranche,
                critical_extra=False if scenario=='BUY_HOLD' else cfg.critical_extra,delay_sessions=1,
                equity_difference_vs_buy_hold=d[-1]['equity']-bd[-1]['equity'],
                period_pnl_difference_vs_buy_hold=(d[-1]['equity']-initial)-(bd[-1]['equity']-binit),
                return_difference_pp=m['return_pct']-bm['return_pct'],
                max_drawdown_reduction_pp=m['max_drawdown_pct']-bm['max_drawdown_pct']))
    sensitivity=[]
    for symbol in SYMBOLS:
        base=full[(symbol,'BUY_HOLD')]
        for recovery in ('HOLD3','TREND3','TIME10'):
            for critical in (True,False):
                for size in (.05,.10,.15,.25):
                    for delay in (1,2,3):
                        cfg=EconomicConfig(recovery=recovery,tranche=size,critical_extra=critical,
                            execution=ExecutionConfig(initial_cash=100000,delay_sessions=delay))
                        result=full.get((symbol,scenario_id(cfg))) or simulate(stocks[symbol],signals[symbol],'2023-01-01',END,cfg,dividends=dividends[symbol])
                        sensitivity.append(dict(run_metrics(result,base,false),symbol=symbol,scenario=scenario_id(cfg),
                            recovery=recovery,tranche=size,critical_extra=critical,delay_sessions=delay,include_dividends=True))
                # Price-only check isolates restrictions/entitlements from trading P&L.
                cfg=EconomicConfig(recovery=recovery,critical_extra=critical,include_dividends=False)
                base_price=simulate(stocks[symbol],signals[symbol],'2023-01-01',END,cfg,buy_hold=True)
                result=simulate(stocks[symbol],signals[symbol],'2023-01-01',END,cfg)
                sensitivity.append(dict(run_metrics(result,base_price,false),symbol=symbol,scenario=scenario_id(cfg),
                    recovery=recovery,tranche=.10,critical_extra=critical,delay_sessions=1,include_dividends=False))
    for row in sensitivity:
        reference=next(r for r in sensitivity if r['symbol']==row['symbol'] and r['recovery']==row['recovery'] and r['critical_extra']==row['critical_extra'] and r['delay_sessions']==row['delay_sessions'] and r['include_dividends']==row['include_dividends'] and r['tranche']==.10)
        row['difference_per_1pct_tranche_usd']=row['equity_difference_vs_buy_hold']/(row['tranche']*100)
        row['deviation_from_linear_10pct_usd']=row['equity_difference_vs_buy_hold']-reference['equity_difference_vs_buy_hold']*row['tranche']/.10
    protection=drawdown_rows(full)
    outputs={'summary.csv':summary,'trades.csv':trades,'daily-equity.csv':daily,
        'signal-economics.csv':economics,'recovery-matches.csv':matches,
        'signal-events.csv':decisions,'cancelled-orders.csv':cancelled,
        'recovery-comparison.csv':[r for r in summary if r['scenario']!='BUY_HOLD'],
        'drawdown-protection.csv':protection,'sensitivity.csv':sensitivity,
        'october-2026.csv':[r for r in economics if r['period'] in ('2023-2026','2026','SepOct2026') and r['signal_date']>='2026-10-01']}
    for name,rows in outputs.items():
        fields=('order_id','signal_date','cancelled_at','reason','symbol','period','scenario') if not rows else ()
        write_csv(ROOT/name,rows,fields=fields)
    plots(full)
    report(summary,economics,sensitivity,quality,folds)
    paths=[Path(__file__),Path('aae/research/risk_v3_economic.py'),Path('aae/research/risk_v3_economic_analysis.py'),ROOT/'protocol.md',Path('tests/test_risk_v3_economic.py'),Path('aae/research/requirements-economic.txt'),SOURCE/'run.json',Path('data/risk-signal-v3/manifest.json')]
    metadata=dict(schema_version=1,cutoff=END,source_sha256={str(p):sha(p) for p in paths},
        frozen_signal_sha256=sha(SOURCE/'daily-signals.jsonl.gz'),
        output_sha256={p.name:sha(p) for p in ROOT.iterdir() if p.name not in ('run.json','protocol.md')},
        counts={name:len(rows) for name,rows in outputs.items()},
        principal_configuration=asdict(EconomicConfig()),signal_folds=folds,
        historical_vintage_verified=False,all_accounts_attribution_reconciled=True)
    (ROOT/'run.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(json.dumps(metadata['counts']))


def fmt(value,places=2):
    return '—' if value is None else f'{value:,.{places}f}'


def report(summary,economics,sensitivity,quality,folds):
    lines=['# Risk Signal v3 — economic backtest','',
        'Research-only execution of unchanged PR #5 C walk-forward signals. No merges, deployments, live orders or production changes. Protocol was committed before economic calculations; no policy/size winner is selected by 2026 returns. The principal size remains 10%.','',
        '## Data and accounting','',
        'Frozen Yahoo AMD/NVDA/MU prices and corporate-action responses from PR #5, warm-up 2020–2022, trading 2023 through 22 October 2026. 23 October is excluded. No new market observations or invented prices. Raw OHLCV/action manifest and adjusted split continuity reconciled in data-quality.json; original sources/retrieval times/hashes remain in data/risk-signal-v3/.','',
        'Use one provider split-adjusted OHLC/share/dividend basis. The NVDA 2024 10:1 split is not applied again. Gross dividends accrue to pre-ex-date-open holdings in a separate non-spendable receivable because payment dates are unavailable. Total cash = spendable cash + receivable; NAV = total cash + shares*close. Price-only sensitivity is explicit. Taxes, interest, market impact and terminal liquidation are excluded. Provider dividends/adjustments are not independently verified; payment and vintage limitations prevent a definitive investable total-return claim.','',
        'Opens are checked at 09:30 America/New_York; full OHLCV matches frozen raw responses. PR #5 uses conservative next-midnight availability and assumes 6.5-hour sessions: early closes are delayed, not traded early. There is no independently attested historical publication archive or exchange-calendar completeness audit. These are retrospective diagnostic results, not proven investment effectiveness.','',
        '## Fixed policy','',
        'Full rules: [protocol.md](protocol.md). First high-risk entry sells 10% original shares; first CRITICAL adds 10%, including a combined 20% order for direct CRITICAL. Rearm only after three valid WATCH/HOLD sessions. One sale permission of each type per episode; REDUCE↔CRITICAL chatter does not repeatedly sell. Minimum 50% original shares. The no-CRITICAL control isolates the first reduction.','',
        'HOLD3 restores after three consecutive HOLD; TREND3 after three consecutive WATCH/HOLD with close>MA20 and positive MA20 five-session slope; TIME10 after ten consecutive WATCH/HOLD. Once confirmed, restore one tranche per session, next-open execution, bounded by cash and original shares. New risk/invalid data cancels queued buys; firm queued sells stay scheduled. Buy & Hold shares/costs at inception match Tactical. Costs are 5 bps fee plus 5 bps adverse slippage, fractional shares, no leverage. Initial observation of high risk may qualify in a fresh account and is explicitly flagged.','',
        'Frozen signal configurations (unchanged): '+', '.join(f"{year}: C/{f['configuration']} trained through {f['training_end']}" for year,f in sorted(folds.items()))+'.','',
        '## Full continuous test: 2023–22 October 2026','',
        '| Stock | Policy | Return % | CAGR % | Max DD % | Sharpe | Final NAV $ | Δ vs B&H $ | Fees+slippage $ | Profitable completed lots % |',
        '|---|---|---|---|---|---|---|---|---|---|']
    for r in summary:
        if r['period']!='2023-2026':continue
        label='Buy & Hold' if r['scenario']=='BUY_HOLD' else r['recovery']+(' +CRITICAL' if r['critical_extra'] else ' REDUCE only')
        lines.append('| '+' | '.join([r['symbol'],label,fmt(r['return_pct']),fmt(r['cagr_pct']),fmt(r['max_drawdown_pct']),fmt(r['sharpe']),fmt(r['final_equity']),fmt(r['equity_difference_vs_buy_hold']),fmt(r['trading_costs']),fmt(r.get('profitable_completed_lot_pct'))])+' |')
    lines += ['', '![Equity and original share fractions](equity-and-position.png)','', '![Equity drawdowns](drawdowns.png)','',
        'Sharpe uses daily total-equity returns including inception costs, sample SD, risk-free=0 and sqrt(252). CAGR is omitted for periods shorter than 365 calendar days. No portfolio aggregation across correlated stocks. Independent accounts for every subperiod start at $100,000 and reset execution state; continuous full-period results inherit state across years. Summary account_mode=inherited gives slices of that same continuous account, with inherited initial capital and a separate period_pnl_difference_vs_buy_hold; its final equity difference includes earlier years. Their dollar outcomes must not be treated as the same experiment.','',
        '## Independent period controls: principal HOLD3, CRITICAL enabled','',
        '| Period | Stock | Tactical return % | Δ return vs B&H, pp | DD reduction, pp | Δ final NAV $ | Ending missing shares |',
        '|---|---|---|---|---|---|---|']
    for r in summary:
        if r['scenario']==scenario_id(EconomicConfig()) and r['period']!='2023-2026' and r['account_mode']=='independent':
            lines.append('| '+' | '.join([r['period'],r['symbol'],fmt(r['return_pct']),fmt(r['return_difference_pp']),fmt(r['max_drawdown_reduction_pp']),fmt(r['equity_difference_vs_buy_hold']),fmt(r['final_share_deficit'])])+' |')
    lines += ['', '## October 2026: full continuous account, HOLD3, CRITICAL enabled','',
        '| Stock | Signal / kind | Close | Sale date / fill | Next closing trough / price | Extra fall % | Full lot buyback / avg fill | Net contribution $ | Completed? |',
        '|---|---|---|---|---|---|---|---|---|']
    for r in economics:
        if r['period']=='2023-2026' and r['scenario']==scenario_id(EconomicConfig()) and r['signal_date']>='2026-10-01':
            lines.append('| '+' | '.join([r['symbol'],r['signal_date']+' '+r['reason'],fmt(r['signal_close']),
                str(r.get('sale_date') or r.get('execution_status'))+' / '+fmt(r.get('sale_fill')),
                str(r.get('next_local_min_date','—'))+' / '+fmt(r.get('next_local_min_close')),
                fmt(r.get('additional_decline_after_fill_pct')),str(r.get('full_lot_recovery_date') or 'OPEN')+' / '+fmt(r.get('average_buy_fill')),
                fmt(r.get('total_net_contribution')),str(r['cycle_completed'])])+' |')
    lines += ['', 'The table includes CRITICAL add-ons and blocked entries. Open-lot contribution is an unrealized relative mark at October 22, not booked trading profit. october-2026.csv also includes independent 2026 and Sep–Oct accounts and all recovery controls. A confirmed local trough is a closing low <=previous close and <next close; where unavailable, the observed minimum is right-censored. No minimum or forward label is an execution input.','',
        '## Quantitative answers: principal 10%, HOLD3, CRITICAL enabled','']
    for symbol in SYMBOLS:
        r=next(r for r in summary if r['symbol']==symbol and r['period']=='2023-2026' and r['scenario']==scenario_id(EconomicConfig()))
        controls=[x for x in summary if x['symbol']==symbol and x['period']=='2023-2026' and x['scenario']!='BUY_HOLD' and x['critical_extra']]
        lines += [f"- **{symbol}:** Δ final NAV {fmt(r['equity_difference_vs_buy_hold'])} USD; Δ return {fmt(r['return_difference_pp'])} pp; maximum-drawdown reduction {fmt(r['max_drawdown_reduction_pp'])} pp. {fmt(r['positive_trough_protection_lot_pct'])}% of confirmed-trough lots have positive actual net protection; {fmt(r['profitable_completed_lot_pct'])}% of completed lots are profitable; grouping direct-CRITICAL components into a single first-REDUCE event gives {fmt(r['profitable_completed_reduce_signal_pct'])}% profitable completed REDUCE signals (n={r['completed_reduce_signals']}). Sale followed by +20-session price growth: {fmt(r['sold_before_growth_20_pct'])}% of {r['sold_before_growth_20_classified_lots']} classified REDUCE lots. Stricter false-growth REDUCE labels: {r['false_reduce_lots']}/{r['false_reduce_classified_lots']} classified lots ({fmt(r['false_reduce_lot_pct'])}%), associated negative net contribution {fmt(r['loss_from_false_reduce_usd'])} USD. Missed gross recovery growth {fmt(r['missed_growth'])} USD (overlapping opportunity measure, not an extra NAV deduction). Recovery-rule Δ NAV range {fmt(min(x['equity_difference_vs_buy_hold'] for x in controls))} to {fmt(max(x['equity_difference_vs_buy_hold'] for x in controls))} USD. Ending deficit {fmt(r['final_share_deficit'])} adjusted-basis shares; receivable {fmt(r['final_dividend_receivable'])} USD."]
    lines += ['', 'Protection at a retrospective trough measures contribution at that date; it is not the final round-trip outcome. actual_trough_protection_sum sums different, potentially overlapping dates and is NOT portfolio profit. Exact final reconciliation uses realized lot contributions + open lot marks (both already net of their allocated missed dividends), with each dividend counted once; this equals Tactical NAV minus Buy & Hold in every simulation. Closed profitable lots exclude unfinished lots. Average reduced-spell duration includes the observed length of an open spell (a censored lower bound); even a small unrecovered fee-related share deficit keeps that spell open. Quantity-weighted matched absence is separately reported, so it is not confused with signal-state duration. Repeated reductions can share one REDUCE entry; signal IDs and component lots are retained to avoid treating components as independent predictions.','',
        '## Size, latency and corporate-action sensitivity','',
        '| Stock | Tranche % | Delay sessions | Δ NAV $ | Deviation from linear 10% scaling $ |',
        '|---|---|---|---|---|']
    for r in sensitivity:
        if r['recovery']=='HOLD3' and r['critical_extra'] and r['include_dividends'] and (r['delay_sessions']==1 or r['tranche']==.10):
            lines.append('| '+' | '.join([r['symbol'],fmt(r['tranche']*100,0),str(r['delay_sessions']),fmt(r['equity_difference_vs_buy_hold']),fmt(r['deviation_from_linear_10pct_usd'])])+' |')
    lines += ['', 'sensitivity.csv retains all 216 size/recovery/CRITICAL/latency configurations plus 18 price-only controls. Cash constraints, the 50% floor, finite tranches and restored-share deficits can make scaling nonlinear. No best-size recommendation is inferred. Delay 1 is next open; delays 2/3 add one/two sessions. Missing/last-day executions are never manufactured.','',
        '## Interpretation and limits','',
        'The economic criterion is final NAV after costs alongside drawdown, not merely the ability to flag a decline. Positive protection followed by costly re-entry can destroy the earlier benefit; remaining below the original share count also reduces future participation. Compare all three recovery rules and the CRITICAL-disabled controls rather than presenting the best retrospective return as independent validation. Numerical trade-offs above quantify whether protection compensates lost returns for each stock and policy; no utility preference for drawdown versus return is assumed.','',
        'There is no established universal economic advantage over Buy & Hold from this retrospective sample. Even a positive individual result is diagnostic: the signal catalogue and execution policies were developed after outcomes became observable. Independent verified price/action/publication vintages, actual dividend payment dates, a reserved future holdout, additional instruments, and execution/market-impact validation are needed before any investment-effectiveness claim.','',
        '## Artifacts and reproduction','',
        '`python -m aae.research.risk_v3_economic_study` runs offline. summary/recovery-comparison cover all independent periods; trades, recovery-matches, daily-equity, signal-events and cancelled-orders audit primary/control executions. Sensitivity contains summary outputs for every fixed combination and is reproducible with the same runner. signal-economics includes blocked/unfilled signals as well as actual lots. drawdown-protection includes every original C walk-forward >=10% event, true old-peak recovery dates and censored episodes. Never substitute a trailing-20 high for recovery of an old peak. validation.md lists checks and historical limitations; run.json records hashes.']
    extra=['## Dividend convention sensitivity: principal HOLD3','',
        '| Stock | Δ NAV including restricted dividends $ | Δ NAV price-only $ | Difference $ |',
        '|---|---|---|---|']
    for symbol in SYMBOLS:
        on=next(r for r in sensitivity if r['symbol']==symbol and r['recovery']=='HOLD3' and r['critical_extra'] and r['tranche']==.10 and r['delay_sessions']==1 and r['include_dividends'])
        off=next(r for r in sensitivity if r['symbol']==symbol and r['recovery']=='HOLD3' and r['critical_extra'] and not r['include_dividends'])
        a=on['equity_difference_vs_buy_hold'];b=off['equity_difference_vs_buy_hold']
        extra.append(f'| {symbol} | {fmt(a)} | {fmt(b)} | {fmt(a-b)} |')
    extra.append('')
    at=lines.index('## Interpretation and limits')
    lines[at:at]=extra
    principal=[r for r in summary if r['period']=='2023-2026' and r['scenario']==scenario_id(EconomicConfig())]
    controls=[r for r in summary if r['period']=='2023-2026' and r['scenario']!='BUY_HOLD']
    negative=sum(r['equity_difference_vs_buy_hold']<0 for r in controls)
    finding=f"In this source vintage, {negative}/{len(controls)} full-period primary recovery/CRITICAL controls finish below Buy & Hold. Principal HOLD3 drawdown reduction is {fmt(min(r['max_drawdown_reduction_pp'] for r in principal))}–{fmt(max(r['max_drawdown_reduction_pp'] for r in principal))} pp, at a cumulative-return cost of {fmt(min(-r['return_difference_pp'] for r in principal))}–{fmt(max(-r['return_difference_pp'] for r in principal))} pp. Smaller drawdowns do not compensate lost terminal wealth under a terminal-NAV objective. An investor's preference between return and drawdown cannot be inferred from these numbers alone."
    at=lines.index('## Interpretation and limits')+2
    lines[at:at]=[finding,'']
    (ROOT/'report.md').write_text('\n'.join(lines)+'\n')


if __name__=='__main__':main()
