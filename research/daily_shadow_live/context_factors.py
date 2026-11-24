"""Point-in-time context adapter and separate, unqualified research correction.

No vendor requests, credentials, DB writes, or hand-assigned probability weights.
Only normalized, owner-provided Seeking Alpha observations enter this module.
"""
import hashlib
import json
import math
from datetime import datetime, timezone
from urllib.parse import urlsplit

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit

SCHEMA = 'ALPHA_CONTEXT_V1'
FACTORS = ('monetary_policy', 'financial_conditions', 'macro_surprises',
           'politics_regulation', 'market_sector', 'company_events')
SA_FIELDS = ('eps_revision_30d_pct', 'revenue_revision_30d_pct',
             'eps_up_revisions_90d', 'eps_down_revisions_90d')
FEATURES = FACTORS + ('eps_revision_30d', 'revenue_revision_30d', 'revision_breadth')
MODELS = ('VOL', 'RISK_FORECAST', 'ENSEMBLE_RISK', 'MARKET_PRECURSORS')


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def utc(value):
    if not isinstance(value,str):raise ValueError('UTC_TIMESTAMP_REQUIRED')
    d = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if d.tzinfo is None:
        raise ValueError('TIMEZONE_REQUIRED')
    return d.astimezone(timezone.utc)


def number(value, lower, upper):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError('MISSING_OR_NONNUMERIC')
    if not math.isfinite(value) or not lower <= value <= upper:
        raise ValueError('OUT_OF_RANGE')
    return float(value)


def source_url(value):
    if not isinstance(value,str):raise ValueError('CANONICAL_SOURCE_URL_REQUIRED')
    u = urlsplit(value)
    # Never accept tracking / email authentication links or embedded credentials.
    if (u.scheme != 'https' or u.hostname not in ('seekingalpha.com', 'www.seekingalpha.com')
            or u.username or u.password or u.query or u.fragment
            or not u.path.startswith(('/symbol/', '/news/', '/article/'))):
        raise ValueError('UNSAFE_OR_NONCANONICAL_SA_URL')


def feature_record(coefficients, seeking, symbol, session, issued_at, *, fixture=False):
    """Fail closed per instrument; missing is not neutral and news is untrusted data.

    The LLM's signed factor scores stay signed features, never percentage returns.
    SA Quant and Momentum are deliberately not added to avoid aggregate double count.
    """
    out = dict(schema_version=SCHEMA, symbol=symbol, session=session,
               available_at_utc=issued_at, fixture=fixture, feature_names=list(FEATURES),
               values=None, status='CONTEXT_NOT_CONSUMED', reasons=[],
               coefficient_sha256=digest(coefficients), seeking_sha256=digest(seeking))
    reasons = out['reasons']
    issued = utc(issued_at)
    values = []
    try:
        if coefficients['schema_version'] != '1.0':
            raise ValueError('COEFFICIENT_SCHEMA')
        if coefficients.get('fixture', False) != fixture:
            raise ValueError('COEFFICIENT_FIXTURE_MISMATCH')
        created = utc(coefficients['created_at_utc'])
        cutoff = utc(coefficients['information_cutoff_utc'])
        if not cutoff <= created <= issued:
            raise ValueError('COEFFICIENT_NOT_AVAILABLE_ASOF')
        if (issued - cutoff).total_seconds() > 36*3600:
            raise ValueError('STALE_COEFFICIENT')
        from research.daily_shadow.core import future_sessions
        if (coefficients['last_completed_session'] != session
                or coefficients['forecast_sessions'] != future_sessions(session, 10)
                or coefficients['horizon_sessions'] != 10):
            raise ValueError('COEFFICIENT_SESSION_OR_HORIZON_MISMATCH')
        entries = [x for x in coefficients['instruments'] if isinstance(x,dict) and x.get('symbol') == symbol]
        if len(entries) != 1:
            raise ValueError('COEFFICIENT_SYMBOL_NOT_UNIQUE')
        entry = entries[0]
        if entry['data_status'] != 'SUFFICIENT' or entry['confidence_level'] == 'LOW':
            raise ValueError('COEFFICIENT_PARTIAL_OR_LOW_CONFIDENCE')
        # Do not include both total score and its six constituent scores.
        values = [number(entry['factor_scores'].get(k), -100, 100)/100 for k in FACTORS]
        if not coefficients.get('events'):
            raise ValueError('COEFFICIENT_EVIDENCE_MISSING')
        for event in coefficients['events']:
            if not utc(event['published_at_utc']) <= utc(event['retrieved_at_utc']) <= cutoff:
                raise ValueError('FUTURE_COEFFICIENT_EVIDENCE')
    except (KeyError, TypeError, ValueError) as exc:
        reasons.append(str(exc) if isinstance(exc, ValueError) else 'COEFFICIENT_SCHEMA')
    try:
        if seeking['schema_version'] != 'SA_CONTEXT_V1':
            raise ValueError('SEEKING_SCHEMA')
        if seeking.get('fixture', False) != fixture:
            raise ValueError('SEEKING_FIXTURE_MISMATCH')
        if seeking['use_scope'] != 'PRIVATE_RESEARCH':
            raise ValueError('SEEKING_USE_SCOPE')
        records = [x for x in seeking['instruments'] if isinstance(x,dict) and x.get('symbol') == symbol]
        if len(records) != 1:
            raise ValueError('SEEKING_SYMBOL_NOT_UNIQUE')
        r = records[0]
        if r['data_status'] != 'VERIFIED_OBSERVATION':
            raise ValueError('SEEKING_UNVERIFIED_OBSERVATION')
        fields = {}
        periods = set()
        for key in SA_FIELDS:
            observation = r['fields'][key]
            source_url(observation['source_url'])
            published = utc(observation['published_at_utc'])
            retrieved = utc(observation['retrieved_at_utc'])
            if not published <= retrieved <= issued:
                raise ValueError('SEEKING_NOT_AVAILABLE_ASOF')
            if (issued - retrieved).total_seconds() > 7*86400:
                raise ValueError('STALE_SEEKING_SNAPSHOT')
            if observation['source_type'] not in ('MANUAL_VERIFIED', 'LICENSED_EXPORT'):
                raise ValueError('SEEKING_UNSUPPORTED_SOURCE_TYPE')
            # Comparing different fiscal periods / GAAP conventions is invalid.
            periods.add((observation['fiscal_period'], observation['accounting_basis']))
            fields[key] = number(observation['value'], 0 if 'revisions_90d' in key else -1000, 100000)
            if 'revisions_90d' in key and not fields[key].is_integer():
                raise ValueError('SEEKING_NONINTEGER_ANALYST_COUNT')
        if len(periods) != 1 or any(not p[0] or p[1] not in ('GAAP', 'NON_GAAP') for p in periods):
            raise ValueError('SEEKING_PERIOD_OR_BASIS_MISMATCH')
        up, down = fields['eps_up_revisions_90d'], fields['eps_down_revisions_90d']
        if up + down == 0:
            raise ValueError('SEEKING_NO_REVISION_SUPPORT')
        values += [fields['eps_revision_30d_pct']/100,
                   fields['revenue_revision_30d_pct']/100, (up-down)/(up+down)]
    except (KeyError, TypeError, ValueError) as exc:
        reasons.append(str(exc) if isinstance(exc, ValueError) else 'SEEKING_SCHEMA')
    if not reasons:
        out.update(values=values, status='CONTEXT_READY_FOR_RESEARCH')
    out['record_sha256'] = digest(out)
    return out


