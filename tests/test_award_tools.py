"""Tests for award spending tools using FastMCP Client."""

import base64
import json

from fastmcp import FastMCP
from fastmcp.client import Client

from tests.conftest import (
    SAMPLE_AWARD_COUNT_RESPONSE,
    SAMPLE_AWARDS_RESPONSE,
    SAMPLE_AWARDS_RESPONSE_NO_NEXT,
    SAMPLE_CATEGORY_RESPONSE,
    SAMPLE_GEOGRAPHY_RESPONSE,
    SAMPLE_SPENDING_OVER_TIME_RESPONSE,
    SAMPLE_SPENDING_SUMMARY_RESPONSE,
)
from usa_spending_mcp_server.tools.award_spending import register_award_search_tools

MINIMAL_REQUEST = {
    "award_search_request": {
        "filters": {"time_period": [{"start_date": "2023-10-01", "end_date": "2024-09-30"}]}
    }
}


class TestSearchAwards:
    """Tests for the search_awards tool."""

    async def test_first_call_returns_all_sections(self, award_mcp_client):
        """First call (no cursor) returns awards, summary, trends, geography, categories."""
        result = await award_mcp_client.call_tool("search_awards", MINIMAL_REQUEST)
        data = result.data

        assert "awards" in data
        assert "summary" in data
        assert "trends" in data
        assert "geography" in data
        assert "categories" in data

    async def test_first_call_awards_section_has_results(self, award_mcp_client):
        """Awards section contains results from spending_by_award."""
        result = await award_mcp_client.call_tool("search_awards", MINIMAL_REQUEST)
        data = result.data

        assert data["awards"]["results"] == SAMPLE_AWARDS_RESPONSE["results"]
        assert data["awards"]["page_metadata"]["hasNext"] is True

    async def test_first_call_has_next_true_returns_cursor(self, award_mcp_client):
        """When hasNext=True, next_cursor is returned."""
        result = await award_mcp_client.call_tool("search_awards", MINIMAL_REQUEST)
        data = result.data

        assert data["awards"]["next_cursor"] is not None
        assert isinstance(data["awards"]["next_cursor"], str)
        # Cursor should decode to page 2
        decoded = json.loads(base64.b64decode(data["awards"]["next_cursor"]))
        assert decoded["page"] == 2

    async def test_first_call_has_next_false_returns_no_cursor(self, mock_usa_client):
        """When hasNext=False, next_cursor is null."""
        mock_usa_client.post.side_effect = None
        mock_usa_client.post.return_value = SAMPLE_AWARDS_RESPONSE_NO_NEXT

        mcp = FastMCP("test")
        register_award_search_tools(mcp, mock_usa_client)
        async with Client(transport=mcp) as client:
            result = await client.call_tool("search_awards", MINIMAL_REQUEST)
            data = result.data

        assert data["awards"]["next_cursor"] is None

    async def test_cursor_call_returns_only_awards_section(self, mock_usa_client):
        """Cursor-based call returns only awards section (no aggregate calls)."""
        mock_usa_client.post.side_effect = None
        mock_usa_client.post.return_value = SAMPLE_AWARDS_RESPONSE

        mcp = FastMCP("test")
        register_award_search_tools(mcp, mock_usa_client)

        cursor = base64.b64encode(json.dumps({"page": 2}).encode()).decode()
        async with Client(transport=mcp) as client:
            result = await client.call_tool("search_awards", {**MINIMAL_REQUEST, "cursor": cursor})
            data = result.data

        assert "awards" in data
        assert "summary" not in data
        assert "trends" not in data
        assert "geography" not in data
        assert "categories" not in data

    async def test_cursor_advances_to_correct_page(self, mock_usa_client):
        """Cursor correctly passes page=2 to the awards endpoint."""
        mock_usa_client.post.side_effect = None
        mock_usa_client.post.return_value = SAMPLE_AWARDS_RESPONSE

        mcp = FastMCP("test")
        register_award_search_tools(mcp, mock_usa_client)

        cursor = base64.b64encode(json.dumps({"page": 2}).encode()).decode()
        async with Client(transport=mcp) as client:
            await client.call_tool("search_awards", {**MINIMAL_REQUEST, "cursor": cursor})

        # Verify the post was called with page=2
        call_args = mock_usa_client.post.call_args
        payload = call_args[0][1]
        assert payload["pagination"]["page"] == 2

    async def test_include_time_trends_false_skips_spending_over_time(self, mock_usa_client):
        """Setting include_time_trends=False skips the spending_over_time call."""
        calls_made = []

        async def tracking_side_effect(endpoint, _data):
            calls_made.append(endpoint)
            if "spending_by_award_count" in endpoint:
                return SAMPLE_AWARD_COUNT_RESPONSE
            if "transaction_spending_summary" in endpoint:
                return SAMPLE_SPENDING_SUMMARY_RESPONSE
            if "spending_by_geography" in endpoint:
                return SAMPLE_GEOGRAPHY_RESPONSE
            if "spending_by_category" in endpoint:
                return SAMPLE_CATEGORY_RESPONSE
            return SAMPLE_AWARDS_RESPONSE

        mock_usa_client.post.side_effect = tracking_side_effect

        mcp = FastMCP("test")
        register_award_search_tools(mcp, mock_usa_client)
        async with Client(transport=mcp) as client:
            await client.call_tool(
                "search_awards", {**MINIMAL_REQUEST, "include_time_trends": False}
            )

        assert not any("spending_over_time" in ep for ep in calls_made)

    async def test_include_geography_false_skips_geography_call(self, mock_usa_client):
        """Setting include_geography=False skips the spending_by_geography call."""
        calls_made = []

        async def tracking_side_effect(endpoint, _data):
            calls_made.append(endpoint)
            if "spending_by_award_count" in endpoint:
                return SAMPLE_AWARD_COUNT_RESPONSE
            if "transaction_spending_summary" in endpoint:
                return SAMPLE_SPENDING_SUMMARY_RESPONSE
            if "spending_over_time" in endpoint:
                return SAMPLE_SPENDING_OVER_TIME_RESPONSE
            if "spending_by_category" in endpoint:
                return SAMPLE_CATEGORY_RESPONSE
            return SAMPLE_AWARDS_RESPONSE

        mock_usa_client.post.side_effect = tracking_side_effect

        mcp = FastMCP("test")
        register_award_search_tools(mcp, mock_usa_client)
        async with Client(transport=mcp) as client:
            await client.call_tool("search_awards", {**MINIMAL_REQUEST, "include_geography": False})

        assert not any("spending_by_geography" in ep for ep in calls_made)

    async def test_include_categories_false_skips_category_call(self, mock_usa_client):
        """Setting include_categories=False skips the spending_by_category call."""
        calls_made = []

        async def tracking_side_effect(endpoint, _data):
            calls_made.append(endpoint)
            if "spending_by_award_count" in endpoint:
                return SAMPLE_AWARD_COUNT_RESPONSE
            if "transaction_spending_summary" in endpoint:
                return SAMPLE_SPENDING_SUMMARY_RESPONSE
            if "spending_over_time" in endpoint:
                return SAMPLE_SPENDING_OVER_TIME_RESPONSE
            if "spending_by_geography" in endpoint:
                return SAMPLE_GEOGRAPHY_RESPONSE
            return SAMPLE_AWARDS_RESPONSE

        mock_usa_client.post.side_effect = tracking_side_effect

        mcp = FastMCP("test")
        register_award_search_tools(mcp, mock_usa_client)
        async with Client(transport=mcp) as client:
            await client.call_tool(
                "search_awards", {**MINIMAL_REQUEST, "include_categories": False}
            )

        assert not any("spending_by_category" in ep for ep in calls_made)

    async def test_supplementary_failure_graceful_degradation(self, mock_usa_client):
        """Supplementary API failure returns error key without failing full call."""

        async def failing_side_effect(endpoint, _data):
            if "spending_over_time" in endpoint:
                raise Exception("API timeout")
            if "spending_by_award_count" in endpoint:
                return SAMPLE_AWARD_COUNT_RESPONSE
            if "transaction_spending_summary" in endpoint:
                return SAMPLE_SPENDING_SUMMARY_RESPONSE
            if "spending_by_geography" in endpoint:
                return SAMPLE_GEOGRAPHY_RESPONSE
            if "spending_by_category" in endpoint:
                return SAMPLE_CATEGORY_RESPONSE
            return SAMPLE_AWARDS_RESPONSE

        mock_usa_client.post.side_effect = failing_side_effect

        mcp = FastMCP("test")
        register_award_search_tools(mcp, mock_usa_client)
        async with Client(transport=mcp) as client:
            result = await client.call_tool("search_awards", MINIMAL_REQUEST)
            data = result.data

        assert "awards" in data
        assert "error" in data["trends"]
        assert "summary" in data
        assert "geography" in data
        assert "categories" in data

    async def test_summary_contains_award_counts_and_totals(self, award_mcp_client):
        """Summary section contains both award_counts_by_type and totals."""
        result = await award_mcp_client.call_tool("search_awards", MINIMAL_REQUEST)
        data = result.data

        assert "award_counts_by_type" in data["summary"]
        assert "totals" in data["summary"]
        assert data["summary"]["award_counts_by_type"] == SAMPLE_AWARD_COUNT_RESPONSE["results"]
        assert data["summary"]["totals"] == SAMPLE_SPENDING_SUMMARY_RESPONSE["results"]

    async def test_trends_contains_spending_over_time(self, award_mcp_client):
        """Trends section contains spending_over_time results."""
        result = await award_mcp_client.call_tool("search_awards", MINIMAL_REQUEST)
        data = result.data

        assert data["trends"]["group"] == "fiscal_year"
        assert data["trends"]["results"] == SAMPLE_SPENDING_OVER_TIME_RESPONSE["results"]

    async def test_geography_contains_state_breakdown(self, award_mcp_client):
        """Geography section contains state-level breakdown."""
        result = await award_mcp_client.call_tool("search_awards", MINIMAL_REQUEST)
        data = result.data

        assert data["geography"]["scope"] == "place_of_performance"
        assert data["geography"]["geo_layer"] == "state"
        assert data["geography"]["results"] == SAMPLE_GEOGRAPHY_RESPONSE["results"]

    async def test_categories_contains_awarding_agency(self, award_mcp_client):
        """Categories section contains awarding agency breakdown."""
        result = await award_mcp_client.call_tool("search_awards", MINIMAL_REQUEST)
        data = result.data

        assert data["categories"]["category"] == "awarding_agency"
        assert data["categories"]["results"] == SAMPLE_CATEGORY_RESPONSE["results"]


