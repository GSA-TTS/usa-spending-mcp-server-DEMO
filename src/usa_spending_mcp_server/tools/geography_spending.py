import asyncio
from typing import Any

from fastmcp import FastMCP

from usa_spending_mcp_server.client import USASpendingClient
from usa_spending_mcp_server.models.geography_spending_models import GeographySearchRequest


def register_geography_tools(mcp: FastMCP, client: USASpendingClient):
    """Register geography spending tool"""

    @mcp.tool()
    async def search_spending_by_geography(
        geography_search_request: GeographySearchRequest,
    ) -> Any:
        """
        Search USA government spending data by geographic location.

        Returns geographic spending breakdown alongside total summary and awarding agency
        breakdown for full context — three parallel API calls in one tool invocation.

        Args:
            geography_search_request: Structured request object containing:
                - scope: Geographic scope - 'place_of_performance' (where work was performed)
                    or 'recipient_location' (where recipient is located)
                - geo_layer: Geographic aggregation level - 'state', 'county', 'district', or 'zip'
                - geo_layer_filters: List of geographic codes to filter by:
                    - For states: 2-letter postal codes (WA, CA) or 2-digit FIPS codes
                    - For counties: 5-digit FIPS codes (53033 for King County, WA)
                    - For districts: State code + district (WA01, CA12)
                    - For ZIP: 5-digit ZIP codes (98101, 90210)
                - filters: GeographySearchFilters with optional fields:
                    - time_period: List of TimePeriod objects with start_date and end_date (YYYY-MM-DD)
                    - award_type_codes: List of award type codes (A, B, C, D, etc.)
                    - agencies: List of Agency objects
                    - recipient_search_text: List of recipient names to search for
                    - recipient_type_names: Recipient type names (e.g., 'nonprofit')
                - sort: Sort field (default: 'aggregated_amount')
                - subawards: Include subaward data (default: False)

        Returns:
            Dict with three sections:
            - geography: {scope, geo_layer, results} — geographic spending breakdown
            - summary: {transaction_count, obligations} — totals across the filtered scope
            - categories: {category, results} — awarding agency breakdown for the scope

            Supplementary sections (summary, categories) return {error: "..."} on failure
            without failing the whole call.

        Examples:
            - State-level spending in California:
                GeographySearchRequest(scope="place_of_performance", geo_layer="state",
                    geo_layer_filters=["CA"],
                    filters=GeographySearchFilters(
                        time_period=[TimePeriod(start_date="2023-10-01", end_date="2024-09-30")]
                    ))
            - County-level DOD contracts in Washington:
                GeographySearchRequest(scope="place_of_performance", geo_layer="county",
                    geo_layer_filters=["53033"],
                    filters=GeographySearchFilters(
                        agencies=[Agency(name="Department of Defense")],
                        award_type_codes=["A","B","C","D"]
                    ))
        """
        request_payload = geography_search_request.to_api_payload()
        base_filters = geography_search_request.filters.model_dump(exclude_none=True)

        async def fetch_geography():
            return await client.post("search/spending_by_geography/", request_payload)

        async def fetch_summary():
            return await client.post(
                "search/transaction_spending_summary/", {"filters": base_filters}
            )

        async def fetch_categories():
            return await client.post(
                "search/spending_by_category/awarding_agency/",
                {"filters": base_filters},
            )

        # Build tasks: always fetch geography + categories.
        # transaction_spending_summary requires keywords — skip when absent.
        has_keywords = bool(base_filters.get("keywords"))
        tasks = [fetch_geography(), fetch_categories()]
        if has_keywords:
            tasks.insert(1, fetch_summary())

        results = await asyncio.gather(*tasks, return_exceptions=True)

        geo_result = results[0]
        if has_keywords:
            summary_result = results[1]
            category_result = results[2]
        else:
            summary_result = None
            category_result = results[1]

        if isinstance(geo_result, Exception):
            return {"error": f"Error fetching geography data: {geo_result}"}

        def _safe(result: Any, transform=None) -> Any:
            if isinstance(result, Exception):
                return {"error": str(result)}
            return transform(result) if transform else result

        return {
            "geography": {
                "scope": geography_search_request.scope,
                "geo_layer": geography_search_request.geo_layer,
                "results": geo_result.get("results", []),
            },
            "summary": (
                _safe(summary_result, lambda r: r.get("results", r))
                if summary_result is not None
                else {"note": "transaction_spending_summary requires keywords; skipped"}
            ),
            "categories": _safe(
                category_result,
                lambda r: {
                    "category": "awarding_agency",
                    "results": r.get("results", []),
                },
            ),
        }
