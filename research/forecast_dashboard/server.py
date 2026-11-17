"""Private read-only Alpha OS forecast dashboard. No trading, no raw market data."""
from __future__ import annotations
import hashlib
import hmac
import json
import os
import secrets
import time
from datetime import datetime, timezone
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
import psycopg

ROOT = Path(__file__).resolve().parent
SESSION_SECONDS = 8 * 3600
QUERY = """
SELECT f.session_date::text, f.symbol, f.label_type, f.threshold_pct,
       f.horizon, m.model_name, round((f.probability_raw*100)::numeric,1)::float,
       f.model_status, f.training_status, f.issued_at::text,
       o.status, o.outcome, b.probability
FROM alpha_research_v3.forecasts f
JOIN alpha_shadow_v1.model_registry m ON m.id=f.model_id
LEFT JOIN LATERAL (
 SELECT v.status,v.outcome
 FROM alpha_research_v3.outcomes v
 JOIN alpha_research_v3.journal j ON j.id=v.id
 WHERE v.forecast_id=f.id ORDER BY j.seq DESC LIMIT 1
) o ON TRUE
LEFT JOIN alpha_operations_v4.baselines b ON b.forecast_id=f.id
WHERE f.run_mode='RESEARCH_FORECAST' AND f.status='RESEARCH_FORECAST'
  AND f.session_date >= CURRENT_DATE - INTERVAL '120 days'
ORDER BY f.session_date DESC,f.symbol,f.label_type,f.horizon,f.threshold_pct,m.model_name
LIMIT 25000
"""
FIELDS = ("session","symbol","label","threshold","horizon","model","probability",
          "model_status","training_status","issued_at","outcome_status","outcome","baseline")
PASSWORD = os.getenv("DASHBOARD_PASSWORD", "")
KEY = os.getenv("DASHBOARD_SESSION_KEY", "").encode()
DB = os.getenv("DASHBOARD_DATABASE_URL", "")
if len(PASSWORD) < 24 or len(KEY) < 32 or not DB:
    raise RuntimeError("DASHBOARD_PASSWORD (24+), DASHBOARD_SESSION_KEY (32+) and DASHBOARD_DATABASE_URL required")
if psycopg.conninfo.conninfo_to_dict(DB).get("dbname") != "alpha_shadow_research":
    raise RuntimeError("ISOLATED_RESEARCH_DATABASE_REQUIRED")

def sign(ts: int) -> str:
    return hmac.new(KEY, f"alpha-dashboard-v1:{ts}".encode(), hashlib.sha256).hexdigest()

def valid_session(raw: str) -> bool:
    try:
        stamp, digest = raw.split(".", 1)
        ts = int(stamp)
        return 0 <= time.time()-ts < SESSION_SECONDS and hmac.compare_digest(digest, sign(ts))
    except (ValueError, AttributeError):
        return False

def load_forecasts():
    # Explicitly read-only, repeatable-read transaction. No OHLC or encrypted payload access.
    with psycopg.connect(DB, connect_timeout=8, options="-c default_transaction_read_only=on") as conn:
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        raw = conn.execute(QUERY).fetchall()
    records = [dict(zip(FIELDS, row)) for row in raw]
    return {"asof":datetime.now(timezone.utc).isoformat(),
            "latest_session": records[0]["session"] if records else None,
            "count":len(records),"rows":records,
            "classification":"UNVALIDATED_UNCALIBRATED_RESEARCH_ONLY"}

class Handler(BaseHTTPRequestHandler):
    def send(self, code, data, mime="application/json; charset=utf-8", extra=None):
        body = data if isinstance(data, bytes) else json.dumps(data, default=str, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        if extra:
            for k, v in extra.items(): self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def authenticated(self):
        jar = cookies.SimpleCookie()
        try: jar.load(self.headers.get("Cookie", ""))
        except cookies.CookieError: return False
        return "alpha_session" in jar and valid_session(jar["alpha_session"].value)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            return self.send(200, {"status":"ok"})
        if path == "/api/data":
            if not self.authenticated(): return self.send(401, {"error":"AUTH_REQUIRED"})
            try: return self.send(200, load_forecasts())
            except Exception:
                self.log_error("DATABASE_READ_FAILED")
                return self.send(503, {"error":"DATA_TEMPORARILY_UNAVAILABLE"})
        files = {"/":("index.html","text/html; charset=utf-8"),
                 "/app.js":("app.js","application/javascript; charset=utf-8"),
                 "/style.css":("style.css","text/css; charset=utf-8")}
        if path not in files: return self.send(404, {"error":"NOT_FOUND"})
        name, mime = files[path]
        return self.send(200, (ROOT/name).read_bytes(), mime)

    def do_POST(self):
        if urlparse(self.path).path != "/api/login": return self.send(404, {"error":"NOT_FOUND"})
        if self.headers.get("Content-Type","").split(";")[0] != "application/json":
            return self.send(415, {"error":"JSON_REQUIRED"})
        try:
            length = int(self.headers.get("Content-Length","0"))
            if length < 1 or length > 4096: return self.send(400, {"error":"INVALID_BODY"})
            data = json.loads(self.rfile.read(length))
            supplied = data.get("password","")
            if not isinstance(supplied,str) or not secrets.compare_digest(supplied,PASSWORD):
                time.sleep(0.3)
                return self.send(401, {"error":"INVALID_CREDENTIALS"})
        except (ValueError, TypeError, json.JSONDecodeError):
            return self.send(400, {"error":"INVALID_BODY"})
        ts = int(time.time())
        cookie = f"alpha_session={ts}.{sign(ts)}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age={SESSION_SECONDS}"
        return self.send(200, {"authenticated":True}, extra={"Set-Cookie":cookie})

if __name__ == "__main__":
    port = int(os.getenv("PORT","8080"))
    ThreadingHTTPServer(("0.0.0.0",port),Handler).serve_forever()
