"""Offline research only. No I/O to providers, brokers, or production modules."""
import copy,hashlib,json,math
from datetime import datetime

def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def instant(x):
    t=datetime.fromisoformat(x)
    if t.tzinfo is None:raise ValueError("TIMEZONE_REQUIRED")
    return t.timestamp()

def finite(x):return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)
def validate_snapshot(s):
    required=('snapshot_id','decision_at','valuation_at','base_currency','positions','cash','fx','source_hashes','source_available_at','ingested_at','price_basis','corporate_actions','cash_flows','peak_history','fees_assumptions')
    if any(k not in s for k in required):raise ValueError('INCOMPLETE_SNAPSHOT')
    for t in ('decision_at','valuation_at','source_available_at','ingested_at'):
        if datetime.fromisoformat(s[t]).tzinfo is None:raise ValueError('TIMEZONE_REQUIRED')
    if max(instant(s[k]) for k in ('valuation_at','source_available_at','ingested_at'))>instant(s['decision_at']):raise ValueError('FUTURE_INPUT')
    if s['price_basis']!='RAW_UNADJUSTED':raise ValueError('DOUBLE_ADJUSTMENT_RISK')
    if not s['source_hashes'] or not s['snapshot_id'] or not s['base_currency']:raise ValueError('PROVENANCE_REQUIRED')
    if len({p['symbol'] for p in s['positions']})!=len(s['positions']):raise ValueError('DUPLICATE_POSITION')
    for p in s['positions']:
        if not all(k in p for k in ('symbol','shares','currency','price','price_at','source_hash')):raise ValueError('POSITION_INCOMPLETE')
        if not finite(p['shares']) or p['shares']<0 or not finite(p['price']) or p['price']<=0 or p['price_at']!=s['valuation_at']:raise ValueError('INVALID_POSITION_MARK')
    for c,v in s['cash'].items():
        if not finite(v) or v<0:raise ValueError('INVALID_CASH')
    currencies=set(s['cash'])|{p['currency'] for p in s['positions']}
    for c in currencies:
        f=s['fx'].get(c)
        if not f or not finite(f['rate']) or f['rate']<=0 or f['at']!=s['valuation_at'] or not f['source_hash']:raise ValueError('MISSING_FX')
    if s['fx'][s['base_currency']]['rate']!=1:raise ValueError('BASE_FX_NOT_ONE')
    return digest(s)

def nav_path(snapshot,sessions):
    """Each entry is a synchronous mark; repeated marks may share session id.
    Actions applied once, by stable event id. Inputs must carry full action audit.
    No external flows, future portfolio weights or asynchronous asset lows allowed.
    """
    validate_snapshot(snapshot);s=copy.deepcopy(snapshot);positions={p['symbol']:p for p in s['positions']};cash=dict(s['cash']);receivables={};seen=set();result=[];last=s['valuation_at']
    initial=sum(p['shares']*p['price']*s['fx'][p['currency']]['rate'] for p in positions.values())+sum(v*s['fx'][c]['rate'] for c,v in cash.items())
    if initial<=0:raise ValueError('NONPOSITIVE_NAV')
    for m in sessions:
        if instant(m['at'])<=instant(last) or not m.get('actions_complete') or m.get('external_flows'):raise ValueError('UNQUALIFIED_MARK_OR_FLOW')
        last=m['at']
        for a in m.get('actions',[]):
            if a['id'] in seen:continue
            if a['type']=='split':
                if not finite(a['ratio']) or a['ratio']<=0:raise ValueError('SPLIT_RATIO')
                positions[a['symbol']]['shares']*=a['ratio']
            elif a['type']=='dividend_ex':
                if not a.get('pay_at') or not finite(a['amount']) or a['amount']<0:raise ValueError('DIVIDEND_EVIDENCE_MISSING')
                p=positions[a['symbol']];receivables[a['id']]=(p['currency'],p['shares']*a['amount'],a['pay_at'])
            else:raise ValueError('UNKNOWN_ACTION')
            seen.add(a['id'])
        for key,(c,v,pay) in list(receivables.items()):
            if instant(pay)<=instant(m['at']):cash[c]=cash.get(c,0)+v;del receivables[key]
        if not set(cash)<=set(m['cash_accrual']):raise ValueError('UNKNOWN_CASH_ACCRUAL')
        for c,v in m['cash_accrual'].items():
            if not finite(v):raise ValueError('UNKNOWN_CASH_ACCRUAL')
            cash[c]=cash.get(c,0)+v
        def fx(c):
            f=m['fx'][c]
            if not f.get('source_hash') or f['at']!=m['at'] or not finite(f['rate']) or f['rate']<=0:raise ValueError('UNSYNCHRONISED_FX')
            if c==s['base_currency'] and f['rate']!=1:raise ValueError('BASE_FX_NOT_ONE')
            return f['rate']
        total=0
        for sym,p in positions.items():
            q=m['prices'][sym]
            if q['at']!=m['at'] or not finite(q['price']) or q['price']<0 or not q.get('source_hash'):raise ValueError('UNSYNCHRONISED_OR_MISSING_PRICE')
            if q['price']==0 and not q.get('verified_zero_recovery'):raise ValueError('MISSING_IS_NOT_ZERO')
            total+=p['shares']*q['price']*fx(p['currency'])
        total+=sum(v*fx(c) for c,v in cash.items())+sum(v*fx(c) for c,v,pay in receivables.values())
        result.append({'session':m['session'],'at':m['at'],'nav':total,'return':total/initial-1})
    return initial,result

