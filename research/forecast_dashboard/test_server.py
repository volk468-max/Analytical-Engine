"""Minimal security and SQL contract regression checks. Run with unittest."""
import os
import time
import unittest

os.environ.setdefault("DASHBOARD_PASSWORD", "testing-password-that-is-over-24-characters")
os.environ.setdefault("DASHBOARD_SESSION_KEY", "testing-signing-key-over-32-characters-long")
os.environ.setdefault("DASHBOARD_DATABASE_URL", "postgresql://test@localhost/alpha_shadow_research")

from research.forecast_dashboard import server

class DashboardTests(unittest.TestCase):
    def test_cookie_signature_and_expiry(self):
        ts=int(time.time())
        self.assertTrue(server.valid_session(f"{ts}.{server.sign(ts)}"))
        self.assertFalse(server.valid_session(f"{ts}.wrong"))
        old=ts-server.SESSION_SECONDS-1
        self.assertFalse(server.valid_session(f"{old}.{server.sign(old)}"))
    def test_sql_is_research_only(self):
        self.assertIn("f.run_mode='RESEARCH_FORECAST'",server.QUERY)
        self.assertIn("f.status='RESEARCH_FORECAST'",server.QUERY)
        self.assertNotIn("alpha_licensed_v3",server.QUERY)
        self.assertNotIn("SELECT *",server.QUERY.upper())
    def test_field_count(self):
        self.assertEqual(len(server.FIELDS),14)
        self.assertIn("model_id", server.FIELDS)

if __name__ == "__main__":
    unittest.main()
