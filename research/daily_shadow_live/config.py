import os,json,base64,hashlib
from urllib.parse import urlsplit,unquote
from pathlib import Path
from research.daily_shadow.artifacts import load_artifact
from research.daily_shadow.core import canonical,sha
PROJECT='73fc59d1-8aaf-480d-bc33-313cbdf428e6'
ENVIRONMENT='eb43b87d-7d51-46a6-829d-cd0c5b68e0f2'
WORKER='4a395356-42c7-4489-a051-5789bf51e206'
ROOT=Path(__file__).resolve().parents[2]
class ConfigurationError(Exception):pass

def identity(env=None):
 e=os.environ if env is None else env
 if (e.get('RAILWAY_PROJECT_ID'),e.get('RAILWAY_ENVIRONMENT_ID'),e.get('RAILWAY_SERVICE_ID'))!=(PROJECT,ENVIRONMENT,WORKER):raise ConfigurationError('WRONG_RAILWAY_ISOLATION_IDENTITY')
 if e.get('ALPHA_LIVE_TRADING','false').lower()!='false':raise ConfigurationError('TRADING_FORBIDDEN')
 if e.get('ALPHA_RUN_MODE')!='RESEARCH_FORECAST':raise ConfigurationError('RESEARCH_MODE_REQUIRED')

def dsn():
 value=os.environ.get('ALPHA_SHADOW_DATABASE_URL','')
 if not value:raise ConfigurationError('MISSING_ISOLATED_DATABASE_REFERENCE')
 parsed=urlsplit(value)
 if parsed.path!='/alpha_shadow_research':raise ConfigurationError('WRONG_DATABASE_NAME')
 return value

def vault_key(url):
 explicit=os.environ.get('ALPHA_VAULT_KEY')
 if explicit:return explicit.encode()
 password=unquote(urlsplit(url).password or '')
 if not password:raise ConfigurationError('VAULT_KEY_OR_BOOTSTRAP_SECRET_REQUIRED')
 # A DB dump alone does not contain this environment secret; rotation needs rekey.
 return base64.urlsafe_b64encode(hashlib.scrypt(password.encode(),salt=(PROJECT+':vault-v4').encode(),n=2**14,r=8,p=1,dklen=32))

def models():
 index=json.loads((ROOT/'reports/daily-shadow-postgres-v2/model-index.json').read_text());out=[]
 for item in index['models']:
  m=load_artifact(ROOT/'reports/daily-shadow-postgres-v2'/item['file'])
  if m.get('fixture') or m.get('qualified') or m.get('calibrated'):raise ConfigurationError('EXPECTED_GENUINE_UNVALIDATED_FROZEN_ARTIFACT')
  out.append(m)
 if len(out)!=222:raise ConfigurationError('INCOMPLETE_MODEL_REGISTRY')
 return out
