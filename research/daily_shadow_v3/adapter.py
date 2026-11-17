"""EODHD adapter. Credentials injected, no networking until an explicit reviewed gate.
Fixtures are handcrafted; no source payload is written to Git or to immutable audit.
"""
import json,os,hashlib,math,time,socket
from email.utils import parsedate_to_datetime
from dataclasses import dataclass
from datetime import datetime,timezone,timedelta
from urllib.parse import urlencode
from urllib.request import Request,build_opener,HTTPRedirectHandler
from urllib.error import HTTPError,URLError
from zoneinfo import ZoneInfo
import pandas as pd
from research.daily_shadow.core import calendar,utc

SYMBOLS=('SPY','QQQ','SOXX','AMD','NVDA','MU')
MAPPING={s:s+'.US' for s in SYMBOLS}

class VendorError(Exception):
    def __init__(self,code,*,http_status=None):
        super().__init__(code);self.code=code;self.http_status=http_status
class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

class HTTPTransport:
    fixture=False
    def __init__(self,*,max_attempts=3,timeout=20,sleeper=None,observer=None,deadline=None):
        if not 1<=max_attempts<=3 or not 0<timeout<=20:raise ValueError('INVALID_HTTP_RETRY_BOUNDS')
        self.max_attempts=max_attempts;self.timeout=timeout;self.sleeper=sleeper or time.sleep;self.observer=observer;self.deadline=deadline
    def emit(self,**fields):
        if self.observer:self.observer(phase='HTTP',**fields)
    def get(self,path,query,secret):
        # Never log URL/query/headers. HTTP errors do not expose the token-bearing URL.
        url='https://eodhd.com'+path+'?'+urlencode(dict(query,api_token=secret));endpoint=path.split('?',1)[0]
        for attempt in range(1,self.max_attempts+1):
            if self.deadline is not None and time.monotonic()>=self.deadline:raise VendorError('RUN_DEADLINE_EXCEEDED')
            started=time.monotonic();status=None;retry=False;delay=min(2**(attempt-1),5)
            try:
                timeout=self.timeout if self.deadline is None else min(self.timeout,max(.01,self.deadline-started))
                with build_opener(NoRedirect).open(Request(url,headers={'User-Agent':'AlphaOS isolated research adapter'}),timeout=timeout) as response:
                    status=response.status;body=response.read(8*1024*1024+1)
                    if len(body)>8*1024*1024:raise VendorError('RESPONSE_TOO_LARGE')
                    self.emit(status='RESPONSE',endpoint=endpoint,http_status=status,http_attempt=attempt,duration_ms=round((time.monotonic()-started)*1000))
                    return body
            except HTTPError as exc:
                kind=type(exc).__name__;status=exc.code;code='HTTP_'+str(status);retry=status in (429,500,502,503,504)
                retry_after=exc.headers.get('Retry-After') if exc.headers else None
                if retry_after:
                    try:delay=max(0,float(retry_after))
                    except ValueError:
                        try:delay=max(0,(parsedate_to_datetime(retry_after)-datetime.now(timezone.utc)).total_seconds())
                        except (ValueError,TypeError,OverflowError):retry=False
                if not math.isfinite(delay) or delay>30:retry=False # Do not retry EARLIER than a long Retry-After.
            except (TimeoutError,socket.timeout) as exc:kind=type(exc).__name__;code='TRANSPORT_TIMEOUT';retry=True
            except URLError as exc:kind=type(exc).__name__;code='TRANSPORT_TIMEOUT' if isinstance(exc.reason,TimeoutError) else 'TRANSPORT_CONNECTION_FAILURE';retry=True
            except (ConnectionError,OSError) as exc:kind=type(exc).__name__;code='TRANSPORT_CONNECTION_FAILURE';retry=True
            except VendorError as exc:
                self.emit(status='ERROR',endpoint=endpoint,http_status=status,http_attempt=attempt,error_code=exc.code,exception_type=type(exc).__name__);raise
            except Exception as exc:kind=type(exc).__name__;code='TRANSPORT_FAILURE';retry=False
            self.emit(status='ERROR',endpoint=endpoint,http_status=status,http_attempt=attempt,error_code=code,exception_type=kind,duration_ms=round((time.monotonic()-started)*1000))
            if not retry or attempt==self.max_attempts:raise VendorError(code,http_status=status) from None
            if self.deadline is not None and time.monotonic()+delay>=self.deadline:raise VendorError('RUN_DEADLINE_EXCEEDED')
            self.emit(status='RETRY',endpoint=endpoint,http_status=status,http_attempt=attempt,retry_delay_seconds=delay)
            self.sleeper(delay)

