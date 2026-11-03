"""Optional PR9 policy: unchanged source, only study-start constant extended."""
import json,subprocess,csv,hashlib,tempfile
from pathlib import Path
from research.historical_sell_buyback.prepare import R,STOCKS,write
from research.historical_sell_buyback.run import padded_daily,aggregate
from research.historical_sell_buyback.stats import metrics,annual
def main():
    p=json.loads((R/'prepared.json').read_text());raw=(R/'control/pr10/reports/fixed-5pct-buyback-v1/inputs/pr9-audit.cjs').read_text()
    needle='const START="2026-09-01"';assert raw.count(needle)==1
    src=raw.replace(needle,'const START="2021-01-01"',1);adapter=R/'prior-period-only.cjs';adapter.write_text(src)
    inp=dict(prices=[dict(x,symbol='SOX' if x['symbol']=='^SOX' else x['symbol']) for x in p['prices'] if x['symbol']!='NBIS' or x['date']>=p['eligible']['NBIS']],actions=p['actions'],vix=[dict(date=x['date'],close=x['close'],available_at=x['available_at']) for x in p['prices'] if x['symbol']=='^VIX'],rates=[],data_end='2026-11-02')
    tmp=tempfile.TemporaryDirectory(prefix='alpha-prior-input-');input_path=Path(tmp.name)/'inputs.json';input_path.write_text(json.dumps(inp,separators=(',',':'))+'\n')
    js="const fs=require('fs'),A=require(process.argv[1]),p=JSON.parse(fs.readFileSync(process.argv[2])),m=A.market(p);for(const f of [.05,.1])for(const s of A.STOCKS){let z=A.simulate(m.g[s],m.all,p.actions.filter(x=>x.symbol===s),f,1);console.log(JSON.stringify({symbol:s,fraction:f,...z}));}"
    proc=subprocess.Popen(['node','-e',js,str(adapter),str(input_path)],stdout=subprocess.PIPE,text=True);results={}
    for line in proc.stdout:
        z=json.loads(line);results[z['fraction'],z['symbol']]=z
    assert proc.wait()==0;tmp.cleanup()
    cal=[x['date'] for x in p['calendar']];variants={'RESERVED11':STOCKS,'COMPARABLE10':[s for s in STOCKS if p['eligible'][s]==cal[0]]}
    stats=[];years=[];stock=[];daily=[];trades=[]
    for f in [.05,.1]:
        name='PR9_ORIGINAL_F'+str(f);padded={}
        for s in STOCKS:
            z=results[f,s];padded[s]=padded_daily(cal,z['daily']);sm=metrics(z['daily']);sm.update(z['summary']);sm.update(scenario=name,symbol=s,mode='PR9_ORIGINAL',primary=True,fraction=f,threshold=None,delay=1,fee_rate=.0005,slip_rate=.0005,stress=False,final_nominal_shares=z['daily'][-1]['shares']);stock.append(sm);trades.extend(dict(scenario=name,**t) for t in z['trades'])
        for variant,members in variants.items():
            ds=aggregate(padded,members);m=metrics(ds);xs=[results[f,s]['summary'] for s in members];m.update(scenario=name,variant=variant,primary=True,mode='PR9_ORIGINAL',fraction=f,threshold=None,delay=1,fee_rate=.0005,slip_rate=.0005,stress=False,sales=sum(x['sales'] for x in xs),closed_buybacks=None,open_lots=None,fees=sum(x['fees'] for x in xs)/len(members),slippage=sum(x['slippage'] for x in xs)/len(members),cash=ds[-1]['cash'],stock_value=ds[-1]['stock_value'],dividend_receivable=ds[-1]['dividend_receivable']);stats.append(m);years.extend(dict(scenario=name,variant=variant,primary=True,**y) for y in annual(ds));daily.extend(dict(scenario=name,variant=variant,**d) for d in ds)
    core=[x for x in csv.DictReader((R/'portfolio-comparison.csv').open()) if x['mode']!='PR9_ORIGINAL'];corestock=[x for x in csv.DictReader((R/'stock-performance.csv').open()) if x['mode']!='PR9_ORIGINAL']
    for x in stats:
        same=[z for z in core if z['variant']==x['variant']];bh=next(z for z in same if float(z['fraction'])==0);sell=next(z for z in same if z['mode']=='sale_only' and float(z['fraction'])==x['fraction']);x['excess_vs_buyhold']=x['final_equity']-float(bh['final_equity']);x['excess_vs_sale_only']=x['final_equity']-float(sell['final_equity'])
    for x in stock:
        bh=next(z for z in corestock if z['symbol']==x['symbol'] and float(z['fraction'])==0 and float(z['fee_rate'])==.0005);x['excess_vs_buyhold']=x['final_equity']-float(bh['final_equity'])
    write('prior-portfolio.csv',stats);write('prior-annual.csv',years);write('prior-stock.csv',stock);write('prior-trades.csv',trades);write('prior-daily.csv',daily)
    write('portfolio-comparison.csv',core+stats);write('stock-performance.csv',corestock+stock)
    oldyears=[x for x in csv.DictReader((R/'annual-performance.csv').open()) if not x['scenario'].startswith('PR9_ORIGINAL')];write('annual-performance.csv',oldyears+years)
    run=json.loads((R/'run.json').read_text());run['prior_strategy_status']='UNCHANGED_POLICY_PERIOD_ONLY_ADAPTER_REPLAYED';run['prior_source_sha256']=hashlib.sha256(raw.encode()).hexdigest();run['prior_adapter_sha256']=hashlib.sha256(src.encode()).hexdigest();(R/'run.json').write_text(json.dumps(run,indent=2)+'\n')
    (R/'prior-validation.json').write_text(json.dumps(dict(source='PR9 frozen source from PR10 snapshot',only_source_change='Study start2026-09-01 ->2021-01-01; no rule/threshold changes',full_original_fundamental_engine_replayed=False,policy_only=True,vix_and_rates_do_not_enter_sale_or_recovery_rules=True),indent=2)+'\n')
    print([(x['variant'],x['fraction'],round(x['final_equity'],2)) for x in stats])
if __name__=='__main__':main()
