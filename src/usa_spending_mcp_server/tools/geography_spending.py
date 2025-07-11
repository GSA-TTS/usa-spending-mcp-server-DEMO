from typing import Any

from fastmcp import FastMCP

from usa_spending_mcp_server.client import USASpendingClient
from usa_spending_mcp_server.models.geography_spending_models import (
    GeographySearchRequest,
)


def register_geography_tools(mcp: FastMCP, client: USASpendingClient):
    """Register geography spending tool"""

    @mcp.tool()
    async def search_spending_by_geography(
        geography_search_request: GeographySearchRequest,
    ) -> Any:
        """
        Search USA government spending data by geographic location.

        Args:
            scope: Geographic scope - 'place_of_performance' (where work was performed) or
                'recipient_location' (where recipient is located)
            geo_layer: Geographic aggregation level - 'state', 'county', 'district', or 'zip'
            geo_layer_filters: REQUIRED - Comma-separated list of geographic codes to filter by:
                - For states: 2-letter postal codes (WA, CA) or 2-digit FIPS codes (53, 06)
                - For counties: 5-digit FIPS codes (53033 for King County, WA)
                - For districts: State code + district (WA01, CA12)
                - For ZIP: 5-digit ZIP codes (98101, 90210)
            award_types: Award type codes to filter by (e.g., 'A', 'B', 'C', 'D')
            agencies: Agency names to filter by. Format options:
                - Just name: "Department of Defense" (defaults to awarding:toptier)
                - type:name: "awarding:Department of Defense"
                - subtier:top_tier_name:name:
                    "awarding:subtier:Department of Defense:Office of Inspector General"
                - type:subtier:top_tier_name:name:
                    "awarding:subtier:Department of Defense:Office of Inspector General"
                - Multiple agencies:
                    "Department of Defense,Department of Health and Human Services"
            recipients: Recipient names to search for (comma-separated)
            start_date: Start date in YYYY-MM-DD format (required)
            end_date: End date in YYYY-MM-DD format (required)
            subawards: Include subaward data (default: False)
            page: Page number for pagination (default: 1)
            limit: Number of results per page (default: 100, max: 100)
            sort: Sort field (default: 'aggregated_amount')
            order: Sort order - 'asc' or 'desc' (default: 'desc')

        Returns:
            Raw API response data as JSON string
        """

        try:
            # Make API call
            response = await client.post(
                "search/spending_by_geography/",
                geography_search_request.model_dump(exclude_none=True),
            )

            # Return raw API response
            return response

        except Exception as e:
            return f"Error searching spending by geography: {str(e)}"
