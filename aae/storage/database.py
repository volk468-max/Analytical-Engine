import sqlite3
from pathlib import Path

class Database:
    def __init__(self, path: str):
        self.path=Path(path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.connection=sqlite3.connect(self.path,check_same_thread=False)
        self.connection.row_factory=sqlite3.Row
        self.execute("""CREATE TABLE IF NOT EXISTS analyses(
            analysis_id TEXT PRIMARY KEY,
            created_at TEXT,
            payload_json TEXT
        )""")
    def execute(self,sql,params=()):
        cur=self.connection.cursor(); cur.execute(sql,params); self.connection.commit(); return cur
    def query(self,sql,params=()):
        cur=self.connection.cursor(); cur.execute(sql,params); return [dict(r) for r in cur.fetchall()]
