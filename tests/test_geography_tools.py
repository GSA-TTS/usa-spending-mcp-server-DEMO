"""Tests for geography spending tools using FastMCP Client."""

from unittest.mock import AsyncMock

import pytest
from fastmcp import FastMCP
from fastmcp.client import Client

from usa_spending_mcp_server.tools.geography_spending import register_geography_tools

SAMPLE_GEO_RESPONSE = {
    "results": [
        {"shape_code": "CA", "aggregated_amount": 987654321.00, "display_name": "California"},
        {"shape_code": "TX", "aggregated_amount": 876543210.00, "display_name": "Texas"},
    ]
}

SAMPLE_SUMMARY_RESPONSE = {"results": {"transaction_count": 5432, "obligations": 9876543210.00}}

SAMPLE_CATEGORY_RESPONSE = {
    "category": "awarding_agency",
    "results": [{"id": 97, "name": "Department of Defense", "amount": 5678901234.00}],
}

MINIMAL_GEO_REQUEST = {
    "geography_search_request": {
        "scope": "place_of_performance",
        "geo_layer": "state",
        "geo_layer_filters": ["CA", "TX"],
        "filters": {"time_period": [{"start_date": "2023-10-01", "end_date": "2024-09-30"}]},
    }
}


@pytest.fixture
def mock_geo_client():
    client = AsyncMock()

    async def default_side_effect(endpoint, _data):
        if "spending_by_geography" in endpoint:
            return SAMPLE_GEO_RESPONSE
        if "transaction_spending_summary" in endpoint:
            return SAMPLE_SUMMARY_RESPONSE
        if "spending_by_category" in endpoint:
            return SAMPLE_CATEGORY_RESPONSE
        return {}

    client.post.side_effect = default_side_effect
    return client


@pytest.fixture
async def geo_mcp_client(mock_geo_client):
    mcp = FastMCP("test-geo")
    register_geography_tools(mcp, mock_geo_client)
    async with Client(transport=mcp) as client:
        yield client


class TestSearchSpendingByGeography:
    async def test_returns_all_three_sections(self, geo_mcp_client):
        """Response includes geography, summary, and categories sections."""
        result = await geo_mcp_client.call_tool("search_spending_by_geography", MINIMAL_GEO_REQUEST)
        data = result.data

        assert "geography" in data
        assert "summary" in data
        assert "categories" in data

    async def test_geography_section_has_results(self, geo_mcp_client):
        """Geography section contains results from spending_by_geography."""
        result = await geo_mcp_client.call_tool("search_spending_by_geography", MINIMAL_GEO_REQUEST)
        data = result.data

        assert data["geography"]["results"] == SAMPLE_GEO_RESPONSE["results"]
        assert data["geography"]["scope"] == "place_of_performance"
        assert data["geography"]["geo_layer"] == "state"

    async def test_summary_section_has_totals(self, geo_mcp_client):
        """Summary section contains transaction_spending_summary results."""
        result = await geo_mcp_client.call_tool("search_spending_by_geography", MINIMAL_GEO_REQUEST)
        data = result.data

        assert data["summary"] == SAMPLE_SUMMARY_RESPONSE["results"]

    async def test_categories_section_has_agency_breakdown(self, geo_mcp_client):
        """Categories section contains awarding agency breakdown."""
        result = await geo_mcp_client.call_tool("search_spending_by_geography", MINIMAL_GEO_REQUEST)
        data = result.data

        assert data["categories"]["category"] == "awarding_agency"
        assert data["categories"]["results"] == SAMPLE_CATEGORY_RESPONSE["results"]

    async def test_supplementary_failure_degrades_gracefully(self, mock_geo_client):
        """Supplementary API failure returns error key without failing the call."""

        async def failing_side_effect(endpoint, _data):
            if "transaction_spending_summary" in endpoint:
                raise Exception("timeout")
            if "spending_by_geography" in endpoint:
                return SAMPLE_GEO_RESPONSE
            if "spending_by_category" in endpoint:
                return SAMPLE_CATEGORY_RESPONSE
            return {}

        mock_geo_client.post.side_effect = failing_side_effect

        mcp = FastMCP("test")
        register_geography_tools(mcp, mock_geo_client)
        async with Client(transport=mcp) as client:
            result = await client.call_tool("search_spending_by_geography", MINIMAL_GEO_REQUEST)
            data = result.data

        assert "geography" in data
        assert "error" in data["summary"]
        assert "categories" in data

    async def test_primary_failure_returns_error(self, mock_geo_client):
        """Primary geography API failure returns top-level error."""

        async def failing_side_effect(endpoint, _data):
            if "spending_by_geography" in endpoint:
                raise Exception("API down")
            return {}

        mock_geo_client.post.side_effect = failing_side_effect

        mcp = FastMCP("test")
        register_geography_tools(mcp, mock_geo_client)
        async with Client(transport=mcp) as client:
            result = await client.call_tool("search_spending_by_geography", MINIMAL_GEO_REQUEST)
            data = result.data

        assert "error" in data
