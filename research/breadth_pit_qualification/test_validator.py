import copy
import unittest
from datetime import datetime, timezone
from validator import validate, digest

POLICY={'min_member_count':{'SP500':1,'NDX100':1},'ma_windows':[2,3]}


def fixture():
    """Invented data only: no vendor IDs, membership or prices."""
    source={'source_id':'invented'}
    p={'provenance':[dict(id='invented',sha256='a'*64,reviewed=True)],'calendar':[],
       'securities':[],'tickers':[],'memberships':[],'prices':[],'actions':[],
       'reference':dict(independent=True,reviewed=True,members=[],**source)}
    for d in ['2025-01-02','2025-01-03','2025-01-06']:
        p['calendar'].append(dict(session=d,open_at=d+'T14:30:00Z',close_at=d+'T21:00:00Z',decision_at=d+'T22:00:00Z',**source))
    for sid,exit,end in [('SYNTH:A','acquired','2025-01-06'),('SYNTH:B','active','')]:
        p['securities'].append(dict(security_id=sid,issuer_id='SYNTH:ISSUER',exit_type=exit,**{'from':'2025-01-01','to':end},**source))
        p['tickers'].append(dict(security_id=sid,symbol=sid[-1],exchange='SYNTH',**{'from':'2025-01-01','to':end},**source))
        for idx in ['SP500','NDX100']:
            p['memberships'].append(dict(index=idx,security_id=sid,available_at='2024-12-31T00:00:00Z',availability_verified=True,**{'from':'2025-01-02','to':end},**source))
        for d in ['2025-01-02','2025-01-03','2025-01-06']:
            if end and d>=end:continue
            p['prices'].append(dict(security_id=sid,session=d,open=10.,high=12.,low=9.,close=11.,volume=100,adjustment_basis='unadjusted',
                                   padded=False,available_at=d+'T21:15:00Z',availability_verified=True,**source))
    for idx in ['SP500','NDX100']:
        for d in ['2025-01-02','2025-01-03','2025-01-06']:
            p['reference']['members'].append(dict(index=idx,session=d,security_ids=['SYNTH:A','SYNTH:B'] if d<'2025-01-06' else ['SYNTH:B']))
    for typ in ['split','reverse_split','merger','delisting']:
        p['actions'].append(dict(security_id='SYNTH:A',type=typ,ex_date='2025-01-03',ratio=2.,available_at='2025-01-02T21:00:00Z',availability_verified=True,**source))
    m=dict(schema_version=1,data_kind='synthetic',purpose='personal_research',private_processing=True,licence_reviewed=True,history_basis='historical_all_members',
           entitlement_expires_at='2099-01-01T00:00:00Z',security_master_reviewed=True,actions_reconciled=True,retrieved_at='2025-01-07T00:00:00Z',start='2025-01-02',end='2025-01-06')
    b=dict(manifest=m,payload=p);return seal(b)


def seal(b):b['manifest']['payload_sha256']=digest(b['payload']);return b


