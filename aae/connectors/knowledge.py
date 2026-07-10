import httpx

class KnowledgeConnector:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
    async def latest(self, limit: int = 50) -> list[dict]:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(f"{self.base_url}/knowledge/latest", params={"limit": limit})
            r.raise_for_status()
            return r.json().get("records", [])
    async def high_importance(self, minimum_score: float = 70, limit: int = 50) -> list[dict]:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                f"{self.base_url}/knowledge/high-importance",
                params={"minimum_score": minimum_score, "limit": limit},
            )
            r.raise_for_status()
            return r.json().get("records", [])
