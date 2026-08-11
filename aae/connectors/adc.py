import httpx


class ADCConnector:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def market_summary(self) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                f"{self.base_url}/market/summary"
            )
            r.raise_for_status()
            return r.json()

    async def fundamentals(self, symbol: str) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                f"{self.base_url}/fundamentals/{symbol.upper()}"
            )
            r.raise_for_status()
            return r.json()
