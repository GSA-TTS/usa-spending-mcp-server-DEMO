import json
import logging
from typing import Optional

from fastmcp import FastMCP

from usa_spending_mcp_server.client import USASpendingClient

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


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
        naics_codes: Optional[str] = None,
        psc_codes: Optional[str] = None,
        cfda_codes: Optional[str] = None,
        start_date: str = "2023-10-01",
        end_date: str = "2024-09-30",
        min_award_amount: Optional[float] = None,
        max_award_amount: Optional[float] = None,
        subawards: bool = False,
        page: int = 1,
        limit: int = 100,
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
            agencies: Agency names to filter by
            recipients: Recipient names to search for
            naics_codes: NAICS industry codes to filter by
            psc_codes: Product/Service codes to filter by
            cfda_codes: CFDA program codes to filter by
            start_date: Start date in YYYY-MM-DD format (required)
            end_date: End date in YYYY-MM-DD format (required)
            min_award_amount: Minimum award amount
            max_award_amount: Maximum award amount
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
            payload = {
                "scope": scope,
                "geo_layer": geo_layer,
                "geo_layer_filters": [
                    code.strip() for code in geo_layer_filters.split(",")
                ],
                "subawards": subawards,
                "page": page,
                "limit": limit,
                "sort": sort,
                "order": order,
                "filters": {"time_period": []},
            }

            # Add time period filter (required by API)
            payload["filters"]["time_period"] = [
                {"start_date": start_date, "end_date": end_date}
            ]

            if award_types:
                payload["filters"]["award_type_codes"] = award_types.split(",")

            if agencies:
                payload["filters"]["agencies"] = [
                    {"name": name.strip()} for name in agencies.split(",")
                ]

            if recipients:
                payload["filters"]["recipient_search_text"] = recipients.split(",")

            if naics_codes:
                payload["filters"]["naics_codes"] = naics_codes.split(",")

            if psc_codes:
                payload["filters"]["psc_codes"] = psc_codes.split(",")

            if cfda_codes:
                payload["filters"]["cfda_codes"] = cfda_codes.split(",")

            if min_award_amount is not None or max_award_amount is not None:
                payload["filters"]["award_amounts"] = {}
                if min_award_amount is not None:
                    payload["filters"]["award_amounts"]["min"] = min_award_amount
                if max_award_amount is not None:
                    payload["filters"]["award_amounts"]["max"] = max_award_amount

            # Make API call
            response = await client.post("search/spending_by_geography/", payload)

            # Return raw API response
            return json.dumps(response, indent=2)

        except Exception as e:
            return f"Error searching spending by geography: {str(e)}"