def touch_label(initial,marks,expected_sessions,full_maturity,intraday_complete=False):
    if len(expected_sessions)!=60 or len(set(expected_sessions))!=60:raise ValueError('EXACTLY_60_SESSIONS_REQUIRED')
    observed={m['session'] for m in marks}
    if not full_maturity or observed!=set(expected_sessions):return {'primary':None,'daily_proxy':None,'status':'IMMATURE_OR_GAP'}
    hit=any(m['nav']<=initial*.9+abs(initial)*1e-12 for m in marks)
    return {'primary':bool(hit) if hit or intraday_complete else None,'daily_proxy':bool(hit),'status':'EXACT' if intraday_complete else 'DAILY_PROXY_ONLY'}

def drawdown_budget(nav,hwm):
    if nav is None or hwm is None:return dict(drawdown=None,used=None,residual=None,residual_fraction=None)
    if not finite(nav) or not finite(hwm) or nav<=0 or hwm<nav:raise ValueError('INVALID_FLOW_ADJUSTED_HWM')
    return dict(drawdown=nav/hwm-1,used=hwm-nav,residual=max(0,nav-.85*hwm),residual_fraction=max(0,nav-.85*hwm)/nav)

def qualify_factor(f,decision):
    required=('value','release_at','ingested_at','source_hash','pit_qualified','group','event_id','kind','stale')
    if not all(k in f for k in required) or not f['pit_qualified'] or f['stale'] or f['value'] is None:return False
    try:return max(instant(f['release_at']),instant(f['ingested_at']))<=instant(decision) and finite(f['value'])
    except (ValueError,TypeError):return False

def deduplicate(items):
    # Caller supplies verified canonical event id and near-duplicate text fingerprint.
    parents=list(range(len(items)))
    def find(i):
        while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
        return i
    by_event={};by_text={}
    for i,item in enumerate(items):
        if not item.get('event_id') or not item.get('text_fingerprint'):raise ValueError('DEDUP_ID_REQUIRED')
        for key,mapping in ((item['event_id'],by_event),(item['text_fingerprint'],by_text)):
            if key in mapping:
                a,b=find(i),find(mapping[key]);parents[max(a,b)]=min(a,b)
            else:mapping[key]=i
    return [items[i] for i in range(len(items)) if find(i)==i]

