import json
from aae.storage.database import Database
from aae.models.analysis import AnalysisResult

class AnalysisRepository:
    def __init__(self,db: Database): self.db=db
    def save(self,result: AnalysisResult):
        self.db.execute(
            "INSERT OR REPLACE INTO analyses(analysis_id,created_at,payload_json) VALUES(?,?,?)",
            (result.analysis_id,result.created_at,json.dumps(result.model_dump()))
        )
    def latest(self):
        rows=self.db.query("SELECT payload_json FROM analyses ORDER BY created_at DESC LIMIT 1")
        return json.loads(rows[0]["payload_json"]) if rows else None
    def history(self,limit=50):
        rows=self.db.query("SELECT payload_json FROM analyses ORDER BY created_at DESC LIMIT ?",(limit,))
        return [json.loads(r["payload_json"]) for r in rows]
