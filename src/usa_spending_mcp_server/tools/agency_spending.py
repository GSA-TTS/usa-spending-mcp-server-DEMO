import json
import logging
from typing import Optional

from fastmcp import FastMCP

from usa_spending_mcp_server.client import USASpendingClient

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def register_agency_tools(mcp: FastMCP, client: USASpendingClient):
    """Register agency spending tools"""

    @mcp.tool()
    async def get_agency_overview(
        toptier_code: str,
        fiscal_year: Optional[int] = None,
    ) -> str:
        """
        Get agency overview information including total spending, award counts, and basic details.

        Args:
            toptier_code: The agency's top-tier code (e.g., '097' for DOD, '020' for Treasury)
            fiscal_year: Optional fiscal year to filter data (defaults to current fiscal year)

        Returns:
            Raw API response data as JSON string containing agency overview
        """
        try:
            params = {}
            if fiscal_year is not None:
                params["fiscal_year"] = fiscal_year

            response = await client.get(f"agency/{toptier_code}/", params=params)
            return json.dumps(response, indent=2)

        except Exception as e:
            return f"Error getting agency overview: {str(e)}"

    @mcp.tool()
    async def get_agency_awards(
        toptier_code: str,
        fiscal_year: Optional[int] = None,
        award_type_codes: Optional[str] = None,
        award_amounts: Optional[str] = None,
        recipient_search_text: Optional[str] = None,
        recipient_type_names: Optional[str] = None,
        recipient_locations: Optional[str] = None,
        place_of_performance_locations: Optional[str] = None,
        agencies: Optional[str] = None,
        federal_accounts: Optional[str] = None,
        object_class: Optional[str] = None,
        program_activities: Optional[str] = None,
        naics_codes: Optional[str] = None,
        psc_codes: Optional[str] = None,
        contract_pricing_type_codes: Optional[str] = None,
        set_aside_type_codes: Optional[str] = None,
        extent_competed_type_codes: Optional[str] = None,
        page: int = 1,
        limit: int = 100,
        sort: str = "Award Amount",
        order: str = "desc",
    ) -> str:
        """
        Get agency awards data with comprehensive filtering options.

        Args:
            toptier_code: The agency's top-tier code (e.g., '097' for DOD)
            fiscal_year: Optional fiscal year to filter data
            award_type_codes: Award type codes to filter by (e.g., 'A,B,C,D' for contracts)
            award_amounts: Award amount range (e.g., '1000000,10000000' for $1M-$10M)
            recipient_search_text: Text to search in recipient names
            recipient_type_names: Recipient type names to filter by
            recipient_locations: Recipient location codes to filter by
            place_of_performance_locations: Place of performance location codes
            agencies: Sub-agency names to filter by
            federal_accounts: Federal account codes to filter by
            object_class: Object class codes to filter by
            program_activities: Program activity codes to filter by
            naics_codes: NAICS industry codes to filter by
            psc_codes: Product/Service codes to filter by
            contract_pricing_type_codes: Contract pricing type codes
            set_aside_type_codes: Set aside type codes
            extent_competed_type_codes: Extent competed type codes
            page: Page number for pagination (default: 1)
            limit: Number of results per page (default: 100, max: 500)
            sort: Sort field (default: 'Award Amount')
            order: Sort order - 'asc' or 'desc' (default: 'desc')

        Returns:
            Raw API response data as JSON string containing agency awards
        """
        try:
            payload = {
                "page": page,
                "limit": limit,
                "sort": sort,
                "order": order,
                "filters": {},
            }

            if fiscal_year is not None:
                payload["filters"]["fy"] = str(fiscal_year)

            if award_type_codes:
                payload["filters"]["award_type_codes"] = award_type_codes.split(",")

            if award_amounts:
                amounts = award_amounts.split(",")
                if len(amounts) == 2:
                    payload["filters"]["award_amounts"] = {
                        "lower_bound": float(amounts[0]),
                        "upper_bound": float(amounts[1]),
                    }

            if recipient_search_text:
                payload["filters"]["recipient_search_text"] = [recipient_search_text]

            if recipient_type_names:
                payload["filters"]["recipient_type_names"] = recipient_type_names.split(
                    ","
                )

            if recipient_locations:
                payload["filters"]["recipient_locations"] = [
                    {"country": "USA", "state": code.strip()}
                    for code in recipient_locations.split(",")
                ]

            if place_of_performance_locations:
                payload["filters"]["place_of_performance_locations"] = [
                    {"country": "USA", "state": code.strip()}
                    for code in place_of_performance_locations.split(",")
                ]

            if agencies:
                payload["filters"]["agencies"] = [
                    {"name": name.strip()} for name in agencies.split(",")
                ]

            if federal_accounts:
                payload["filters"]["federal_accounts"] = federal_accounts.split(",")

            if object_class:
                payload["filters"]["object_class"] = object_class.split(",")

            if program_activities:
                payload["filters"]["program_activities"] = program_activities.split(",")

            if naics_codes:
                payload["filters"]["naics_codes"] = naics_codes.split(",")

            if psc_codes:
                payload["filters"]["psc_codes"] = psc_codes.split(",")

            if contract_pricing_type_codes:
                payload["filters"]["contract_pricing_type_codes"] = (
                    contract_pricing_type_codes.split(",")
                )

            if set_aside_type_codes:
                payload["filters"]["set_aside_type_codes"] = set_aside_type_codes.split(
                    ","
                )

            if extent_competed_type_codes:
                payload["filters"]["extent_competed_type_codes"] = (
                    extent_competed_type_codes.split(",")
                )

            response = await client.get(f"agency/{toptier_code}/awards/", payload)
            return json.dumps(response, indent=2)

        except Exception as e:
            return f"Error getting agency awards: {str(e)}"
