from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from usa_spending_mcp_server.client import USASpendingClient
from usa_spending_mcp_server.models.common_models import BaseSearchFilters
from usa_spending_mcp_server.models.spending_over_time_models import TimeGroup


def register_spending_over_time_tools(mcp: FastMCP, client: USASpendingClient):
    """Register spending over time tools."""

    @mcp.tool()
    async def search_spending_over_time(
        filters: BaseSearchFilters,
        group: Annotated[
            TimeGroup,
            Field(
                description=(
                    "Time grouping: 'fiscal_year', 'quarter', or 'month'. "
                    "Use 'quarter' for seasonal patterns, 'month' for granular trends."
                )
            ),
        ] = TimeGroup.FISCAL_YEAR,
        subawards: Annotated[
            bool,
            Field(description="If True, return subaward spending over time."),
        ] = False,
    ) -> Any:
        """
        Get spending trends over time — standalone tool for time-series analysis.

        Returns aggregated obligation amounts grouped by fiscal year, quarter, or month.
        Supports the same filters as search_awards (time period, agencies, award types, etc.)
        but focuses purely on time-series data without returning individual awards.

        Use this for:
        - "How has spending changed over the last decade?"
        - "Which quarters have the highest spending?"
        - "What are the trends in grant vs contract spending?"
        - "How has agency X's spending changed year over year?"
        - Computing total obligation amounts for a filtered set of awards

        Args:
            filters: Search filters (same as search_awards):
                - time_period: REQUIRED. List of {start_date, end_date} in YYYY-MM-DD
                - award_type_codes: e.g. ["A","B","C","D"] for contracts
                - agencies: List of agency objects
                - keywords: e.g. ["broadband"]
                - recipient_search_text: e.g. ["Boeing"]
                - recipient_type_names: e.g. ["nonprofit"]
                - place_of_performance_locations: e.g. [{country: "USA", state: "CA"}]
                - recipient_locations: e.g. [{country: "USA", state: "TX"}]
            group: Time grouping — 'fiscal_year', 'quarter', or 'month'
            subawards: If True, return subaward spending instead of prime awards

        Returns:
            Dict with:
            - group: The grouping used (fiscal_year/quarter/month)
            - results: Array of time period objects, each with:
                - time_period: {fiscal_year, [quarter], [month]}
                - aggregated_amount: Total obligations in that period
                - Contract_Obligations, Grant_Obligations, etc.

        Examples:
            # DOD contract spending by fiscal year, last 5 years
            search_spending_over_time(
                filters=BaseSearchFilters(
                    time_period=[TimePeriod(start_date="2019-10-01", end_date="2024-09-30")],
                    agencies=[Agency(name="Department of Defense")],
                    award_type_codes=["A","B","C","D"]
                ),
                group="fiscal_year"
            )

            # Quarterly spending patterns for all agencies
            search_spending_over_time(
                filters=BaseSearchFilters(
                    time_period=[TimePeriod(start_date="2022-10-01", end_date="2023-09-30")]
                ),
                group="quarter"
            )
        """
        try:
            payload = {
                "group": group.value,
                "filters": filters.model_dump(exclude_none=True),
                "subawards": subawards,
            }
            response = await client.post("search/spending_over_time/", payload)
            return {
                "group": response.get("group", group.value),
                "results": response.get("results", []),
            }
        except Exception as e:
            return {"error": f"Error fetching spending over time: {e}"}

    @mcp.tool()
    async def search_new_awards_over_time(
        filters: BaseSearchFilters,
        group: Annotated[
            TimeGroup,
            Field(description="Time grouping: 'fiscal_year', 'quarter', or 'month'."),
        ] = TimeGroup.FISCAL_YEAR,
    ) -> Any:
        """
        Get count of new awards created over time.

        Returns the number of new awards in each time period. Useful for tracking
        how award activity (not just spending amounts) changes over time.

        Args:
            filters: Search filters (same as search_awards)
            group: Time grouping — 'fiscal_year', 'quarter', or 'month'

        Returns:
            Dict with results array, each entry has time_period and new_award_count_in_period.
        """
        try:
            payload = {
                "group": group.value,
                "filters": filters.model_dump(exclude_none=True),
            }
            response = await client.post("search/new_awards_over_time/", payload)
            return {
                "group": response.get("group", group.value),
                "results": response.get("results", []),
            }
        except Exception as e:
            return {"error": f"Error fetching new awards over time: {e}"}
