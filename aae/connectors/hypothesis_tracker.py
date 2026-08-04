import httpx
class HypothesisTrackerConnector:
    """
    HTTP-клиент для регистрации гипотез
    в Alpha Hypothesis Tracker.
    """
    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
    async def register(
        self,
        payload: dict,
    ) -> dict:
        async with httpx.AsyncClient(
            timeout=self.timeout
        ) as client:
            response = await client.post(
                f"{self.base_url}/hypotheses",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
