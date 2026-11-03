"""Mandatory control gate. Raises on any mismatch before long-run economics."""
import csv,hashlib,json,subprocess,tempfile,shutil
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
    # Run the entire untouched PR10 source in an isolated temp copy, never modifying frozen copies.
    with tempfile.TemporaryDirectory(prefix='alpha-historical-control-') as td:
        t=Path(td);shutil.copytree(C,t,dirs_exist_ok=True)
        subprocess.run(['python','-B','-m','research.fixed_5pct_buyback.run'],cwd=t,check=True,capture_output=True)
        subprocess.run(['python','-B','-m','research.fixed_5pct_buyback.report'],cwd=t,check=True,capture_output=True)
        generated=['comparison.csv','sensitivity.csv','stock-results.csv','sales.csv','limit-orders.csv','buybacks.csv','trades.csv','cycles.csv','daily-stock-equity.csv','daily-portfolio-equity.csv','opportunity-cost.csv','signals-used.csv','run.json','sale-quality.csv','waiting-summary.csv']
        for name in generated:assert (base/name).read_bytes()==(t/'reports/fixed-5pct-buyback-v1'/name).read_bytes(),name
    result=dict(gate_passed=True,source_commit=man['source_commit'],source_files_verified=len(man['files']),signal_dates=expected,sector_daily_rows_equal=44,exact_PR10_generated_files_equal=len(generated),long_economics_authorized_only_after_this_gate=True)
    (R/'control/gate.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
