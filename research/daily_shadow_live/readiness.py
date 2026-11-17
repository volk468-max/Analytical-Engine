"""Stable *validated six-symbol inputs*, with raw vintages retained independently."""
import hashlib,time
from datetime import datetime,timezone
from research.daily_shadow.core import canonical
from research.daily_shadow_v3.adapter import SYMBOLS,VendorError,issuance_gate
from dataclasses import replace
from .diagnostics import observe
BAR_FIELDS=('date','open','high','low','close','volume')

def components(snapshot,symbols=SYMBOLS):
    result={'context':dict(provider=snapshot.provider,session=snapshot.session,basis=snapshot.basis,fixture=snapshot.fixture,legal_reason=snapshot.legal_reason)}
    for symbol in symbols:
        result[symbol+'.currency']=snapshot.currency.get(symbol)
        result[symbol+'.bars']=[{k:r[k] for k in BAR_FIELDS} for r in snapshot.bars.get(symbol,[])]
        result[symbol+'.splits']=sorted(snapshot.splits.get(symbol,[]),key=lambda e:e['date'])
        result[symbol+'.dividends']=sorted(snapshot.dividends.get(symbol,[]),key=lambda e:e['date'])
    return result

def fingerprint(snapshot,symbols=SYMBOLS):return hashlib.sha256(canonical(components(snapshot,symbols)).encode()).hexdigest()

def collect_stable(adapter,store,contract,session,*,gap=60,max_pairs=3,sleeper=None,clock=None,symbols=SYMBOLS):
    if not 60<=gap<=120 or not 1<=max_pairs<=3:raise ValueError('INVALID_READINESS_BOUNDS')
    sleeper=sleeper or time.sleep;clock=clock or (lambda:datetime.now(timezone.utc))
    def fetch():
        reason=issuance_gate(session,clock().isoformat(),replace(adapter.permit,finalization_verified=True))
        if reason:raise VendorError(reason)
        snap=adapter.collect(session)
        if snap.legal_reason:raise VendorError(snap.legal_reason)
        ref=store.payload(contract,snap,adapter.permit.raw_until)
        return snap,str(ref),fingerprint(snap,symbols)
    first,first_ref,first_hash=fetch()
    for attempt in range(1,max_pairs+1):
        sleeper(gap);second,second_ref,second_hash=fetch()
        first_parts,second_parts=components(first,symbols),components(second,symbols)
        changed=[key for key,value in first_parts.items() if value!=second_parts.get(key)]
        classification='STABLE_INPUTS' if first_hash==second_hash else 'FORECAST_INPUT_REVISION'
        if first_hash==second_hash and first.revision!=second.revision:classification='RAW_ONLY_REVISION'
        # Persist safe evidence even for the terminal failed pair. Raw is private/deletable.
        from .runtime import receipt
        receipt(store,phase='READINESS',fingerprint_kind='VALIDATED_SYMBOL_INPUTS_V2' if tuple(symbols)!=SYMBOLS else 'VALIDATED_SIX_SYMBOL_INPUTS_V1',status=classification,readiness_attempt=attempt,first_raw_revision=first.revision,second_raw_revision=second.revision,first_semantic_hash=first_hash,second_semantic_hash=second_hash,changed_components=changed,first_payload_ref=first_ref,second_payload_ref=second_ref)
        if first_hash==second_hash:return first,second,first_hash,second_hash
        first,first_ref,first_hash=second,second_ref,second_hash
    raise VendorError('SOURCE_STILL_REVISING')
