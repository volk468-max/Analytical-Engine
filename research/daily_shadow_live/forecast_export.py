"""Emit a checksummed CSV of committed research forecasts for private delivery."""
import base64
import csv
import hashlib
import io
from datetime import timezone
from itertools import product
import re

from .portfolio import SYMBOLS

MODELS = ('VOL', 'RISK_FORECAST', 'ENSEMBLE_RISK', 'MARKET_PRECURSORS')
HEADER = ('session_date', 'symbol', 'model', 'horizon', 'threshold_pct', 'label_type',
          'probability_raw', 'status', 'reason', 'issued_at_utc')
QUERY = """
SELECT f.session_date, f.symbol, m.body->>'name', f.horizon, f.threshold_pct,
       f.label_type, f.probability_raw, f.status, j.body->>'reason', f.issued_at
FROM alpha_research_v3.forecasts f
JOIN alpha_research_v3.journal j ON j.id = f.id
JOIN alpha_shadow_v1.audit_events m ON m.id = f.model_id
WHERE f.session_date = %s AND f.run_mode = 'RESEARCH_FORECAST'
  AND m.body->>'name' IN ('VOL','RISK_FORECAST','ENSEMBLE_RISK','MARKET_PRECURSORS')
ORDER BY f.symbol, m.body->>'name', f.horizon, f.threshold_pct, f.label_type
"""

def encode_csv(rows):
    expected = {
        (symbol, model, horizon, threshold, label)
        for model in MODELS
        for symbol, horizon, threshold, label in product(
            SYMBOLS + (('SPY', 'QQQ', 'SOXX') if model == 'MARKET_PRECURSORS' else ()),
            (10, 30), (5, 10, 15), ('LOW_INTRADAY', 'EOD_CLOSE'))
    }
    if len(rows) != len(expected) or {tuple(row[1:6]) for row in rows} != expected:
        raise ValueError('INCOMPLETE_FORECAST_EXPORT')
    output = io.StringIO(newline='')
    writer = csv.writer(output, lineterminator='\n')
    writer.writerow(HEADER)
    for row in rows:
        reason = row[8]
        if reason and not re.fullmatch(r'[A-Z][A-Z0-9_]{0,95}', reason):
            raise ValueError('UNEXPECTED_FORECAST_REASON')
        writer.writerow((*row[:9], row[9].astimezone(timezone.utc).isoformat()))
    return output.getvalue().encode('utf-8')

def export_session(store, audit, session):
    with store.connect() as connection:
        connection.commit()
        connection.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        rows = connection.execute(QUERY, (session,)).fetchall()
    if not rows:
        audit.emit(persist=False, phase='FORECAST_EXPORT', status='NO_ROWS', session=session)
        return
    blob = encode_csv(rows)
    digest = hashlib.sha256(blob).hexdigest()
    encoded = base64.b64encode(blob).decode('ascii')
    chunks = [encoded[i:i+2000] for i in range(0, len(encoded), 2000)]
    for index, chunk in enumerate(chunks):
        audit.emit(persist=False, phase='FORECAST_EXPORT', status='CHUNK', session=session,
                   csv_sha256=digest, chunk_index=index, chunk_count=len(chunks), csv_b64=chunk)
    audit.emit(persist=False, phase='FORECAST_EXPORT', status='READY', session=session,
               csv_sha256=digest, chunk_count=len(chunks), row_count=len(rows))
