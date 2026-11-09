"""Deterministic, per-event frozen frequency artifacts from unqualified replay.
No network; causal numerical code does not attest historical availability or rights.
"""
import gzip,json
from pathlib import Path
from datetime import timedelta,datetime,timezone
import pandas as pd
import numpy as np
from .core import canonical,sha,utc,requested_series,calendar
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/daily-shadow-postgres-v2'
FIT='2026-11-09T00:00:00+00:00'

def freeze(rows,series,name,source_hashes,fit=FIT,created_at=None):
 symbol,label,threshold,horizon=series
 eligible=sorted((r for r in rows if utc(r['maturity'])<utc(fit)),key=lambda r:r['session'])
 if not eligible:raise ValueError('NO_MATURE_LABEL_SUPPORT')
 if len({r['session'] for r in eligible})!=len(eligible):raise ValueError('DUPLICATE_LABEL_SESSION')
 if any(r['y'] not in (0,1) or r['regime'] not in ('UP','DOWN','MIXED') or r['session']>=r['maturity'][:10] for r in eligible):raise ValueError('INVALID_TRAINING_LABEL')
 groups={g:dict(n=sum(r['regime']==g for r in eligible),hits=sum(r['y'] for r in eligible if r['regime']==g)) for g in ('UP','DOWN','MIXED')}
 payload=dict(name=name,series=dict(symbol=symbol,label_type=label,threshold_pct=threshold,horizon=horizon),supported_tasks=[f'{label}:{threshold}:{horizon}'],fit_cutoff=fit,created_at=created_at,qualified=False,calibrated=False,causal_code_verified=True,training_source_qualified=False,qualification_reason='RESEARCH_REPLAY_NOT_PIT; FULL_ACTION_PRICE_HISTORY_UNVERIFIED',count_bank=dict(n=len(eligible),hits=sum(r['y'] for r in eligible),groups=groups,last_maturity=max(r['maturity'] for r in eligible),first_anchor=eligible[0]['session'],last_anchor=eligible[-1]['session']),training_rows_sha256=sha(canonical(eligible).encode()),source_hashes=source_hashes,code_sha256=sha(Path(__file__).read_bytes()+Path(__file__).with_name('core.py').read_bytes()),params=dict(beta_prior=[1,1],regime_shrinkage=20,regime_feature='QQQ_CLOSE_SMA200_AND_MOM20',availability='FOLLOWING_UTC_MIDNIGHT_REPLAY_ASSUMPTION'),score_kind='RESEARCH_UNCALIBRATED_NOT_LIVE_APPROVED')
 payload['version']='frozen-'+sha(canonical(payload).encode())
 return payload

def load_artifact(path):
 obj=json.loads(Path(path).read_text());version=obj.pop('version')
 if version!='frozen-'+sha(canonical(obj).encode()):raise ValueError('ARTIFACT_HASH_MISMATCH')
 obj['version']=version;return obj

def build():
 base=ROOT/'reports/market-drawdown-precursors-v1';manifest=json.loads((base/'data/manifest.json').read_text());source_hashes={}
 frames={};dates=calendar().sessions;qq=None
 for src in manifest['sources']:
  raw=gzip.decompress((base/src['raw_file']).read_bytes())
  if sha(raw)!=src['raw_sha256']:raise ValueError('SOURCE_HASH_MISMATCH')
  source_hashes[src['symbol']]=sha(raw);obj=json.loads(raw)['chart']['result'][0]
  ix=pd.to_datetime(obj['timestamp'],unit='s',utc=True).tz_convert('America/New_York').strftime('%Y-%m-%d')
  f=pd.DataFrame(obj['indicators']['quote'][0],index=ix)
  if not f.index.is_unique or not np.isfinite(f[['close','low']]).all().all() or (f[['close','low']]<=0).any().any():raise ValueError('INVALID_FROZEN_OHLC')
  expected=calendar().sessions_in_range(f.index[0],f.index[-1]).strftime('%Y-%m-%d').tolist()
  if list(f.index)!=expected:raise ValueError('SOURCE_CALENDAR_GAP')
  frames[src['symbol']]=f
 qq=frames['QQQ'].close
 regime=pd.Series(np.where((qq>=qq.rolling(200).mean())&(qq>qq.shift(20)),'UP',np.where((qq<qq.rolling(200).mean())&(qq<=qq.shift(20)),'DOWN','MIXED')),index=qq.index)
 portfolios=ROOT/'reports/model-portfolios-eod-v1';pl=pd.read_csv(portfolios/'labels.csv.gz')
 for src in json.loads((portfolios/'sources.json').read_text()):
  raw=gzip.decompress((portfolios/'data'/(src['symbol']+'.json.gz')).read_bytes())
  if sha(raw)!=src['raw_sha256']:raise ValueError('PORTFOLIO_SOURCE_HASH_MISMATCH')
  source_hashes['PR24_'+src['symbol']]=sha(raw)
 source_hashes['PR24_LABELS']=sha((portfolios/'labels.csv.gz').read_bytes())
 preparation=OUT/('preparation-'+sha(Path(__file__).read_bytes()+Path(__file__).with_name('core.py').read_bytes())+'.json')
 if not preparation.exists():preparation.write_text(json.dumps(dict(started_at=datetime.now(timezone.utc).isoformat(),purpose='OFFLINE_ARTIFACT_BUILD_NOT_ISSUANCE'),indent=2)+'\n')
 created_at=json.loads(preparation.read_text())['started_at']
 cache={};artifacts=[]
 for symbol,label,threshold,horizon,name in requested_series():
  key=(symbol,label,threshold,horizon)
  if key not in cache:
   rows=[]
   if symbol in 'ABC':
    for r in pl[pl.recipe==symbol].itertuples():rows.append(dict(session=r.date,maturity=(pd.Timestamp(r.maturity,tz='UTC')+pd.Timedelta(days=1)).isoformat(),y=int(r.event),regime=r.regime))
   else:
    f=frames[symbol];mark=f['low' if label=='LOW_INTRADAY' else 'close'].to_numpy();close=f.close.to_numpy()
    for i in range(199,len(f)-horizon):
     end=f.index[i+horizon];minimum=float(mark[i+1:i+horizon+1].min());rows.append(dict(session=f.index[i],maturity=(pd.Timestamp(end,tz='UTC')+pd.Timedelta(days=1)).isoformat(),y=int(minimum<=close[i]*(1-threshold/100)+close[i]*1e-12),regime=regime.loc[f.index[i]]))
   cache[key]=rows
  artifacts.append(freeze(cache[key],key,name,source_hashes,created_at=created_at))
 dest=OUT/'models';dest.mkdir(exist_ok=True)
 for m in artifacts:
  s=m['series'];file=m['version']+'.json';path=dest/file;content=canonical(m)+'\n'
  if path.exists() and path.read_text()!=content:raise ValueError('IMMUTABLE_ARTIFACT_CONFLICT')
  path.write_text(content)
 index=dict(classification='RESEARCH_PRICE_REPLAY_NOT_PIT',fit_cutoff=FIT,created_at=artifacts[0]['created_at'],requested_series=222,artifacts=len(artifacts),qualified=0,calibrated=0,live_eligible=0,source_hashes=source_hashes,models=[dict(file=str(Path('models')/(m['version']+'.json')),name=m['name'],version=m['version'],series=m['series'],n=m['count_bank']['n'],last_maturity=m['count_bank']['last_maturity']) for m in artifacts])
 (OUT/'model-index.json').write_text(json.dumps(index,indent=2)+'\n');return artifacts
if __name__=='__main__':print(f'Frozen artifacts: {len(build())}; qualified live: 0')
