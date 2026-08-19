import httpx


class ADCConnector:
    def __init__(
        self,
        base_url: str,
    ):
        self.base_url = base_url.rstrip("/")

    async def market_summary(self) -> dict:
        async with httpx.AsyncClient(
            timeout=30
        ) as client:
            response = await client.get(
                f"{self.base_url}/market/summary"
            )

            response.raise_for_status()

            return response.json()

    async def fundamentals(
        self,
        symbol: str,
    ) -> dict:
        async with httpx.AsyncClient(
            timeout=30
        ) as client:
            response = await client.get(
                f"{self.base_url}/fundamentals/"
                f"{symbol.upper()}"
            )

            response.raise_for_status()

            return response.json()

    async def history(
        self,
        symbol: str,
        limit: int = 500,
    ) -> dict:
        async with httpx.AsyncClient(
            timeout=30
        ) as client:
            response = await client.get(
                f"{self.base_url}/market/history/"
                f"{symbol.upper()}",
                params={
                    "limit": limit,
                },
            )

            response.raise_for_status()

            return response.json()
    async def revisions(
        self,
        symbol: str,
    ) -> dict:
        async with httpx.AsyncClient(
            timeout=30
        ) as client:
            response = await client.get(
                f"{self.base_url}/revisions/"
                f"{symbol.upper()}"
            )

            response.raise_for_status()

            return response.json()