class TestGetAwardDetails:
    """Tests for the get_award_details tool."""

    async def test_single_award_returns_result(self, mock_usa_client):
        """Single award ID returns data under that ID key."""
        mock_usa_client.get.return_value = {"id": "CONT_AWD_001", "amount": 1000000}

        mcp = FastMCP("test")
        register_award_search_tools(mcp, mock_usa_client)
        async with Client(transport=mcp) as client:
            result = await client.call_tool("get_award_details", {"award_ids": ["CONT_AWD_001"]})
            data = result.data

        assert data["success_count"] == 1
        assert "CONT_AWD_001" in data["results"]

    async def test_multiple_awards_parallel_fetch(self, mock_usa_client):
        """Multiple award IDs are fetched and all appear in results."""
        mock_usa_client.get.return_value = {"id": "test", "amount": 500}

        mcp = FastMCP("test")
        register_award_search_tools(mcp, mock_usa_client)
        async with Client(transport=mcp) as client:
            result = await client.call_tool(
                "get_award_details",
                {"award_ids": ["CONT_AWD_001", "CONT_AWD_002", "CONT_AWD_003"]},
            )
            data = result.data

        assert data["success_count"] == 3
        assert "CONT_AWD_001" in data["results"]
        assert "CONT_AWD_002" in data["results"]
        assert "CONT_AWD_003" in data["results"]

    async def test_failed_award_appears_in_errors(self, mock_usa_client):
        """Award ID that raises an exception appears in errors dict."""

        async def failing_get(endpoint, **_kwargs):
            if "CONT_BAD" in endpoint:
                raise Exception("Not found")
            return {"id": "ok", "amount": 100}

        mock_usa_client.get.side_effect = failing_get

        mcp = FastMCP("test")
        register_award_search_tools(mcp, mock_usa_client)
        async with Client(transport=mcp) as client:
            result = await client.call_tool(
                "get_award_details", {"award_ids": ["CONT_AWD_001", "CONT_BAD"]}
            )
            data = result.data

        assert data["success_count"] == 1
        assert data["error_count"] == 1
        assert "CONT_BAD" in data["errors"]
