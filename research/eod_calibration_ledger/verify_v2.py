"""Offline full replay verification; never contacts providers or production."""
import hashlib,json,socket
from unittest.mock import patch
import pandas as pd
from .preliminary import OUT,run,load_prices,CLASS
from .continuity_v2 import run as continuity

def verify():
 files=sorted(OUT.glob('*.csv'))+sorted(OUT.glob('*.csv.gz'))
 before={p.name:(pd.read_csv(p),hashlib.sha256(p.read_bytes()).hexdigest()) for p in files}
 with patch('socket.socket',side_effect=AssertionError('NETWORK_FORBIDDEN')):
  run();continuity()
 checks=[]
 for name,(expected,digest) in before.items():
  p=OUT/name;actual=pd.read_csv(p)
  pd.testing.assert_frame_equal(expected,actual,check_exact=False,rtol=1e-11,atol=1e-8)
  checks.append(dict(file=name,rows=len(actual),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),byte_identical=hashlib.sha256(p.read_bytes()).hexdigest()==digest,numeric_match=True))
 manifest=json.loads((OUT/'run-manifest.json').read_text());assert not manifest['qualified'];assert manifest['classification']==CLASS
 v=dict(mode='OFFLINE_REAL_FROZEN_REPLAY_NOT_PIT',network_forbidden=True,files=checks,all_numeric_match=True,all_byte_identical=all(x['byte_identical'] for x in checks),model_qualified=False,production_touched=False)
 (OUT/'verification-v2.json').write_text(json.dumps(v,indent=2)+'\n');print('Offline preliminary replay verification PASS')
if __name__=='__main__':verify()