@dataclass(repr=False)
class Snapshot:
    provider:str
    session:str
    retrieved_at:str|None
    publication_at:str|None
    fixture:bool
    legal_reason:str|None
    bars:dict
    splits:dict
    dividends:dict
    currency:dict
    raw_responses:dict
    revision:str|None
    source_uris:list
    basis:str='RAW_AS_TRADED_OHLC; VOLUME_SPLIT_ADJUSTED; ADJUSTED_CLOSE_TOTAL_RETURN'

    def __repr__(self):return f'Snapshot(provider={self.provider}, fixture={self.fixture}, legal_reason={self.legal_reason})'

    @property
    def source_status(self):return 'BLOCKED' if self.legal_reason else ('UNQUALIFIED_FIXTURE' if self.fixture else 'UNREVIEWED_REAL_INPUTS')

    def private_payload(self):
        return dict(provider=self.provider,session=self.session,bars=self.bars,splits=self.splits,dividends=self.dividends,currency=self.currency,raw_responses={k:v.decode('utf-8') for k,v in self.raw_responses.items()},basis=self.basis,revision=self.revision,source_uris=self.source_uris,retrieved_at=self.retrieved_at,publication_at=self.publication_at)

def date_only(value):
    if not isinstance(value,str) or len(value)!=10:raise VendorError('INVALID_SESSION_DATE')
    try:d=datetime.strptime(value,'%Y-%m-%d').date()
    except ValueError:raise VendorError('INVALID_SESSION_DATE') from None
    if d.isoformat()!=value:raise VendorError('INVALID_SESSION_DATE')
    return value

def finite(value):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):raise VendorError('NONFINITE_PRICE')
    return float(value)

def ratio(value):
    try:
        parts=value.split('/')
        if len(parts)!=2:raise ValueError()
        a,b=map(float,parts)
        if not math.isfinite(a) or not math.isfinite(b) or min(a,b)<=0:raise ValueError()
        return a/b
    except Exception:raise VendorError('INVALID_SPLIT_RATIO') from None

def normalized_prefix(rows,events,asof):
    """As-of split-only prices. Never use total-adjusted-close ratio for low/OHLC."""
    out=[]
    for row in rows:
        if row['date']>asof:continue
        factor=math.prod(e['factor'] for e in events if row['date']<e['date']<=asof)
        out.append(dict(row,**{k:row[k]/factor for k in ('open','high','low','close')},basis='SPLIT_ONLY_AS_OF'))
    return out

def future_anchor_units(value,anchor_session,observation_session,events):
    return value*math.prod(e['factor'] for e in events if anchor_session<e['date']<=observation_session)

def issuance_gate(session,issued,permit):
    try:
        date_only(session);stamp=utc(issued);ny=stamp.astimezone(ZoneInfo('America/New_York'))
        if not calendar().is_session(pd.Timestamp(session)):return 'WEEKEND_OR_HOLIDAY'
        if ny.date().isoformat()!=session:return 'STALE_OR_BACKDATED_SESSION'
        if stamp<=calendar().session_close(pd.Timestamp(session)).to_pydatetime():return 'BEFORE_OFFICIAL_CLOSE'
        if (ny.hour,ny.minute)<(20,30):return 'BEFORE_CONSERVATIVE_FINALIZATION_WINDOW'
        if not permit.finalization_verified:return 'PROVIDER_FINALIZATION_NOT_VERIFIED'
        return None
    except (ValueError,TypeError):return 'INVALID_UTC_OR_SESSION'

