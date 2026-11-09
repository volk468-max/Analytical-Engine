"""No approved live source exists. Explicit blocker, no guessed timestamps/network."""
from .core import archive
class UnavailableLiveProvider:
 def __init__(self,reason):
  if not reason:raise ValueError('SPECIFIC_BLOCKER_REQUIRED')
  self.reason=reason
 def collect(self,session):
  return archive(b'',session,None,None,qualification='UNAVAILABLE',basis='UNKNOWN',source_present=False,provider_error=self.reason,license_status='NOT_VERIFIED',actions_qualified=False)
