import json
import logging
from datetime import date
from typing import Any, Optional

from fastmcp import FastMCP

from usa_spending_mcp_server.client import USASpendingClient

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def register_award_spending_tools(mcp: FastMCP, client: USASpendingClient):
    """Register award spending tools"""

    @mcp.tool()
    async def search_award_spending_by_agency(
        fiscal_year: int,
        awarding_agency_id: Optional[int] = None,
        funding_agency_id: Optional[int] = None,
        award_type_codes: Optional[str] = None,
        page: int = 1,
        limit: int = 100,
        sort: str = "award_amount",
        order: str = "desc",
    ) -> str:
        """
        Search USA government award spending data by agency.

        Args:
            fiscal_year: Fiscal year to search (required)
            awarding_agency_id: ID of the awarding agency (e.g., 183 for DOD)
            funding_agency_id: ID of the funding agency
            award_type_codes: Award type codes to filter by (e.g., 'A,B,C,D' for contracts)
            page: Page number for pagination (default: 1)
            limit: Number of results per page (default: 100, max: 500)
            sort: Sort field (default: 'award_amount')
            order: Sort order - 'asc' or 'desc' (default: 'desc')

        Returns:
            Raw API response data as JSON string
        """

        try:
            # Build the request URL with query parameters
            params = {
                "fiscal_year": fiscal_year,
                "page": page,
                "limit": limit,
                "sort": sort,
                "order": order,
            }

            if awarding_agency_id is not None:
                params["awarding_agency_id"] = awarding_agency_id

            if funding_agency_id is not None:
                params["funding_agency_id"] = funding_agency_id

            if award_type_codes:
                params["award_type_codes"] = award_type_codes

            # Make API call using GET method for this endpoint
            response = await client.get("award_spending/agency/", params=params)

            # Return raw API response
            return json.dumps(response, indent=2)

        except Exception as e:
            return f"Error searching award spending by agency: {str(e)}"

    @mcp.tool()
    async def search_award_spending_by_recipient(
        fiscal_year: int,
        awarding_agency_id: Optional[int] = None,
        funding_agency_id: Optional[int] = None,
        recipient_id: Optional[str] = None,
        award_type_codes: Optional[str] = None,
        page: int = 1,
        limit: int = 100,
        sort: str = "award_amount",
        order: str = "desc",
    ) -> str:
        """
        Search USA government award spending data by recipient.

        Args:
            fiscal_year: Fiscal year to search (required)
            awarding_agency_id: ID of the awarding agency (e.g., 183 for DOD)
            funding_agency_id: ID of the funding agency
            recipient_id: Recipient ID to filter by
            award_type_codes: Award type codes to filter by (e.g., 'A,B,C,D' for contracts)
            page: Page number for pagination (default: 1)
            limit: Number of results per page (default: 100, max: 500)
            sort: Sort field (default: 'award_amount')
            order: Sort order - 'asc' or 'desc' (default: 'desc')

        Returns:
            Raw API response data as JSON string
        """

        try:
            # Build the request URL with query parameters
            params = {
                "fiscal_year": fiscal_year,
                "page": page,
                "limit": limit,
                "sort": sort,
                "order": order,
            }

            if awarding_agency_id is not None:
                params["awarding_agency_id"] = awarding_agency_id

            if funding_agency_id is not None:
                params["funding_agency_id"] = funding_agency_id

            if recipient_id:
                params["recipient_id"] = recipient_id

            if award_type_codes:
                params["award_type_codes"] = award_type_codes

            # Make API call using GET method for this endpoint
            response = await client.get("award_spending/recipient/", params=params)

            # Return raw API response
            return json.dumps(response, indent=2)

        except Exception as e:
            return f"Error searching award spending by recipient: {str(e)}"

    @mcp.tool()
    async def search_spending_by_award(
        fiscal_year: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        keywords: Optional[str] = None,
        awarding_agency_name: Optional[str] = None,
        funding_agency_name: Optional[str] = None,
        recipient_state_code: Optional[str] = None,
        recipient_search_text: Optional[str] = None,
        award_type_codes: Optional[str] = None,
        award_ids: Optional[str] = None,
        naics_codes: Optional[str] = None,
        psc_codes: Optional[str] = None,
        fields: Optional[str] = None,
        page: int = 1,
        limit: int = 100,
        sort: Optional[str] = None,
        order: str = "desc",
    ) -> str:
        """
        Search USA government spending data by award with advanced filtering.

        Args:
            fiscal_year: Fiscal year to search (e.g., 2023)
            start_date: Start date in YYYY-MM-DD format (alternative to fiscal_year)
            end_date: End date in YYYY-MM-DD format (alternative to fiscal_year)
            keywords: Comma-separated keywords to search for (e.g., "broadband,internet")
            awarding_agency_name: Name of awarding agency (e.g., "Department of Commerce")
            funding_agency_name: Name of funding agency
            recipient_state_code: State code for recipient location (e.g., "GA")
            recipient_search_text: Comma-separated text to search in recipient names
            award_type_codes: Comma-separated award type codes (e.g., "A,B,C,D" for contracts)
            award_ids: Comma-separated specific award IDs to search for
            naics_codes: Comma-separated NAICS industry codes to filter by
            psc_codes: Comma-separated Product/Service codes to filter by
            fields: Comma-separated fields to return (defaults to common fields if not specified)
            page: Page number for pagination (default: 1)
            limit: Number of results per page (default: 100, max: 500)
            sort: Sort field (optional)
            order: Sort order - 'asc' or 'desc' (default: 'desc')

        Returns:
            Raw API response data as JSON string
        """

        try:
            # Build the filters object
            filters = {}

            # Time period handling
            if fiscal_year:
                filters["time_period"] = [
                    {
                        "start_date": f"{fiscal_year-1}-10-01",
                        "end_date": f"{fiscal_year}-09-30",
                    }
                ]
            elif start_date and end_date:
                filters["time_period"] = [
                    {"start_date": start_date, "end_date": end_date}
                ]

            # Add other filters with comma-separated string handling
            if keywords:
                filters["keywords"] = [kw.strip() for kw in keywords.split(",")]

            if awarding_agency_name or funding_agency_name:
                agencies = []
                if awarding_agency_name:
                    agencies.append(
                        {
                            "type": "awarding",
                            "tier": "toptier",
                            "name": awarding_agency_name,
                        }
                    )
                if funding_agency_name:
                    agencies.append(
                        {
                            "type": "funding",
                            "tier": "toptier",
                            "name": funding_agency_name,
                        }
                    )
                filters["agencies"] = agencies

            if recipient_state_code:
                filters["recipient_locations"] = [
                    {"state_code": [recipient_state_code]}
                ]

            if recipient_search_text:
                filters["recipient_search_text"] = [
                    text.strip() for text in recipient_search_text.split(",")
                ]

            if award_type_codes:
                filters["award_type_codes"] = [
                    code.strip() for code in award_type_codes.split(",")
                ]

            if award_ids:
                filters["award_ids"] = [aid.strip() for aid in award_ids.split(",")]

            if naics_codes:
                filters["naics_codes"] = {
                    "require": [code.strip() for code in naics_codes.split(",")]
                }

            if psc_codes:
                filters["psc_codes"] = {
                    "require": [code.strip() for code in psc_codes.split(",")]
                }

            # Handle fields - either comma-separated string or use defaults
            if fields:
                field_list = [field.strip() for field in fields.split(",")]
            else:
                field_list = [
                    "Award ID",
                    "Recipient Name",
                    "Award Amount",
                    "Description",
                    "Awarding Agency",
                    "Start Date",
                    "End Date",
                    "Award Type",
                ]

            # Build the request payload
            payload = {
                "filters": filters,
                "fields": field_list,
                "page": page,
                "limit": limit,
                "order": order,
            }

            if sort:
                payload["sort"] = sort

            # Make API call using POST method
            response = await client.post("search/spending_by_award/", data=payload)

            # Return raw API response
            return json.dumps(response, indent=2)

        except Exception as e:
            return f"Error searching spending by award: {str(e)}"
