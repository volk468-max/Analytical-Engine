"""Explicit, reviewed capabilities. Public prices/FAQ do not create an entitlement."""
from dataclasses import dataclass
from datetime import datetime,timezone
from decimal import Decimal,InvalidOperation
from research.daily_shadow.core import utc

@dataclass(frozen=True)
class Permit:
    provider:str
    scope:str='UNQUALIFIED'
    paid:bool=False
    reviewer_evidence:str=''
    operator_class:str='UNKNOWN'
    total_monthly_usd:str|None=None
    access_until:str|None=None
    raw_until:str|None=None
    raw_storage:bool=False
    hash_metadata_retention:bool=False
    nonreconstructible_forecasts_retention:bool=False
    cloud:bool=False
    backups:bool=False
    finalization_verified:bool=False
    revoked:bool=False
    existing_paid_owner_authorized:bool=False
    authorized_vendor_cap_usd:str|None=None

    def reason(self,now,*,fixture=False,horizon_end=None):
        if self.revoked:return 'VENDOR_OFFBOARDED'
        if self.scope not in ('LIVE','FIXTURE_ONLY'):return 'LICENSE_UNQUALIFIED'
        if fixture != (self.scope=='FIXTURE_ONLY'):return 'FIXTURE_LIVE_SCOPE_MISMATCH'
        if not self.paid:return 'TRIAL_DURABLE_STORAGE_FORBIDDEN'
        if not self.reviewer_evidence or self.operator_class=='UNKNOWN':return 'MISSING_APPLICABLE_LICENSE_REVIEW'
        if self.total_monthly_usd is None and not self.existing_paid_owner_authorized:return 'TOTAL_PRICE_TAXES_UNCONFIRMED'
        try:cost=Decimal(self.total_monthly_usd if self.total_monthly_usd is not None else self.authorized_vendor_cap_usd)
        except (InvalidOperation,TypeError,ValueError):return 'INVALID_TOTAL_PRICE'
        if not cost.is_finite() or not 0<=cost<=50:return 'VENDOR_BUDGET_EXCEEDED'
        if not self.access_until or utc(now)>=utc(self.access_until):return 'SUBSCRIPTION_EXPIRED'
        if not all((self.raw_storage,self.hash_metadata_retention,self.nonreconstructible_forecasts_retention,self.cloud,self.backups)):return 'RETENTION_CAPABILITIES_NOT_APPROVED'
        if not self.raw_until or utc(now)>=utc(self.raw_until):return 'RAW_TTL_EXPIRED'
        if horizon_end and utc(self.raw_until)<=utc(horizon_end):return 'RETENTION_SHORTER_THAN_LABEL_HORIZON'
        return None

    def to_dict(self):
        from dataclasses import asdict
        return asdict(self)

def fixture_permit(provider='EODHD'):
    return Permit(provider=provider,scope='FIXTURE_ONLY',paid=True,reviewer_evidence='SYNTHETIC_PERMISSION_NOT_VENDOR_LICENSE',operator_class='SYNTHETIC',total_monthly_usd='0',access_until='2035-01-01T00:00:00+00:00',raw_until='2035-01-01T00:00:00+00:00',raw_storage=True,hash_metadata_retention=True,nonreconstructible_forecasts_retention=True,cloud=True,backups=True,finalization_verified=True)
