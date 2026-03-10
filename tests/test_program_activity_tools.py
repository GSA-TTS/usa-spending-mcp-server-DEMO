"""Tests for program activity tools using FastMCP Client."""

from unittest.mock import AsyncMock

import pytest
from fastmcp import FastMCP
from fastmcp.client import Client

from usa_spending_mcp_server.tools.program_activity_spending import (
    register_program_activity_tools,
)


@pytest.fixture
def mock_pa_client():
    client = AsyncMock()
    client.get.return_value = {
        "results": [{"name": "IT Spending", "obligated_amount": 1000000}],
        "page_metadata": {"hasNext": False},
    }
    return client


@pytest.fixture
async def pa_mcp_client(mock_pa_client):
    mcp = FastMCP("test-pa")
    register_program_activity_tools(mcp, mock_pa_client)
    async with Client(transport=mcp) as client:
        yield client


class TestListProgramActivities:
    async def test_leading_zero_toptier_code_preserved(self, mock_pa_client):
        """toptier_code '012' must not be stripped to '12' — leading zeros required."""
        mcp = FastMCP("test")
        register_program_activity_tools(mcp, mock_pa_client)
        async with Client(transport=mcp) as client:
            await client.call_tool("list_program_activities", {"toptier_code": "012"})

        call_args = mock_pa_client.get.call_args
        endpoint = call_args[0][0]
        assert "agency/012/" in endpoint, f"Expected 'agency/012/' in endpoint, got: {endpoint}"

    async def test_three_digit_toptier_code_preserved(self, mock_pa_client):
        """toptier_code '097' (DOD) builds correct URL."""
        mcp = FastMCP("test")
        register_program_activity_tools(mcp, mock_pa_client)
        async with Client(transport=mcp) as client:
            await client.call_tool("list_program_activities", {"toptier_code": "097"})

        call_args = mock_pa_client.get.call_args
        endpoint = call_args[0][0]
        assert "agency/097/" in endpoint

    async def test_returns_api_response(self, pa_mcp_client):
        """Tool returns the API response."""
        result = await pa_mcp_client.call_tool("list_program_activities", {"toptier_code": "097"})
        assert result.data is not None
