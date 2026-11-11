import os
from pathlib import Path
import psycopg
from .bootstrap import apply,ROOT
if __name__=='__main__':
 url=os.environ['ALPHA_SHADOW_TEST_DSN'];apply(url,isolated_test=True)
 with psycopg.connect(url,autocommit=True) as c:c.execute((ROOT/'research/daily_shadow/sql/local_fixture_roles.sql').read_text())
