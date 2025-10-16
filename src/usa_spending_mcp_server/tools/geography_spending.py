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
            geography_search_request: Structured request object containing:
                - scope: Geographic scope - 'place_of_performance' (where
                    work was performed) or
                    'recipient_location' (where recipient is located)
                - geo_layer: Geographic aggregation level - 'state', 'county',
                    'district', or 'zip'
                - geo_layer_filters: REQUIRED - List of geographic codes to filter by:
                    - For states: 2-letter postal codes (WA, CA) or 2-digit FIPS
                        codes (53, 06)
                    - For counties: 5-digit FIPS codes (53033 for King County, WA)
                    - For districts: State code + district (WA01, CA12)
                    - For ZIP: 5-digit ZIP codes (98101, 90210)
                - filters: GeographySearchFilters with optional fields:
                    - time_period: List of TimePeriod objects with start_date
                        and end_date (YYYY-MM-DD)
                    - award_type_codes: List of award type codes (A, B, C, D, etc.)
                    - agencies: List of Agency objects with name, type
                        (awarding/funding), tier (toptier/subtier)
                    - recipient_search_text: List of recipient names to search for
                    - recipient_type_names: List of recipient type names to filter by
                        (e.g., 'category_business', 'sole_proprietorship', 'nonprofit',
                        'community_development_corporations', 'tribally_owned_firm')
                - pagination: BasePagination with page, limit, order (asc/desc)
                - sort: Sort field (default: 'aggregated_amount')
                - subawards: Include subaward data (default: False)

        Returns:
            Raw API response data as JSON string containing:
            - results: Array of geographic spending records with location data and amounts
            - page_metadata: Pagination information

        Examples:
            - Search spending in Washington state:
                GeographySearchRequest(
                    scope="place_of_performance",
                    geo_layer="state",
                    geo_layer_filters=["WA"],
                    filters=GeographySearchFilters(time_period=
                        [TimePeriod(start_date="2023-10-01", end_date="2024-09-30")])
                )
            - Search DOD contracts in King County, WA:
                GeographySearchRequest(
                    scope="place_of_performance",
                    geo_layer="county",
                    geo_layer_filters=["53033"],
                    filters=GeographySearchFilters(
                        agencies=[Agency(name="Department of Defense")],
                        award_type_codes=["A", "B", "C", "D"]
                    )
                )
            - Search by ZIP codes with recipient location:
                GeographySearchRequest(
                    scope="recipient_location",
                    geo_layer="zip",
                    geo_layer_filters=["98101", "90210"],
                    filters=GeographySearchFilters(time_period=
                        [TimePeriod(start_date="2024-01-01", end_date="2024-12-31")])
                )
            - Search for nonprofit recipients in California:
                GeographySearchRequest(
                    scope="recipient_location",
                    geo_layer="state",
                    geo_layer_filters=["CA"],
                    filters=GeographySearchFilters(
                        time_period=[TimePeriod(start_date="2024-01-01", end_date="2024-12-31")],
                        recipient_type_names=["nonprofit"]
                    )
                )
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