class EODHDAdapter:
    def __init__(self,permit,transport=None,clock=None,network_approved=False,history_start=None,symbols=None):
        self.symbols=tuple(SYMBOLS if symbols is None else symbols)
        if not self.symbols or len(set(self.symbols))!=len(self.symbols) or any(not __import__('re').fullmatch(r'[A-Z][A-Z0-9.-]{0,9}',s) for s in self.symbols):raise ValueError('INVALID_SYMBOL_UNIVERSE')
        self.permit=permit;self.transport=transport or HTTPTransport();self.clock=clock or (lambda:datetime.now(timezone.utc));self.network_approved=network_approved;self.history_start=date_only(history_start) if history_start else None

    def collect(self,session):
        date_only(session);fixture=bool(self.transport.fixture);start_time=self.clock().isoformat()
        reason=self.permit.reason(start_time,fixture=fixture)
        if self.permit.provider!='EODHD':reason='PROVIDER_CONTRACT_MISMATCH'
        # No secret-value inspection or outbound request while the legal gate is closed.
        if reason:return Snapshot('EODHD',session,None,None,fixture,reason,{},{},{},{},{},None,[])
        secret=os.environ.get('EODHD_API_TOKEN')
        if not secret:return Snapshot('EODHD',session,None,None,fixture,'MISSING_CREDENTIALS',{},{},{},{},{},None,[])
        if not fixture and not self.network_approved:raise VendorError('OUTBOUND_ACCESS_NOT_AUTHORIZED')
        raw={};uris=[]
        def get(path,params):
            key=path+'?'+urlencode(params)
            try:b=self.transport.get(path,params,secret)
            except VendorError:raise
            except Exception:raise VendorError('TRANSPORT_FAILURE') from None
            if sum(map(len,raw.values()))+len(b)>16*1024*1024:raise VendorError('BUNDLE_TOO_LARGE')
            raw[key]=b;uris.append('https://eodhd.com'+key)
            try:return json.loads(b)
            except (ValueError,UnicodeError):raise VendorError('INVALID_JSON') from None
        metadata=get('/api/exchange-symbol-list/US',{'fmt':'json'})
        if not isinstance(metadata,list):raise VendorError('INVALID_SYMBOL_METADATA')
        bycode={r.get('Code'):r for r in metadata if isinstance(r,dict)};bars={};splits={};dividends={};currency={}
        since=self.history_start or (datetime.strptime(session,'%Y-%m-%d')-timedelta(days=400)).date().isoformat()
        if since>session:raise VendorError('INVALID_HISTORY_START')
        for symbol in self.symbols:
            mapped=symbol+'.US'
            if bycode.get(symbol,{}).get('Currency')!='USD':raise VendorError('CURRENCY_OR_SYMBOL_NOT_VERIFIED')
            currency[symbol]='USD';params={'from':since,'to':session,'fmt':'json'}
            prices=get('/api/eod/'+mapped,dict(params,period='d'));se=get('/api/splits/'+mapped,params);de=get('/api/div/'+mapped,params)
            if not all(isinstance(x,list) for x in (prices,se,de)):raise VendorError('INVALID_RESPONSE_SCHEMA')
            converted=[]
            for r in prices:
                if not isinstance(r,dict) or not {'date','open','high','low','close','volume','adjusted_close'}<=set(r):raise VendorError('INVALID_BAR_SCHEMA')
                day=date_only(r['date']);row=dict(date=day,**{k:finite(r[k]) for k in ('open','high','low','close','volume','adjusted_close')})
                if day<since or day>session or min(row[k] for k in ('open','high','low','close','adjusted_close'))<=0 or row['volume']<0 or not row['low']<=min(row['open'],row['close'])<=max(row['open'],row['close'])<=row['high']:raise VendorError('INVALID_BAR_OR_RANGE')
                converted.append(row)
            if not converted or converted[-1]['date']!=session:raise VendorError('STALE_OR_MISSING_BAR')
            days=[r['date'] for r in converted]
            if days!=sorted(set(days)):raise VendorError('DUPLICATE_OR_UNORDERED_SESSION')
            expected=calendar().sessions_in_range(days[0],session).strftime('%Y-%m-%d').tolist()
            if days!=expected:raise VendorError('MIXED_SESSION_OR_CALENDAR_GAP')
            bars[symbol]=converted;splits[symbol]=[];dividends[symbol]=[]
            for e in se:
                if not isinstance(e,dict) or not {'date','split'}<=set(e):raise VendorError('INVALID_SPLIT_SCHEMA')
                day=date_only(e['date'])
                if not since<=day<=session:raise VendorError('SPLIT_OUTSIDE_ASOF')
                splits[symbol].append(dict(date=day,factor=ratio(e['split'])))
            if len({e['date'] for e in splits[symbol]})!=len(splits[symbol]):raise VendorError('DUPLICATE_SPLIT')
            for e in de:
                if not isinstance(e,dict) or not {'date','currency','value','unadjustedValue'}<=set(e):raise VendorError('INVALID_DIVIDEND_SCHEMA')
                day=date_only(e['date'])
                if not since<=day<=session or e.get('currency')!='USD':raise VendorError('DIVIDEND_DATE_OR_CURRENCY')
                value=finite(e['value']);unadjusted=finite(e['unadjustedValue'])
                if min(value,unadjusted)<0:raise VendorError('NEGATIVE_DIVIDEND')
                dividends[symbol].append(dict(date=day,value_current_share_units=value,unadjusted_value=unadjusted,payment_date=date_only(e['paymentDate']) if e.get('paymentDate') else None))
            if len({e['date'] for e in dividends[symbol]})!=len(dividends[symbol]):raise VendorError('DUPLICATE_DIVIDEND')
        retrieved=self.clock().isoformat();digest=hashlib.sha256(b''.join(k.encode()+b'\0'+raw[k] for k in sorted(raw))).hexdigest()
        return Snapshot('EODHD',session,retrieved,None,fixture,None,bars,splits,dividends,currency,raw,digest,uris)
