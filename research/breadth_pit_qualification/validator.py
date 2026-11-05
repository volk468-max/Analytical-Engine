"""Offline qualification gates. Never certifies vendor truth or prints licensed rows."""
import argparse
from collections import defaultdict
from datetime import datetime, timezone, date
import hashlib
import json
import math
from pathlib import Path
import re

DEFAULTS = {'min_coverage': 0.98, 'min_departed_coverage': 1.0,
            'min_member_count': {'SP500': 480, 'NDX100': 90},
            'max_member_count': {'SP500': 600, 'NDX100': 150},
            'require_departed_sample': True,
            'required_action_types': ['split', 'reverse_split', 'merger', 'delisting'],
            'ma_windows': [50, 200]}


def digest(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def stamp(value):
    t = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if t.tzinfo is None: raise ValueError('timezone required')
    return t.astimezone(timezone.utc)


def active(row, day):
    return row['from'] <= day < (row['to'] or '9999-12-31')


def validate(bundle, policy=None, now=None):
    """Reports structural gates only. Malformed documents are fail-closed."""
    cfg = dict(DEFAULTS)
    if policy:
        if set(policy)-set(DEFAULTS): return {'gates_passed': False, 'codes': ['UNKNOWN_POLICY'], 'real_data_qualified': False}
        cfg.update(policy)
    codes = set(); metrics = []
    def need(ok, code):
        if not ok: codes.add(code)
    try:
        for name in ('min_coverage','min_departed_coverage'):
            if not isinstance(cfg[name], (int,float)) or not math.isfinite(cfg[name]) or not 0 <= cfg[name] <= 1: raise ValueError('policy')
        if not isinstance(cfg['require_departed_sample'],bool): raise ValueError('policy')
        if not cfg['ma_windows'] or any(type(n) is not int or n < 1 for n in cfg['ma_windows']): raise ValueError('policy')
        m, p = bundle['manifest'], bundle['payload']
        need(m['schema_version'] == 1, 'SCHEMA_VERSION')
        need(m['data_kind'] in ('synthetic','vendor_export'), 'DATA_KIND')
        need(m['payload_sha256'] == digest(p), 'PAYLOAD_HASH')
        clock = now or datetime.now(timezone.utc)
        need(stamp(m['entitlement_expires_at']) > clock, 'ENTITLEMENT_EXPIRED')
        need(m['purpose'] == 'personal_research' and m['private_processing'] is True and m['licence_reviewed'] is True, 'LICENCE_GATE')
        need(m['history_basis'] == 'historical_all_members', 'SURVIVOR_ONLY_UNIVERSE')
        need(m['security_master_reviewed'] is True and m['actions_reconciled'] is True, 'HUMAN_EVIDENCE_MISSING')
        sources = {r['id']:r for r in p['provenance']}
        need(len(sources) == len(p['provenance']), 'DUPLICATE_SOURCE')
        def evidence(r):
            src=sources.get(r.get('source_id'))
            need(bool(src) and bool(re.fullmatch(r'[a-f0-9]{64}',src['sha256'])) and src['reviewed'] is True, 'PROVENANCE')
        sec={r['security_id']:r for r in p['securities']}
        need(len(sec)==len(p['securities']) and bool(sec), 'SECURITY_IDS')
        for sid,r in sec.items():
            need(bool(sid) and ':' in sid and bool(r['issuer_id']), 'SECURITY_IDS')
            date.fromisoformat(r['from'])
            if r['to']: date.fromisoformat(r['to']); need(r['from']<r['to'], 'SECURITY_INTERVAL')
            evidence(r)
        cal={r['session']:r for r in p['calendar']}
        need(bool(cal) and len(cal)==len(p['calendar']), 'CALENDAR')
        days=sorted(cal)
        need(days[0] == m['start'] and days[-1] == m['end'], 'HORIZON')
        for day,r in cal.items():
            date.fromisoformat(day)
            need(stamp(r['open_at']) < stamp(r['close_at']) <= stamp(r['decision_at']) <= clock, 'SESSION_CLOCK')
            evidence(r)
        aliases=p['tickers']; memberships=p['memberships']
        symbol_intervals=defaultdict(list)
        for r in aliases:symbol_intervals[r['exchange'],r['symbol']].append(r)
        for rs in symbol_intervals.values():
            rs=sorted(rs,key=lambda r:r['from'])
            need(all((a['to'] or '9999-12-31')<=b['from'] for a,b in zip(rs,rs[1:])), 'TICKER_REUSE_OVERLAP')
        for r in memberships:need(r['index'] in cfg['min_member_count'], 'UNKNOWN_INDEX')
        for table,fields in [(aliases,('security_id',)),(memberships,('index','security_id'))]:
            groups=defaultdict(list)
            for r in table:
                need(r['security_id'] in sec,'UNKNOWN_SECURITY'); evidence(r)
                date.fromisoformat(r['from'])
                if r['to']:date.fromisoformat(r['to']);need(r['from']<r['to'],'EMPTY_INTERVAL')
                groups[tuple(r[k] for k in fields)].append(r)
            for rs in groups.values():
                rs=sorted(rs,key=lambda r:r['from'])
                need(all((a['to'] or '9999-12-31')<=b['from'] for a,b in zip(rs,rs[1:])), 'OVERLAPPING_INTERVAL')
        ref=p['reference']
        need(ref['independent'] is True and ref['reviewed'] is True, 'REFERENCE_NOT_INDEPENDENT')
        evidence(ref)
        refs={(r['index'],r['session']):r['security_ids'] for r in ref['members']}
        need(len(refs)==len(ref['members']),'DUPLICATE_REFERENCE')
        need(set(refs)=={(idx,day) for idx in cfg['min_member_count'] for day in days}, 'REFERENCE_CALENDAR_GAPS')
        prices={}
        for r in p['prices']:
            key=(r['security_id'],r['session'])
            need(key not in prices,'DUPLICATE_PRICE'); prices[key]=r
            need(r['security_id'] in sec and r['session'] in cal,'PRICE_KEY')
            evidence(r)
            nums=[r[k] for k in ('open','high','low','close','volume')]
            need(all(type(v) in (float,int) and math.isfinite(v) for v in nums),'NONFINITE_OHLCV')
            o,h,l,c,v=nums
            need(0<l<=min(o,c)<=max(o,c)<=h and v>=0,'INVALID_OHLCV')
            need(r['padded'] is False,'PADDED_PRICE')
            need(r['adjustment_basis']=='unadjusted','ADJUSTMENT_BASIS')
            need(r['availability_verified'] is True,'ASSUMED_PRICE_AVAILABILITY')
            if r['session'] in cal:
                cr=cal[r['session']]
                need(stamp(cr['close_at'])<=stamp(r['available_at'])<=stamp(cr['decision_at']), 'PRICE_LOOKAHEAD')
            need(stamp(r['available_at'])<=stamp(m['retrieved_at']), 'RETRIEVAL_CLOCK')
            if r['security_id'] in sec:need(active(sec[r['security_id']],r['session']),'PRICE_OUTSIDE_SECURITY_LIFE')
        action_types=set()
        for r in p['actions']:
            evidence(r); need(r['security_id'] in sec,'ACTION_SECURITY');date.fromisoformat(r['ex_date'])
            need(r['availability_verified'] is True,'ASSUMED_ACTION_AVAILABILITY')
            stamp(r['available_at']);action_types.add(r['type'])
            if r['type'] in ('split','reverse_split'):
                need(type(r['ratio']) in (int,float) and math.isfinite(r['ratio']) and r['ratio']>0, 'ACTION_RATIO')
            if r['ex_date'] in cal:need(stamp(r['available_at'])<=stamp(cal[r['ex_date']]['decision_at']), 'ACTION_LOOKAHEAD')
        need(set(cfg['required_action_types'])<=action_types, 'ACTION_SAMPLE_INCOMPLETE')
        buckets=defaultdict(lambda:{'expected':0,'present':0,'departed_expected':0,'departed_present':0})
        ma={str(n):0 for n in cfg['ma_windows']}
        for (idx,day),expected in sorted(refs.items()):
            need(len(set(expected))==len(expected),'DUPLICATE_MEMBER')
            need(all(sid in sec for sid in expected),'REFERENCE_SECURITY')
            actual=[r for r in memberships if r['index']==idx and active(r,day)]
            need({r['security_id'] for r in actual}==set(expected),'MEMBERSHIP_DISAGREEMENT')
            need(cfg['min_member_count'][idx]<=len(expected)<=cfg['max_member_count'][idx],'MEMBER_COUNT')
            for r in actual:
                need(r['availability_verified'] is True, 'ASSUMED_MEMBERSHIP_AVAILABILITY')
                need(stamp(r['available_at'])<=stamp(cal[day]['decision_at']), 'MEMBERSHIP_LOOKAHEAD')
            bucket=buckets[idx,day[:4]]
            for sid in expected:
                if sid not in sec:continue
                need(active(sec[sid],day),'MEMBER_OUTSIDE_SECURITY_LIFE')
                al=[r for r in aliases if r['security_id']==sid and active(r,day)]
                need(len(al)==1 and bool(al[0]['symbol']),'TICKER_HISTORY_GAP')
                departed=sec[sid]['exit_type'] in ('delisted','bankrupt','acquired')
                present=(sid,day) in prices
                bucket['expected']+=1;bucket['present']+=present
                bucket['departed_expected']+=departed;bucket['departed_present']+=departed and present
                i=days.index(day)
                for n in cfg['ma_windows']:
                    ma[str(n)]+=i>=n-1 and all((sid,d) in prices and prices[sid,d]['padded'] is False for d in days[max(0,i-n+1):i+1])
        for (idx,year),b in sorted(buckets.items()):
            coverage=b['present']/b['expected'] if b['expected'] else 0
            departed=b['departed_present']/b['departed_expected'] if b['departed_expected'] else None
            need(coverage>=cfg['min_coverage'],'COVERAGE')
            need(departed is None or departed>=cfg['min_departed_coverage'],'DEPARTED_COVERAGE')
            if cfg['require_departed_sample']:need(departed is not None,'DEPARTED_NOT_EVALUATED')
            metrics.append(dict(index=idx,year=year,coverage=coverage,departed_coverage=departed,**b))
        return {'gates_passed':not codes,'codes':sorted(codes),'data_kind':m['data_kind'],
                'status': 'BLOCKED' if codes else ('SYNTHETIC_TEST_ONLY' if m['data_kind']=='synthetic' else 'REQUIRES_HUMAN_ATTESTATION'),
                'real_data_qualified':False,'metrics':metrics,'ma_candidate_observations':ma}
    except (KeyError,ValueError,TypeError,IndexError,OverflowError):
        return {'gates_passed':False,'codes':sorted(codes|{'MALFORMED_INPUT'}),'real_data_qualified':False,'status':'BLOCKED'}


if __name__=='__main__':
    ap=argparse.ArgumentParser(__doc__);ap.add_argument('bundle',type=Path);ap.add_argument('--policy',type=Path);ap.add_argument('--private-report',type=Path);a=ap.parse_args()
    try:r=validate(json.loads(a.bundle.read_text()),json.loads(a.policy.read_text()) if a.policy else None)
    except (OSError,ValueError):r={'gates_passed':False,'status':'BLOCKED','codes':['INPUT_READ_ERROR'],'real_data_qualified':False}
    if a.private_report:a.private_report.write_text(json.dumps(r,indent=2)+'\n')
    print(r['status'])
    raise SystemExit(not r['gates_passed'])
