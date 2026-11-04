"""Build two explicitly survivor-selected proxies from frozen PR11 inputs."""
import base64,csv,gzip,hashlib,json
from pathlib import Path
from datetime import date,datetime,time,timedelta
from zoneinfo import ZoneInfo
from research.breadth_data_audit.engine import BreadthEngine,divergence
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'reports/breadth-data-audit-v1';I=R/'inputs'
SEMIS=['AMD','NVDA','MU','TSM','AVGO','AMAT','LRCX'];STOCKS=SEMIS+['AMZN','META','PLTR','NBIS']
def write(name,rs):
    with (R/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in rs for k in r)),lineterminator='\n');w.writeheader();w.writerows(rs)
def main():
    manifest=R/'input-manifest.json'
    if manifest.exists():
        for path,sha in json.loads(manifest.read_text()).items():
            if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=sha:raise ValueError('input hash mismatch: '+path)
    q=json.loads(gzip.decompress(base64.b64decode((I/'prices.json.gz.b64').read_text())));raw=[dict(zip(q['columns'],r)) for r in q['rows']];c=json.loads((I/'calendar.json').read_text());cal=[]
    for d in c['warmup_sessions']:
        dt=datetime.combine(date.fromisoformat(d),time(16),ZoneInfo('America/New_York'));cal.append(dict(date=d,close_at=dt.isoformat()))
    cal+=c['sessions'];ds=[x['date'] for x in cal];index={d:i for i,d in enumerate(ds)};data=[];memberships=[]
    for universe,syms,benchmark in [('FIXED_SEVEN_SEMIS_PROXY',SEMIS,'^SOX'),('FIXED_ELEVEN_CURRENT_SURVIVORS_PROXY',STOCKS,'QQQ')]:
        ms=[]
        for d in sorted({q['eligible'][s] for s in syms}):
            m=dict(effective_date=d,available_at=d+'T00:00:00+00:00',members=sorted(s for s in syms if q['eligible'][s]<=d),pit_verified=False);ms.append(m);memberships.append(dict(universe=universe,**m))
        meta=dict(universe=universe,membership_kind='RETROSPECTIVE_CURRENT_SURVIVOR_SELECTION_NOT_INDEX',price_basis=q['price_basis'],source='PR11 archived Yahoo chart',source_version=q['source_commit'],membership_history_complete=False,publication_times_verified=False,corporate_actions_verified=False,calendar_verified=False,security_ids_verified=False)
        eng=BreadthEngine(raw,cal,ms,meta);hist={};bench={x['date']:x['close'] for x in raw if x['security_id']==benchmark}
        for sess in c['sessions']:
            d=sess['date'];decision=(date.fromisoformat(d)+timedelta(days=1)).isoformat()+'T00:00:00+00:00';row=eng.calculate(d,decision);i=index[d];pd=ds[i-20] if i>=20 else None;prev=hist.get(pd)
            bw=eng.window(benchmark,i,21,decision)
            ret=100*(bw[-1]['close']/bw[0]['close']-1) if bw else None
            row.update(benchmark=benchmark,index_return20_pct=ret,breadth_change20_pp=row['pct_above_ma50']-prev['pct_above_ma50'] if prev and row['members']==prev['members'] and row['pct_above_ma50'] is not None and prev['pct_above_ma50'] is not None else None,breadth_divergence20=divergence(row,prev,ret) if prev else None,stockcharts_comparison='NOT_PERFORMED_NO_AUTHORIZED_SAME_UNIVERSE_SERIES')
            if row['breadth_divergence20'] is None:
                row['historical_backtest_eligible']=False;row['quality_reasons']+=';DIVERGENCE_UNAVAILABLE'
            hist[d]=row;data.append(row)
    for x in data:
        for k,v in x.items():
            if isinstance(v,float):x[k]=round(v,8)
    write('breadth-prototype.csv',data);(I/'membership-proxies.json').write_text(json.dumps(memberships,indent=2)+'\n')
    summary={u:dict(rows=len(xs),first=xs[0]['date'],last=xs[-1]['date'],historical_eligible=sum(x['historical_backtest_eligible'] for x in xs),ma50_available=sum(x['pct_above_ma50'] is not None for x in xs),ma200_available=sum(x['pct_above_ma200'] is not None for x in xs),extrema_available=sum(x['new_highs'] is not None for x in xs)) for u in sorted({x['universe'] for x in data}) if (xs:=[x for x in data if x['universe']==u])}
    (R/'run.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
    files=[p for p in I.iterdir() if p.is_file()];(R/'input-manifest.json').write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)},indent=2)+'\n')
if __name__=='__main__':main()
