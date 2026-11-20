"""Opt-in, private journal export of separate contextual research calculations.

Only a normalized local JSON bundle is read. This is not a Seeking Alpha API
client. Normal cron and 516-row CSV are unchanged when the feature is disabled.
"""
import base64
import csv
import hashlib
import io
import json
import os
from itertools import product
from pathlib import Path

from .context_factors import augment, digest, feature_record, task
from .forecast_export import HEADER
from .portfolio import SYMBOLS


def calculate(blob, bundle):
    reader = csv.DictReader(io.StringIO(blob.decode('utf-8')))
    if tuple(reader.fieldnames or ()) != HEADER:
        raise ValueError('CONTEXT_BASELINE_HEADER')
    rows = list(reader)
    sessions = {r['session_date'] for r in rows}
    if len(rows) != 516 or sessions != {bundle['session']}:
        raise ValueError('CONTEXT_BASELINE_COMPLETENESS_OR_SESSION')
    keys = [digest(task(r)) for r in rows]
    if len(set(keys)) != len(rows):
        raise ValueError('CONTEXT_DUPLICATE_BASELINE_KEY')
    expected = {digest(dict(symbol=s, model=m, horizon=h, threshold_pct=t, label_type=l))
                for m in ('VOL', 'RISK_FORECAST', 'ENSEMBLE_RISK', 'MARKET_PRECURSORS')
                for s,h,t,l in product(SYMBOLS + (('SPY','QQQ','SOXX') if m == 'MARKET_PRECURSORS' else ()),
                                       (10,30), (5,10,15), ('LOW_INTRADAY','EOD_CLOSE'))}
    if set(keys) != expected:
        raise ValueError('CONTEXT_BASELINE_UNIVERSE_MISMATCH')
    artifacts = {digest(a['target']): a for a in bundle.get('artifacts', [])}
    if len(artifacts) != len(bundle.get('artifacts', [])):
        raise ValueError('CONTEXT_DUPLICATE_ARTIFACT_TARGET')
    cache, results = {}, []
    for row in rows:
        key = (row['symbol'], row['issued_at_utc'])
        if key not in cache:
            cache[key] = feature_record(bundle['coefficients'], bundle['seeking'],
                                        row['symbol'], row['session_date'], row['issued_at_utc'])
        results.append(augment(row, cache[key], artifacts.get(digest(task(row)))))
    # A context model must not turn nested TOUCH events into contradictory risks.
    # Keep the baseline immutable; withhold the entire affected enhanced group.
    groups = {}
    for result in results:
        r = result['baseline']
        groups.setdefault((r['symbol'],r['model'],r['horizon']), []).append(result)
    for group in groups.values():
        for field in ('baseline', 'enhanced'):
            bank = {}
            for result in group:
                r = result['baseline']
                value = r['probability_raw'] if field == 'baseline' else result['enhanced_probability_raw']
                if value not in (None, ''):
                    bank[(int(r['threshold_pct']),r['label_type'])] = float(value)
            invalid = any(bank[(t,l)] + 1e-12 < bank[(t+5,l)]
                          for t,l in bank if t in (5,10) and (t+5,l) in bank)
            invalid |= any(bank[(t,'EOD_CLOSE')] > bank[(t,'LOW_INTRADAY')] + 1e-12
                           for t,l in bank if l == 'EOD_CLOSE' and (t,'LOW_INTRADAY') in bank)
            if invalid:
                for result in group:
                    result.update(enhanced_probability_raw=None, context_status='CONTEXT_NOT_CONSUMED',
                                  context_reason='BASELINE_INCOHERENT' if field == 'baseline' else 'ENHANCED_INCOHERENT')
    return dict(schema_version='ALPHA_CONTEXT_EXPORT_V1', session=bundle['session'],
                baseline_csv_sha256=hashlib.sha256(blob).hexdigest(), bundle_sha256=digest(bundle),
                status='RESEARCH_ONLY_NOT_A_QUALIFIED_FORECAST',
                features=list(cache.values()), rows=results)


def export_context(blob, audit, session):
    if os.environ.get('ALPHA_CONTEXT_RESEARCH_ENABLED') != 'true':
        return
    location = os.environ.get('ALPHA_CONTEXT_BUNDLE_PATH')
    if not location:
        audit.emit(persist=False, phase='CONTEXT_EXPORT', status='CONTEXT_NOT_CONSUMED',
                   session=session, reason='CONTEXT_BUNDLE_NOT_CONFIGURED')
        return
    path = Path(location)
    if path.suffix != '.json' or path.stat().st_size > 5_000_000:
        raise ValueError('CONTEXT_BUNDLE_FORMAT_OR_SIZE')
    bundle = json.loads(path.read_text())
    if bundle['session'] != session:
        raise ValueError('CONTEXT_BUNDLE_SESSION_MISMATCH')
    output = calculate(blob, bundle)
    payload = json.dumps(output, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    checksum = hashlib.sha256(payload).hexdigest()
    encoded = base64.b64encode(payload).decode('ascii')
    chunks = [encoded[i:i+2000] for i in range(0, len(encoded), 2000)]
    for index, chunk in enumerate(chunks):
        audit.emit(persist=False, phase='CONTEXT_EXPORT', status='CHUNK', session=session,
                   json_sha256=checksum, chunk_index=index, chunk_count=len(chunks), json_b64=chunk)
    audit.emit(persist=False, phase='CONTEXT_EXPORT', status='READY', session=session,
               json_sha256=checksum, chunk_count=len(chunks), row_count=len(output['rows']),
               enhanced_count=sum(r['enhanced_probability_raw'] is not None for r in output['rows']))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Private, separate contextual research export; never overwrites baseline')
    parser.add_argument('--baseline', required=True)
    parser.add_argument('--bundle', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    result = calculate(Path(args.baseline).read_bytes(), json.loads(Path(args.bundle).read_text()))
    with open(args.output, 'x') as stream:
        json.dump(result, stream, sort_keys=True, allow_nan=False)