def task(row):
    return dict(symbol=row['symbol'], model=row['model'], horizon=int(row['horizon']),
                threshold_pct=int(row['threshold_pct']), label_type=row['label_type'])


def fit_correction(records, target, fit_at, *, fixture=False):
    """Train an L2 logit-offset research model on archived prospective records.

    Caller supplies one exact target (including symbol). Never pool labels/models.
    Each label must have fully matured before fitting; no historic LLM replay.
    This produces NO qualification or automatic promotion to daily forecasts.
    """
    if (target['model'] not in MODELS or target['horizon'] != 10
            or target['threshold_pct'] not in (5, 10, 15)
            or target['label_type'] not in ('LOW_INTRADAY', 'EOD_CLOSE')):
        raise ValueError('UNSUPPORTED_CONTEXT_TARGET')
    seen = set()
    xs, ys, offsets = [], [], []
    for r in records:
        f = r['features']
        if task(r) != target or f['symbol'] != target['symbol'] or f['session'] != r['session_date']:
            raise ValueError('TRAINING_TARGET_MISMATCH')
        if f['fixture'] != fixture or f['status'] != 'CONTEXT_READY_FOR_RESEARCH':
            raise ValueError('TRAINING_CONTEXT_UNAVAILABLE')
        if f['record_sha256'] != digest({k:v for k,v in f.items() if k != 'record_sha256'}):
            raise ValueError('TRAINING_FEATURE_HASH_MISMATCH')
        if (f['feature_names'] != list(FEATURES) or len(f['values']) != len(FEATURES)
                or not all(math.isfinite(v) for v in f['values'])):
            raise ValueError('TRAINING_FEATURE_SCHEMA')
        if not utc(f['available_at_utc']) <= utc(r['issued_at_utc']) < utc(r['maturity_at_utc']) < utc(fit_at):
            raise ValueError('TRAINING_NOT_POINT_IN_TIME_OR_UNMATURED')
        if r['session_date'] in seen:
            raise ValueError('DUPLICATE_TRAINING_SESSION')
        seen.add(r['session_date'])
        p = number(r['probability_raw'], 0, 1)
        if not 0 < p < 1 or r['outcome'] not in (0, 1):
            raise ValueError('INVALID_TRAINING_TARGET')
        offsets.append(math.log(p/(1-p)))
        xs.append(f['values']); ys.append(r['outcome'])
    if len(seen) < 252 or min(sum(ys), len(ys)-sum(ys)) < 10:
        raise ValueError('INSUFFICIENT_PROSPECTIVE_CONTEXT_HISTORY')
    x = np.asarray(xs); y = np.asarray(ys); offset = np.asarray(offsets)
    mean, scale = x.mean(axis=0), x.std(axis=0)
    scale[scale < 1e-12] = 1
    x = np.column_stack((np.ones(len(x)), (x-mean)/scale))
    def objective(beta):
        z = offset + x@beta
        return (float(np.logaddexp(0, z).sum()-y@z + 5*(beta@beta)),
                x.T@(expit(z)-y)+10*beta)
    result = minimize(objective, np.zeros(x.shape[1]), jac=True, method='L-BFGS-B')
    if not result.success:
        raise ValueError('CONTEXT_FIT_DID_NOT_CONVERGE')
    out = dict(schema_version=SCHEMA, target=target, feature_names=list(FEATURES),
               fitted_at_utc=fit_at, fixture=fixture, qualified=False,
               status='UNVALIDATED_CONTEXT_RESEARCH', n=len(ys),
               mean=mean.tolist(), scale=scale.tolist(), beta=result.x.tolist(),
               training_sha256=digest(records), last_maturity_at_utc=max((r['maturity_at_utc'] for r in records),key=utc))
    out['artifact_sha256'] = digest(out)
    return out


