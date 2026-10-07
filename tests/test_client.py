"""Security-focused tests for the shared USAspending API client."""

from unittest.mock import AsyncMock

import httpx
import pytest

from usa_spending_mcp_server.client import USASpendingAPIError, USASpendingClient


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://example.com/data",
        "//example.com/data",
        "../data",
        "awards/../data",
        "awards/%2e%2e/data",
        "awards\\data",
        "awards/data?next=internal",
        "awards/data#fragment",
        "awards/\ndata",
    ],
)
async def test_rejects_non_normalized_relative_endpoints(endpoint):
    client = USASpendingClient()
    client.client.request = AsyncMock()

    try:
        with pytest.raises(ValueError, match="normalized relative API path"):
            await client.get(endpoint)
        client.client.request.assert_not_awaited()
    finally:
        await client.client.aclose()


async def test_http_error_does_not_disclose_response_body():
    sensitive_marker = "synthetic-secret-123"
    request = httpx.Request("GET", "https://api.usaspending.gov/api/v2/awards/test/")
    response = httpx.Response(
        422,
        request=request,
        json={"debug": sensitive_marker, "internal_path": "/private/service"},
    )
    client = USASpendingClient()
    client.client.request = AsyncMock(return_value=response)

    try:
        with pytest.raises(USASpendingAPIError) as exc_info:
            await client.get("awards/test/")
        assert str(exc_info.value) == "USAspending API request failed (HTTP 422)"
        assert sensitive_marker not in str(exc_info.value)
        assert "/private/service" not in str(exc_info.value)
    finally:
        await client.client.aclose()


async def test_redirects_are_not_followed():
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(302, headers={"Location": "http://169.254.169.254/latest/meta-data/"})

    client = USASpendingClient()
    await client.client.aclose()
    client.client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        follow_redirects=False,
    )

    try:
        with pytest.raises(USASpendingAPIError, match=r"HTTP 302"):
            await client.get("awards/test/")
        assert len(requests) == 1
        assert requests[0].url.host == "api.usaspending.gov"
    finally:
        await client.client.aclose()
