import json
from typing import Optional

from fastmcp import FastMCP

from usa_spending_mcp_server.client import USASpendingClient
from usa_spending_mcp_server.models.geography_spending_models import (
    GeographySearchRequest,
)


def register_geography_tools(mcp: FastMCP, client: USASpendingClient):
    """Register geography spending tool"""

    @mcp.tool()
    async def search_spending_by_geography(
        scope: str,
        geo_layer: str,
        geo_layer_filters: str,
        award_types: Optional[str] = None,
        agencies: Optional[str] = None,
        recipients: Optional[str] = None,
        start_date: str = "2023-10-01",
        end_date: str = "2024-09-30",
        subawards: str = "False",
        page: str = "1",
        limit: str = "100",
        sort: str = "aggregated_amount",
        order: str = "desc",
    ) -> str:
        """
        Search USA government spending data by geographic location.

        Args:
            scope: Geographic scope - 'place_of_performance' (where work was performed) or 'recipient_location' (where recipient is located)
            geo_layer: Geographic aggregation level - 'state', 'county', 'district', or 'zip'
            geo_layer_filters: REQUIRED - Comma-separated list of geographic codes to filter by:
                - For states: 2-letter postal codes (WA, CA) or 2-digit FIPS codes (53, 06)
                - For counties: 5-digit FIPS codes (53033 for King County, WA)
                - For districts: State code + district (WA01, CA12)
                - For ZIP: 5-digit ZIP codes (98101, 90210)
            award_types: Award type codes to filter by (e.g., 'A', 'B', 'C', 'D')
            agencies: Agency names to filter by. Format options:
                - Just name: "Department of Defense" (defaults to awarding:toptier)
                - tier:name: "toptier:Department of Defense"
                - type:tier:name: "awarding:toptier:Department of Defense"
                - Multiple agencies: "Department of Defense,Department of Health and Human Services"
            recipients: Recipient names to search for (comma-separated)
            start_date: Start date in YYYY-MM-DD format (required)
            end_date: End date in YYYY-MM-DD format (required)
            subawards: Include subaward data (default: False)
            page: Page number for pagination (default: 1)
            limit: Number of results per page (default: 100, max: 500)
            sort: Sort field (default: 'aggregated_amount')
            order: Sort order - 'asc' or 'desc' (default: 'desc')

        Returns:
            Raw API response data as JSON string
        """

        try:
            # Build the request payload
            request = GeographySearchRequest.from_params(
                scope=scope,
                geo_layer=geo_layer,
                geo_layer_filters=geo_layer_filters,
                award_types=award_types,
                start_date=start_date,
                end_date=end_date,
                agencies=agencies,
                recipients=recipients,
                subawards=subawards,
                page=page,
                limit=limit,
                sort=sort,
                order=order,
            )

            # Make API call
            response = await client.post(
                "search/spending_by_geography/", request.to_api_payload()
            )

            # Return raw API response
            return json.dumps(response, indent=2)

        except Exception as e:
            return f"Error searching spending by geography: {str(e)}"
