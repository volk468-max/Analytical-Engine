"""Safe JSON diagnostics: readable Railway message AND machine-readable attributes."""
import contextvars,json,os,re,traceback,uuid
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit,unquote,quote

ACTIVE=contextvars.ContextVar('alpha_shadow_run',default=None)
SENSITIVE=re.compile(r'token|api[_-]?key|password|passwd|authorization|credential|secret|database_url|dsn',re.I)
URL=re.compile(r'\b[a-z][a-z0-9+.-]*://[^\s<>\"\']+',re.I)

def redact(value):
    if isinstance(value,dict):return {str(k):'[REDACTED]' if SENSITIVE.search(str(k)) else redact(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [redact(v) for v in value]
    if not isinstance(value,str):return value
    text=URL.sub('[URL_REDACTED]',value)
    secrets=[]
    for key in ('EODHD_API_TOKEN','ALPHA_SHADOW_DATABASE_URL','ALPHA_VAULT_KEY','PGPASSWORD','POSTGRES_PASSWORD'):
        secret=os.environ.get(key)
        if secret:
            secrets.extend([secret,quote(secret,safe='')])
            if '://' in secret:
                try:
                    pwd=urlsplit(secret).password
                    if pwd:secrets.extend([pwd,unquote(pwd)])
                except ValueError:pass
    for secret in sorted(set(secrets),key=len,reverse=True):text=text.replace(secret,'[REDACTED]')
    text=re.sub(r'(?i)(bearer\s+)[^\s,;]+',r'\1[REDACTED]',text)
    text=re.sub(r'(?i)((?:api[_-]?token|password|authorization|api[_-]?key)\s*[=:]\s*)[^\s,;&]+',r'\1[REDACTED]',text)
    return text

def exception_fields(exc):
    code=getattr(exc,'code',None)
    if not code or not re.fullmatch(r'[A-Z0-9_]{1,96}',str(code)):code=type(exc).__name__.upper()
    states=[];current=exc;seen=set()
    while current is not None and id(current) not in seen:
        seen.add(id(current));sqlstate=getattr(current,'sqlstate',None)
        detail=('DATABASE_ERROR SQLSTATE='+str(sqlstate)) if hasattr(current,'sqlstate') else str(current)
        primary=getattr(getattr(current,'diag',None),'message_primary',None)
        if primary and re.fullmatch(r'[A-Z0-9_]{1,96}',primary):detail+=' '+primary
        states.append(type(current).__name__+': '+redact(detail)[:500])
        if current.__traceback__:
            states.extend('  at '+Path(frame.f_code.co_filename).name+':'+str(line)+' in '+frame.f_code.co_name for frame,line in traceback.walk_tb(current.__traceback__))
        current=current.__cause__ or (current.__context__ if not current.__suppress_context__ else None)
    return dict(exception_type=type(exc).__name__,error_code=redact(str(code)),traceback=redact('\n'.join(states))[:12000])

class RunAudit:
    def __init__(self):
        self.run_id=str(uuid.uuid4());self.persister=None;self.http_responses=0;self.http_failures=0;self.http_status_counts={}
    def emit(self,*,persist=True,persist_first=False,**fields):
        if fields.get('phase')=='HTTP' and fields.get('status') in ('RESPONSE','ERROR'):
            self.http_responses+=fields['status']=='RESPONSE';self.http_failures+=fields['status']=='ERROR'
            code=str(fields.get('http_status') or 'NO_HTTP_RESPONSE');self.http_status_counts[code]=self.http_status_counts.get(code,0)+1
        record=redact(dict(fields,run_id=self.run_id,timestamp=datetime.now(timezone.utc).isoformat()))
        record['level']='error' if record.get('status') in ('ERROR','FAILED') else ('warning' if record.get('status')=='PARTIAL_FAILURE' else 'info')
        record['message']=str(record.get('message') or (str(record.get('phase','DAILY'))+' '+str(record.get('status','EVENT'))))
        if persist and persist_first and self.persister:self.persister(record)
        print(json.dumps(record,sort_keys=True,allow_nan=False),flush=True)
        if persist and not persist_first and self.persister:self.persister(record)
        return record
    def http_summary(self):return dict(http_responses=self.http_responses,http_failures=self.http_failures,http_status_counts=self.http_status_counts)
    def failure(self,phase,exc,*,persist=True):return self.emit(phase=phase,status='ERROR',persist=persist,**exception_fields(exc))

def observe(**fields):
    audit=ACTIVE.get()
    if audit:return audit.emit(persist=False,**fields)
