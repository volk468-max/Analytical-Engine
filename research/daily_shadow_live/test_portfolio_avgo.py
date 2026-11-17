import copy,os,unittest,uuid
from research.daily_shadow.core import canonical,sha
from research.daily_shadow_v3.legal import fixture_permit
from . import vol,risk_forecast_daily as rf,ensemble_daily as ens,market_precursors_daily as mdp
from .portfolio import SYMBOLS,UNIVERSE_REVISION
from .test_vol import sample,SESSION,NOW
MODULES=(vol,rf,ens,mdp)

def bundle():
 s=sample('AVGO')
 for symbol in ('SPY','QQQ','SOXX'):
  s.bars[symbol]=copy.deepcopy(s.bars['AVGO']);s.currency[symbol]='USD';s.splits[symbol]=[];s.dividends[symbol]=[]
 return s

def bank(s):
 out=[]
 for module in MODULES:
  task=module.series(('AVGO',))[0];m=module.artifact(module.frame(s,'AVGO'),task,SESSION+'T00:00:00+00:00',NOW,s.revision,fixture=True);out.append((module,m))
 return out

class PortfolioRevisionTests(unittest.TestCase):
 def test_consistent_active_manifest_and_preserved_legacy_data_cutoff(self):
  self.assertEqual(SYMBOLS,('ANET','NVDA','AMD','CRWD','AVGO','GOOG','GS','META','MU','LRCX'))
  for module,n in zip(MODULES,(120,120,120,156)):
   self.assertEqual(module.MANIFEST['universe_revision_sha256'],UNIVERSE_REVISION);tasks=module.series();self.assertEqual(len(tasks),n);self.assertNotIn('NBIS',{r['symbol'] for r in tasks});self.assertEqual(sum(r['symbol']=='AVGO' for r in tasks),12)
  self.assertGreaterEqual(vol.frame(sample('NBIS'),'NBIS').index[0],vol.NBIS_START)
 def test_avgo_has_actual_fits_in_each_model_with_synthetic_fixture(self):
  s=bundle()
  for module,m in bank(s):
   self.assertFalse(m['unavailable']);row=module.rows(SESSION,NOW,s,[m],fixture_permit(),reviewed=True)[0];self.assertIsNotNone(row['probability_raw']);self.assertEqual(row['symbol'],'AVGO')

@unittest.skipUnless(os.environ.get('ALPHA_SHADOW_TEST_DSN'),'Disposable local SQL required')
class PortfolioRevisionSQLTests(unittest.TestCase):
 def test_sql_accepts_avgo_and_rejects_retired_nbis_for_all_four_models(self):
  import psycopg
  from cryptography.fernet import Fernet
  from research.daily_shadow_v3.store import ResearchStore
  url=os.environ['ALPHA_SHADOW_TEST_DSN'];info=psycopg.conninfo.conninfo_to_dict(url)
  if info.get('host') not in ('127.0.0.1','localhost') or info.get('dbname')!='alpha_shadow_research':raise ValueError('LOCAL_ONLY')
  store=ResearchStore(url,Fernet.generate_key());permit=fixture_permit();cid=store.register(permit);s=bundle();s.revision=sha(str(uuid.uuid4()).encode());ref=store.payload(cid,s,permit.raw_until)
  for module,m in bank(s):
   rows=module.rows(SESSION,NOW,s,[m],permit,reviewed=True);key='AVGO_TEST:'+str(uuid.uuid4());ids=store.forecasts(key,rows,[m],cid,ref,s);self.assertEqual(len(ids),1)
   self.assertEqual(ids,store.forecasts(key,rows,[m],cid,ref,s))
   oldtask=dict(m['series'],symbol='NBIS');old=module.unavailable(oldtask,NOW,'RETIRED_OWNER_UNIVERSE');oldrows=module.rows(SESSION,NOW,None,[old],permit,reason='RETIRED_OWNER_UNIVERSE')
   with self.assertRaises(psycopg.Error):store.forecasts(key+':NBIS',oldrows,[old],cid,None,s)
  self.assertTrue(store.verify())
