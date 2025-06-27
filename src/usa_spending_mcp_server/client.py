from typing import Any, Dict, Optional

import httpx


class USASpendingClient:
    """Shared HTTP client for USA Spending API"""

    BASE_URL = "https://api.usaspending.gov/api/v2"

    def __init__(self, timeout: float = 30.0):
        self.client = httpx.AsyncClient(
            timeout=timeout, headers={"Content-Type": "application/json"}
        )

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with unified error handling"""
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"

        try:
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = f"HTTP {e.response.status_code}: {e.response.text}"
            raise Exception(f"API request failed: {error_detail}") from e
        except httpx.RequestError as e:
            raise Exception(f"Request error: {str(e)}") from e

    async def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a POST request to the API"""
        return await self._request("POST", endpoint, json=data)

    async def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a GET request to the API"""
        return await self._request("GET", endpoint, params=params)
