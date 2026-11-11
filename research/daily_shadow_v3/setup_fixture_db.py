"""Manual disposable local test setup. Does not read production environment variables."""
import os
from pathlib import Path
import psycopg
from research.daily_shadow.core import calendar

def setup():
    dsn=os.environ['ALPHA_SHADOW_TEST_DSN'];info=psycopg.conninfo.conninfo_to_dict(dsn)
    if info.get('host') not in ('127.0.0.1','localhost') or info.get('dbname')!='alpha_shadow_research':raise ValueError('LOCAL_DISPOSABLE_ONLY')
    with psycopg.connect(dsn,autocommit=True) as c:
        for name in ('001_isolated.sql','002_contract_hardening.sql','003_research_forecast.sql','local_fixture_roles.sql'):
            c.execute(Path('research/daily_shadow/sql',name).read_text())
        rows=[(s.date(),calendar().session_close(s).to_pydatetime(),'XNYS_exchange_calendars_4.11.2') for s in calendar().sessions]
        with c.cursor() as cur:cur.executemany('insert into alpha_research_v3.calendar_sessions values(%s,%s,%s)',rows)
if __name__=='__main__':setup()
