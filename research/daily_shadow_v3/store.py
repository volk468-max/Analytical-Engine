"""Separate licensed payload plane. No raw OHLC enters the append-only journal."""
import json,uuid,hashlib
from pathlib import Path
from cryptography.fernet import Fernet
from research.daily_shadow.core import canonical
from research.daily_shadow.store import Store as LegacyStore

class ResearchStore:
    def __init__(self,dsn,key):
        self.legacy=LegacyStore(dsn);self.cipher=Fernet(key)
    def connect(self):return self.legacy.connect()
    def register(self,permit,contract_id=None):
        cid=contract_id or uuid.uuid4()
        with self.connect() as c:return c.execute('select alpha_research_v3.register_contract(%s,%s::jsonb)',(cid,canonical(permit.to_dict()))).fetchone()[0]
    def permit(self,cid):
        from .legal import Permit
        with self.connect() as c:
            body=c.execute('select body from alpha_research_v3.contracts where id=%s',(cid,)).fetchone()[0]
            if c.execute("select exists(select 1 from alpha_research_v3.lifecycle where contract_id=%s and action='OFFBOARD_REQUESTED')",(cid,)).fetchone()[0]:body['revoked']=True
        return Permit(**body)
    def payload(self,cid,snapshot,expires):
        encrypted=self.cipher.encrypt(canonical(snapshot.private_payload()).encode())
        with self.connect() as c:return c.execute('select alpha_research_v3.save_payload(%s,%s,%s,%s,%s)',(uuid.uuid4(),cid,encrypted,expires,snapshot.revision)).fetchone()[0]
    def private(self,ref):
        with self.connect() as c:encrypted=c.execute('select alpha_research_v3.load_payload(%s)',(ref,)).fetchone()[0]
        return json.loads(self.cipher.decrypt(encrypted))
    @staticmethod
    def append(c,kind,key,body):
        return c.execute('select alpha_research_v3.append(%s,%s,%s,%s)',(uuid.uuid4(),kind,key,canonical(body))).fetchone()[0]
    def forecasts(self,key,rows,models,cid,anchor_ref,snapshot,run_mode='SYNTHETIC',*,baselines=None,baseline_cutoff=None):
        if run_mode not in ('SYNTHETIC','RESEARCH_FORECAST'):raise ValueError('NO_VALIDATED_TRADING_OR_BACKFILL_ROUTE')
        from .engine import complete_models
        models=complete_models(models)
        ids=[]
        with self.connect() as c:
            c.execute('select pg_advisory_xact_lock(280003)')
            mids={(m['name'],m['version']):LegacyStore.append(c,'model',m['name']+':'+m['version'],m) for m in models}
            for row in rows:
                b=dict(row);b.update(contract_id=str(cid),model_id=str(mids[(b.pop('model_name'),b.pop('model_version'))]),run_mode=run_mode,anchor_ref=str(anchor_ref) if anchor_ref else None,source_fixture=snapshot.fixture,source_revision=snapshot.revision)
                ek=key+':'+':'.join(str(b[k]) for k in ('symbol','label_type','threshold_pct','horizon','model_id'))
                fid=self.append(c,'FORECAST',ek,b);ids.append(fid)
                if baselines is not None and b['status']=='RESEARCH_FORECAST':
                    p,n=baselines[tuple(b[k] for k in ('symbol','label_type','threshold_pct','horizon'))]
                    c.execute('select alpha_operations_v4.baseline(%s,%s,%s,%s)',(fid,p,n,baseline_cutoff))
        return ids
    def outcome(self,key,body):
        with self.connect() as c:return self.append(c,'OUTCOME',key,body)
    def correction(self,key,forecast_id,ref,snapshot):
        with self.connect() as c:return self.append(c,'CORRECTION',key,dict(forecast_id=str(forecast_id),replacement_payload_ref=str(ref),source_revision=snapshot.revision,observed_at=snapshot.retrieved_at,reason='SOURCE_REVISION_FORECAST_UNCHANGED'))
    def offboard(self,cid,receipt='SYNTHETIC_OFFBOARD_REQUEST'):
        with self.connect() as c:return c.execute('select alpha_research_v3.offboard(%s,%s)',(cid,receipt)).fetchone()[0]
    def expire(self):
        with self.connect() as c:return c.execute('select alpha_research_v3.expire_payloads()').fetchone()[0]
    def metrics(self):
        from .metrics import paired_metrics
        with self.connect() as c:
            rows=c.execute("""select j.body,m.body->>'name',o.body from alpha_research_v3.forecasts f
                join alpha_research_v3.journal j on j.id=f.id
                join alpha_shadow_v1.audit_events m on m.id=f.model_id
                join lateral (select e.body from alpha_research_v3.outcomes v join alpha_research_v3.journal e on e.id=v.id where v.forecast_id=f.id order by e.seq desc limit 1) o on true""").fetchall()
        return paired_metrics([dict(b,model_name=name,fixture=b.get('source_fixture',True),outcome_status=o['status'],outcome=o['outcome']) for b,name,o in rows])
    def verify(self):
        with self.connect() as c:rows=c.execute('select kind,event_key,body_text,previous_hash,record_hash from alpha_research_v3.journal order by seq').fetchall()
        prev=None
        for kind,key,text,prior,digest in rows:
            if prior!=prev or hashlib.sha256(((prev or '')+'|'+kind+'|'+key+'|'+text).encode()).hexdigest()!=digest:return False
            prev=digest
        return True

def restore_allowed(manifest_contracts,fresh_authoritative_active,*,authority_fresh=False):
    # A restored backup's own contract table is NOT a fresh license authority.
    if not authority_fresh:return False
    return set(manifest_contracts)<=set(fresh_authoritative_active)