class ValidatorTests(unittest.TestCase):
    def test_clean_synthetic_never_qualifies_real(self):
        r=validate(fixture(),POLICY);self.assertTrue(r['gates_passed'],r);self.assertFalse(r['real_data_qualified']);self.assertEqual(r['status'],'SYNTHETIC_TEST_ONLY')

    def fail(self,change,code,policy=None):
        b=fixture();change(b);seal(b);r=validate(b,policy or POLICY);self.assertIn(code,r['codes'],r);self.assertFalse(r['gates_passed'])

    def test_survivor_only(self):self.fail(lambda b:b['manifest'].update(history_basis='current_members'),'SURVIVOR_ONLY_UNIVERSE')
    def test_expired(self):self.fail(lambda b:b['manifest'].update(entitlement_expires_at='2000-01-01T00:00:00Z'),'ENTITLEMENT_EXPIRED')
    def test_cloud_shared(self):self.fail(lambda b:b['manifest'].update(private_processing=False),'LICENCE_GATE')
    def test_missing_reference_date(self):self.fail(lambda b:b['payload']['reference']['members'].pop(),'REFERENCE_CALENDAR_GAPS')
    def test_reference_not_independent(self):self.fail(lambda b:b['payload']['reference'].update(independent=False),'REFERENCE_NOT_INDEPENDENT')
    def test_missing_member(self):self.fail(lambda b:b['payload']['memberships'].pop(),'MEMBERSHIP_DISAGREEMENT')
    def test_future_price(self):self.fail(lambda b:b['payload']['prices'][0].update(available_at='2025-01-03T00:00:00Z'),'PRICE_LOOKAHEAD')
    def test_assumed_date(self):self.fail(lambda b:b['payload']['prices'][0].update(availability_verified=False),'ASSUMED_PRICE_AVAILABILITY')
    def test_future_membership(self):self.fail(lambda b:b['payload']['memberships'][0].update(available_at='2025-01-04T00:00:00Z'),'MEMBERSHIP_LOOKAHEAD')
    def test_duplicate_quote(self):self.fail(lambda b:b['payload']['prices'].append(copy.deepcopy(b['payload']['prices'][0])),'DUPLICATE_PRICE')
    def test_padding(self):self.fail(lambda b:b['payload']['prices'][0].update(padded=True),'PADDED_PRICE')
    def test_adjusted(self):self.fail(lambda b:b['payload']['prices'][0].update(adjustment_basis='TOTALRETURN'),'ADJUSTMENT_BASIS')
    def test_action_ratio(self):self.fail(lambda b:b['payload']['actions'][0].update(ratio=0),'ACTION_RATIO')
    def test_action_missing(self):self.fail(lambda b:b['payload'].update(actions=[]),'ACTION_SAMPLE_INCOMPLETE')
    def test_action_future(self):self.fail(lambda b:b['payload']['actions'][0].update(available_at='2025-01-04T00:00:00Z'),'ACTION_LOOKAHEAD')
    def test_ticker_missing(self):self.fail(lambda b:b['payload']['tickers'].pop(),'TICKER_HISTORY_GAP')
    def test_ticker_reuse(self):self.fail(lambda b:b['payload']['tickers'][0].update(symbol='B'),'TICKER_REUSE_OVERLAP')
    def test_source_missing(self):self.fail(lambda b:b['payload'].update(provenance=[]),'PROVENANCE')
    def test_clock_naive(self):self.fail(lambda b:b['payload']['prices'][0].update(available_at='2025-01-02T21:30:00'),'MALFORMED_INPUT')
    def test_hash(self):
        b=fixture();b['payload']['prices'][0]['close']=10.;self.assertIn('PAYLOAD_HASH',validate(b,POLICY)['codes'])
    def test_missing_price_is_not_padded(self):
        b=fixture();b['payload']['prices'].pop(0);seal(b);r=validate(b,POLICY);self.assertIn('DEPARTED_COVERAGE',r['codes']);self.assertLess(r['ma_candidate_observations']['2'],6)
    def test_coverage_threshold_cannot_disable_pit(self):
        c=dict(POLICY,min_coverage=0,min_departed_coverage=0);self.fail(lambda b:b['payload']['prices'][0].update(availability_verified=False),'ASSUMED_PRICE_AVAILABILITY',c)
    def test_unknown_policy(self):self.assertFalse(validate(fixture(),{'ignore_pit':True})['gates_passed'])
    def test_security_life(self):self.fail(lambda b:b['payload']['securities'][0].update(to='2025-01-03'),'MEMBER_OUTSIDE_SECURITY_LIFE')
    def test_bad_ohlc(self):self.fail(lambda b:b['payload']['prices'][0].update(high=1),'INVALID_OHLCV')

    def test_over_98_percent_still_rejects_departed_loss(self):
        b=fixture();p=b['payload']
        for i in range(80):
            sid=f'SYNTH:C{i}'
            s=copy.deepcopy(p['securities'][1]);s['security_id']=sid;p['securities'].append(s)
            a=copy.deepcopy(p['tickers'][1]);a.update(security_id=sid,symbol=f'C{i}');p['tickers'].append(a)
            for m in list(p['memberships'][:4]):
                if m['security_id']=='SYNTH:B':
                    m=copy.deepcopy(m);m['security_id']=sid;p['memberships'].append(m)
            for r in list(p['prices'][:5]):
                if r['security_id']=='SYNTH:B':
                    r=copy.deepcopy(r);r['security_id']=sid;p['prices'].append(r)
            for r in p['reference']['members']:r['security_ids'].append(sid)
        p['prices'].pop(0);seal(b);r=validate(b,POLICY)
        self.assertTrue(all(m['coverage']>.98 for m in r['metrics']))
        self.assertIn('DEPARTED_COVERAGE',r['codes']);self.assertFalse(r['gates_passed'])

    def test_empty_departed_not_success(self):
        self.fail(lambda b:b['payload']['securities'][0].update(exit_type='active'),'DEPARTED_NOT_EVALUATED')

    def test_overlapping_membership(self):
        self.fail(lambda b:b['payload']['memberships'].append(copy.deepcopy(b['payload']['memberships'][0])),'OVERLAPPING_INTERVAL')

    def test_invalid_policy_fails_closed(self):self.assertFalse(validate(fixture(),dict(POLICY,min_coverage=2))['gates_passed'])


if __name__=='__main__':unittest.main()
