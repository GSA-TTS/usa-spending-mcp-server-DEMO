"""Shared pytest fixtures for USA Spending MCP Server tests."""

from unittest.mock import AsyncMock

import pytest
from fastmcp import FastMCP
from fastmcp.client import Client

from usa_spending_mcp_server.tools.award_spending import register_award_search_tools
from usa_spending_mcp_server.tools.reference_tools import register_reference_tools

SAMPLE_AWARDS_RESPONSE = {
    "results": [
        {
            "Award ID": "CONT_AWD_001",
            "Recipient Name": "ACME Corp",
            "Award Amount": 1000000,
            "Awarding Agency": "Department of Defense",
        }
    ],
    "page_metadata": {"hasNext": True, "page": 1, "limit": 100, "total": 500},
}

SAMPLE_AWARDS_RESPONSE_NO_NEXT = {
    "results": [{"Award ID": "CONT_AWD_001", "Recipient Name": "ACME Corp"}],
    "page_metadata": {"hasNext": False, "page": 1, "limit": 100, "total": 1},
}

SAMPLE_AWARD_COUNT_RESPONSE = {
    "results": {"contracts": 400, "grants": 100, "loans": 0, "direct_payments": 0, "other": 0}
}

SAMPLE_SPENDING_SUMMARY_RESPONSE = {
    "results": {"transaction_count": 500, "obligations": 9876543210.00}
}

SAMPLE_SPENDING_OVER_TIME_RESPONSE = {
    "group": "fiscal_year",
    "results": [
        {"time_period": {"fiscal_year": "2023"}, "aggregated_amount": 1234567.89},
        {"time_period": {"fiscal_year": "2024"}, "aggregated_amount": 9876543.21},
    ],
}

SAMPLE_GEOGRAPHY_RESPONSE = {
    "results": [
        {"shape_code": "CA", "aggregated_amount": 987654321.00, "display_name": "California"},
        {"shape_code": "TX", "aggregated_amount": 876543210.00, "display_name": "Texas"},
    ]
}

SAMPLE_CATEGORY_RESPONSE = {
    "category": "awarding_agency",
    "results": [
        {"id": 97, "name": "Department of Defense", "amount": 5678901234.00},
    ],
}


@pytest.fixture
def mock_usa_client():
    """Mock USASpendingClient with default happy-path responses."""
    client = AsyncMock()
    client.post.side_effect = _default_post_side_effect
    client.get.return_value = {"results": []}
    return client


async def _default_post_side_effect(endpoint, _data):
    """Return appropriate mock response based on endpoint."""
    if "spending_by_award_count" in endpoint:
        return SAMPLE_AWARD_COUNT_RESPONSE
    if "transaction_spending_summary" in endpoint:
        return SAMPLE_SPENDING_SUMMARY_RESPONSE
    if "spending_over_time" in endpoint:
        return SAMPLE_SPENDING_OVER_TIME_RESPONSE
    if "spending_by_geography" in endpoint:
        return SAMPLE_GEOGRAPHY_RESPONSE
    if "spending_by_category" in endpoint:
        return SAMPLE_CATEGORY_RESPONSE
    if "spending_by_award" in endpoint:
        return SAMPLE_AWARDS_RESPONSE
    return {}


@pytest.fixture
async def award_mcp_client(mock_usa_client):
    """FastMCP Client with award tools registered and HTTP calls mocked."""
    mcp = FastMCP("test-awards")
    register_award_search_tools(mcp, mock_usa_client)
    async with Client(transport=mcp) as client:
        yield client


@pytest.fixture
async def reference_mcp_client(mock_usa_client):
    """FastMCP Client with reference tools registered and HTTP calls mocked."""
    mcp = FastMCP("test-reference")
    register_reference_tools(mcp, mock_usa_client)
    async with Client(transport=mcp) as client:
        yield client
