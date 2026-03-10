"""Tests for recipient spending tools using FastMCP Client."""

import base64
import json
from unittest.mock import AsyncMock

import pytest
from fastmcp import FastMCP
from fastmcp.client import Client

from usa_spending_mcp_server.tools.recipient_spending import register_recipient_search_tools

SAMPLE_RECIPIENTS_WITH_NEXT = {
    "results": [{"id": "abc", "name": "ACME Corp", "amount": 5000000}],
    "page_metadata": {"hasNext": True, "page": 1, "limit": 100, "total": 500},
}

SAMPLE_RECIPIENTS_NO_NEXT = {
    "results": [{"id": "abc", "name": "ACME Corp", "amount": 5000000}],
    "page_metadata": {"hasNext": False, "page": 1, "limit": 100, "total": 1},
}

MINIMAL_RECIPIENT_REQUEST = {"recipient_search_request": {"keyword": "Boeing"}}


@pytest.fixture
def mock_recipient_client():
    client = AsyncMock()
    client.post.return_value = SAMPLE_RECIPIENTS_WITH_NEXT
    return client


@pytest.fixture
async def recipient_mcp_client(mock_recipient_client):
    mcp = FastMCP("test-recipients")
    register_recipient_search_tools(mcp, mock_recipient_client)
    async with Client(transport=mcp) as client:
        yield client


class TestSearchRecipients:
    async def test_has_next_true_returns_cursor(self, recipient_mcp_client):
        """When hasNext=True, next_cursor is returned."""
        result = await recipient_mcp_client.call_tool(
            "search_recipients", MINIMAL_RECIPIENT_REQUEST
        )
        data = result.data

        assert data["next_cursor"] is not None
        decoded = json.loads(base64.b64decode(data["next_cursor"]))
        assert decoded["page"] == 2

    async def test_has_next_false_returns_no_cursor(self, mock_recipient_client):
        """When hasNext=False, next_cursor is null."""
        mock_recipient_client.post.return_value = SAMPLE_RECIPIENTS_NO_NEXT

        mcp = FastMCP("test")
        register_recipient_search_tools(mcp, mock_recipient_client)
        async with Client(transport=mcp) as client:
            result = await client.call_tool("search_recipients", MINIMAL_RECIPIENT_REQUEST)
            data = result.data

        assert data["next_cursor"] is None

    async def test_cursor_advances_to_correct_page(self, mock_recipient_client):
        """Cursor-based call passes correct page number to API."""
        mock_recipient_client.post.return_value = SAMPLE_RECIPIENTS_WITH_NEXT

        cursor = base64.b64encode(json.dumps({"page": 3}).encode()).decode()

        mcp = FastMCP("test")
        register_recipient_search_tools(mcp, mock_recipient_client)
        async with Client(transport=mcp) as client:
            await client.call_tool(
                "search_recipients", {**MINIMAL_RECIPIENT_REQUEST, "cursor": cursor}
            )

        call_args = mock_recipient_client.post.call_args
        payload = call_args[0][1]
        assert payload["page"] == 3

    async def test_results_and_metadata_passed_through(self, recipient_mcp_client):
        """Results and page_metadata are included in response."""
        result = await recipient_mcp_client.call_tool(
            "search_recipients", MINIMAL_RECIPIENT_REQUEST
        )
        data = result.data

        assert data["results"] == SAMPLE_RECIPIENTS_WITH_NEXT["results"]
        assert data["page_metadata"] == SAMPLE_RECIPIENTS_WITH_NEXT["page_metadata"]