def update_logit(base,features,coefficients,decision,validated=False,synthetic=False):
    if not synthetic or validated: # no real calibrated model has been qualified here
        return dict(baseline_probability=None,probability=None,interval=None,status='BLOCKED_REAL_MODEL_UNQUALIFIED',attribution=None)
    if not 0<base<1:raise ValueError('PROBABILITY_RANGE')
    ids=set();groups=set();terms={}
    for name,f in features.items():
        if not qualify_factor(f,decision):return dict(baseline_probability=base,probability=None,interval=None,status='UNAVAILABLE_FACTOR',attribution=None)
        if f['event_id'] in ids or f['group'] in groups:raise ValueError('CORRELATED_GROUP_REQUIRES_JOINT_MODEL')
        ids.add(f['event_id']);groups.add(f['group']);terms[name]=coefficients[name]*f['value']
    z=math.log(base/(1-base))+sum(terms.values());p=1/(1+math.exp(-max(-700,min(700,z))))
    return dict(baseline_probability=base,probability=p,interval=None,status='SYNTHETIC_UNVALIDATED',attribution=terms,attribution_units='LOG_ODDS_NOT_PERCENTAGE_POINTS',unique_causal_attribution=False)

def empirical_synthetic(paths):
    if not paths or any(len(p)!=60 for p in paths):raise ValueError('COMPLETE_JOINT_NAV_PATHS_REQUIRED')
    hits=[min(p)<=.9 for p in paths];losses=sorted((1-p[-1] for p in paths),reverse=True);mass=.05*len(losses);es=sum(v*max(0,min(1,mass-i)) for i,v in enumerate(losses))/mass
    return dict(probability=sum(hits)/len(hits),baseline='EMPIRICAL_JOINT_NAV_PATHS',interval=None,expected_shortfall_5pct=es,status='SYNTHETIC_UNVALIDATED',calibrated=False,effective_n=None)

def eligible_train(anchor_index,maturity,cutoff,boundary):return maturity is not None and maturity<=cutoff and anchor_index<boundary-60

class Policy:
    def __init__(self,first,strong,confirmation,cooldown,reentry_below):
        if not 0<=first<=strong<=.5 or confirmation<1 or cooldown<0 or not 0<=reentry_below<.35:raise ValueError('EXPLICIT_POLICY_PARAMETERS_REQUIRED')
        self.first,self.strong,self.confirm,self.cool,self.reentry=first,strong,confirmation,cooldown,reentry_below
        self.target=0.;self.streak=0;self.last=-100000;self.candidate=None;self.pending=None
    def step(self,p,session,validated=False,synthetic=False):
        if not synthetic or validated or p is None:return {'state':'BLOCKED','intent':None}
        if not 0<=p<=1:raise ValueError('P_RANGE')
        desired=self.strong if p>=.60 else self.first if p>=.51 else (0. if p<self.reentry else self.target)
        self.streak=self.streak+1 if desired==self.candidate else 1;self.candidate=desired
        if self.pending or session-self.last<self.cool or self.streak<self.confirm or desired==self.target:return {'state':'WATCH' if p>=.35 else 'HOLD','intent':None}
        self.pending={'execute_not_before_session':session+1,'cumulative_trim_target':desired,'delta_original_exposure':desired-self.target,'mode':'OFFLINE_SYNTHETIC_INTENT'};return {'state':'CANDIDATE','intent':dict(self.pending)}
    def settle(self,session,filled_target):
        if not self.pending or session<self.pending['execute_not_before_session'] or filled_target!=self.pending['cumulative_trim_target']:raise ValueError('INVALID_FILL')
        self.target=filled_target;self.pending=None;self.last=session

def ladder_target(price,anchor):
    if price<=0 or anchor<=0:raise ValueError('PRICE')
    # Mechanism-only original-unit levels, explicit fixed-anchor interpretation.
    levels=max(0,math.floor((price/anchor-1+1e-12)/.02));return max(.5,1-.05*levels)

def append_record(records,payload):
    record=copy.deepcopy(payload);record['previous_hash']=records[-1]['record_hash'] if records else None;record['record_hash']=digest(record);records.append(record);return record

def verify_chain(records):
    prev=None
    for row in records:
        r=dict(row);h=r.pop('record_hash')
        if r['previous_hash']!=prev or digest(r)!=h:return False
        prev=h
    return True
