"""Mandatory control gate. Raises on any mismatch before long-run economics."""
import csv,hashlib,json,subprocess,tempfile,shutil,importlib.util
from pathlib import Path
from research.historical_sell_buyback.signals import reconstruct
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'reports/historical-sell-buyback-v1';C=R/'control/pr10'
def main():
    man=json.loads((R/'control/source-manifest.json').read_text())
    for x in man['files']:assert hashlib.sha256((C/x['path']).read_bytes()).hexdigest()==x['sha256']
    base=C/'reports/fixed-5pct-buyback-v1';inp=json.loads((base/'inputs/inputs.json').read_text())
    daily,events=reconstruct(inp['prices'],'2026-09-01','2026-11-02')
    expected=[r['date'] for r in csv.DictReader((base/'signals-used.csv').open())]
    assert [r['date'] for r in events]==expected,([r['date'] for r in events],expected)
    js="const A=require(process.argv[1]),fs=require('fs');console.log(JSON.stringify(A.market(JSON.parse(fs.readFileSync(process.argv[2]))).rows));"
    original=json.loads(subprocess.check_output(['node','-e',js,str(base/'inputs/pr9-audit.cjs'),str(base/'inputs/inputs.json')],text=True))
    for a,b in zip(daily,original):
        assert a['date']==b['date'] and a['sector_flag']==b['sector_flag']
        for k in ['sector_ret5','qqq_ret5']:assert abs(a[k]-b[k])<1e-14
    assert len(daily)==len(original)==44
    adapted_checks=0
    adapted=ROOT/'research/historical_sell_buyback/engine.py'
    if adapted.exists():
        from research.historical_sell_buyback.engine import simulate
        spec=importlib.util.spec_from_file_location('archived_pr10_engine',C/'research/fixed_5pct_buyback/engine.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        calendar={r['date']:r for r in csv.DictReader((base/'inputs/session-calendar.csv').open())}
        for symbol in ['AMD','NVDA','MU','TSM','AVGO','AMAT','AMZN','META','PLTR','LRCX','NBIS']:
            bars=sorted([dict(r) for r in inp['prices'] if r['symbol']==symbol and r['date']>='2026-09-01'],key=lambda r:r['date'])
            for r in bars:r['dividend']=sum(a['amount'] for a in inp['actions'] if a['symbol']==symbol and a['kind']=='dividends' and a['date']==r['date'])
            for fraction in [0,.05,.1]:
                for delay in [1,2]:
                    a=simulate(bars,events,calendar,fraction=fraction,delay=delay);b=module.simulate(bars,events,calendar,fraction=fraction,delay=delay)
                    assert a==b,(symbol,fraction,delay,'adapted default policy changed');adapted_checks+=1
    # Run the entire untouched PR10 source in an isolated temp copy, never modifying frozen copies.
    with tempfile.TemporaryDirectory(prefix='alpha-historical-control-') as td:
        t=Path(td);shutil.copytree(C,t,dirs_exist_ok=True)
        subprocess.run(['python','-B','-m','research.fixed_5pct_buyback.run'],cwd=t,check=True,capture_output=True)
        subprocess.run(['python','-B','-m','research.fixed_5pct_buyback.report'],cwd=t,check=True,capture_output=True)
        generated=['comparison.csv','sensitivity.csv','stock-results.csv','sales.csv','limit-orders.csv','buybacks.csv','trades.csv','cycles.csv','daily-stock-equity.csv','daily-portfolio-equity.csv','opportunity-cost.csv','signals-used.csv','run.json','sale-quality.csv','waiting-summary.csv']
        for name in generated:assert (base/name).read_bytes()==(t/'reports/fixed-5pct-buyback-v1'/name).read_bytes(),name
    result=dict(gate_passed=True,source_commit=man['source_commit'],source_files_verified=len(man['files']),signal_dates=expected,sector_daily_rows_equal=44,exact_PR10_generated_files_equal=len(generated),adapted_engine_control_cases_equal=adapted_checks,long_economics_authorized_only_after_this_gate=True)
    (R/'control/gate.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
