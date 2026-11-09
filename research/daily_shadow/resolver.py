"""Explicit one-shot outcome job, no scheduler or live provider configuration."""
from typing import Protocol
from .core import resolve, canonical, sha

class OutcomeProvider(Protocol):
 def collect_window(self, original_forecast:dict)->tuple[dict,list[dict]]: ...

def resolve_once(store, forecast_id, provider, now, live_approved=False):
 """Read the immutable original anchor; archive an actual response bundle atomically.
 Every observation must identify this archived bundle. A multi-source adapter must
 package its original bytes and their provenance into that bundle, never invent bars.
 """
 original=store.read_forecast(forecast_id)
 if original['mode']=='PROSPECTIVE' and not live_approved:
  raise PermissionError('LIVE_REQUIRES_SEPARATE_OWNER_APPROVAL')
 for attempt in range(3):
  try:
   vintage,observations=provider.collect_window(original);break
  except (TimeoutError,ConnectionError):
   if attempt==2:
    store.health(str(forecast_id)+':OUTCOME_PROVIDER_FAILURE:'+now,'OUTCOME_PROVIDER_FAILURE',attempts=3)
    return store.outcome(str(forecast_id)+':provider-failure:'+now,dict(forecast_id=str(forecast_id),status='UNRESOLVED',outcome=None,reason='OUTCOME_PROVIDER_RETRIES_EXHAUSTED'))
 if original.get('frozen_anchor') is None:
  result=dict(forecast_id=str(forecast_id),status='UNRESOLVED',outcome=None,reason='NO_FROZEN_ANCHOR')
 elif any(r.get('source_hash')!=vintage['source_hash'] for r in observations):
  result=dict(forecast_id=str(forecast_id),status='UNRESOLVED',outcome=None,reason='OUTCOME_BUNDLE_PROVENANCE_MISMATCH')
 else:
  result=resolve(original,original['frozen_anchor'],observations,now,vintage['basis'],vintage.get('actions_qualified',False))
 key=str(forecast_id)+':'+sha(canonical(result).encode())+':'+vintage['source_hash']
 return store.outcome(key,result,vintage=vintage)