def augment(row, feature, artifact=None):
    """Separate output only: a blocked enhanced result NEVER replaces the baseline."""
    out = dict(baseline=dict(row), enhanced_probability_raw=None,
               context_status='CONTEXT_NOT_CONSUMED', context_reason=None,
               feature_record_sha256=feature['record_sha256'], artifact_sha256=None,
               model_version='CONTEXT_RESEARCH_V1', qualified=False)
    reason = None
    if row['status'] != 'RESEARCH_FORECAST' or row['probability_raw'] in (None, ''):
        reason = 'BASELINE_BLOCKED'
    elif int(row['horizon']) != 10:
        reason = 'NO_30_SESSION_COEFFICIENT'
    elif feature['symbol'] != row['symbol'] or feature['session'] != row['session_date']:
        reason = 'CONTEXT_TARGET_MISMATCH'
    elif utc(feature['available_at_utc']) > utc(row['issued_at_utc']):
        reason = 'CONTEXT_NOT_AVAILABLE_AT_BASELINE_ISSUE'
    elif feature['status'] != 'CONTEXT_READY_FOR_RESEARCH':
        reason = 'INCOMPLETE_CONTEXT_INPUTS'
    elif artifact is None:
        reason = 'NO_TRAINED_CONTEXT_ARTIFACT'
    elif (artifact['target'] != task(row) or artifact['feature_names'] != list(FEATURES)
          or artifact['fixture'] != feature['fixture']):
        reason = 'CONTEXT_ARTIFACT_TARGET_OR_FIXTURE_MISMATCH'
    elif not utc(artifact['last_maturity_at_utc']) < utc(artifact['fitted_at_utc']) <= utc(row['issued_at_utc']):
        reason = 'CONTEXT_ARTIFACT_NOT_AVAILABLE_ASOF'
    if reason:
        out['context_reason'] = reason
        return out
    if (artifact.get('schema_version') != SCHEMA or artifact.get('qualified') is not False
            or artifact.get('status') != 'UNVALIDATED_CONTEXT_RESEARCH'
            or artifact['artifact_sha256'] != digest({k:v for k,v in artifact.items() if k != 'artifact_sha256'})
            or feature['record_sha256'] != digest({k:v for k,v in feature.items() if k != 'record_sha256'})
            or len(artifact['mean']) != len(FEATURES) or len(artifact['scale']) != len(FEATURES)
            or len(artifact['beta']) != len(FEATURES)+1
            or not all(math.isfinite(v) for k in ('mean', 'scale', 'beta') for v in artifact[k])
            or min(artifact['scale']) <= 0):
        out['context_reason'] = 'INVALID_CONTEXT_ARTIFACT_OR_FEATURE_HASH'
        return out
    p = number(float(row['probability_raw']), 0, 1)
    if not 0 < p < 1:
        out['context_reason'] = 'BASELINE_BOUNDARY_PROBABILITY'
        return out
    x = (np.asarray(feature['values'])-artifact['mean'])/artifact['scale']
    beta = np.asarray(artifact['beta'])
    p2 = float(expit(math.log(p/(1-p))+beta[0]+x@beta[1:]))
    out.update(enhanced_probability_raw=p2, context_status='UNVALIDATED_CONTEXT_RESEARCH',
               artifact_sha256=artifact['artifact_sha256'])
    return out
