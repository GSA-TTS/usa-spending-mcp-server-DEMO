import re
from typing import Any
from urllib.parse import urlsplit

import httpx


class USASpendingAPIError(Exception):
    """Caller-safe error raised when the USAspending API request fails."""


class USASpendingClient:
    """Shared HTTP client for USA Spending API"""

    BASE_URL = "https://api.usaspending.gov/api/v2"

    def __init__(self, timeout: float = 30.0):
        self.client = httpx.AsyncClient(
            timeout=timeout,
            headers={"Content-Type": "application/json"},
            follow_redirects=False,
        )

    async def _request(self, method: str, endpoint: str, **kwargs) -> dict[str, Any]:
        """Make HTTP request with unified error handling"""
        parsed_endpoint = urlsplit(endpoint)
        if (
            parsed_endpoint.scheme
            or parsed_endpoint.netloc
            or parsed_endpoint.query
            or parsed_endpoint.fragment
            or "\\" in endpoint
            or not re.fullmatch(r"/?[A-Za-z0-9_/-]+", endpoint)
            or any(segment in ("", ".", "..") for segment in endpoint.strip("/").split("/"))
        ):
            raise ValueError("Endpoint must be a normalized relative API path")

        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"

        try:
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise USASpendingAPIError(
                f"USAspending API request failed (HTTP {e.response.status_code})"
            ) from e
        except httpx.RequestError as e:
            raise USASpendingAPIError("USAspending API request failed") from e

    async def post(self, endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
        """Make a POST request to the API"""
        return await self._request("POST", endpoint, json=data)

    async def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a GET request to the API"""
        return await self._request("GET", endpoint, params=params)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.client.aclose()
