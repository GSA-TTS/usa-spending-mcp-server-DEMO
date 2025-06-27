import json
import logging
from typing import List, Optional

from fastmcp import FastMCP

from usa_spending_mcp_server.client import USASpendingClient

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def register_award_search_tools(mcp: FastMCP, client: USASpendingClient):
    """Register spending by award search tool"""

    @mcp.tool()
    async def search_spending_by_award(
        award_type_codes: str,
        start_date: str = "2023-10-01",
        end_date: str = "2024-09-30",
        agencies: Optional[str] = None,
        recipients: Optional[str] = None,
        award_ids: Optional[str] = None,
        fields: Optional[str] = None,
        subawards: bool = False,
        page: int = 1,
        limit: int = 10,
        sort: Optional[str] = None,
        order: str = "desc",
    ) -> str:
        """
        Search USA government spending data by award with filtering capabilities.

        Args:
            award_type_codes: REQUIRED - Award type codes to filter by (e.g., 'A,B,C' for contracts, 'D' for grants)
                - A: BPA Call
                - B: Purchase Order
                - C: Delivery Order
                - D: Definitive Contract
                - 02-05: Grants
                - 06,10: Direct Payments
                - 07,08: Loans
                - 09,11,-1: Other
                - IDV: Indefinite Delivery Vehicle
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            agencies: Agency names to filter by (format: "type:tier:name" or just "name" for default awarding:toptier)
            recipients: Recipient names to search for (comma-separated)
            award_ids: Award IDs to search for (comma-separated)
            fields: Fields to return in response (comma-separated). Common fields:
                - Award ID, Recipient Name, Start Date, End Date, Award Amount
                - Awarding Agency, Awarding Sub Agency, Award Type
                - Funding Agency, Funding Sub Agency
            subawards: Include subaward data (default: False)
            page: Page number for pagination (default: 1)
            limit: Number of results per page (default: 10, max: 500)
            sort: Field to sort by (any field from the response)
            order: Sort order - 'asc' or 'desc' (default: 'desc')

        Returns:
            Raw API response data as JSON string
        """

        try:
            # Build the request payload
            payload = {
                "subawards": subawards,
                "page": page,
                "limit": limit,
                "order": order,
                "filters": {
                    "time_period": [{"start_date": start_date, "end_date": end_date}],
                    "award_type_codes": [
                        code.strip() for code in award_type_codes.split(",")
                    ],
                },
            }

            # Set default fields if none provided
            if fields:
                payload["fields"] = [field.strip() for field in fields.split(",")]
            else:
                payload["fields"] = [
                    "Award ID",
                    "Recipient Name",
                    "Start Date",
                    "End Date",
                    "Award Amount",
                    "Awarding Agency",
                    "Awarding Sub Agency",
                    "Award Type",
                ]

            # Add sort field if provided
            if sort:
                payload["sort"] = sort

            # Handle agencies filter
            if agencies:
                agency_objects = []
                for agency_str in agencies.split(","):
                    agency_str = agency_str.strip()

                    # Parse agency string format: "type:tier:name" or just "name"
                    if ":" in agency_str:
                        parts = agency_str.split(":")
                        if len(parts) >= 3:
                            agency_type, tier, name = (
                                parts[0],
                                parts[1],
                                ":".join(parts[2:]),
                            )
                        else:
                            # Default values if not fully specified
                            agency_type, tier, name = "awarding", "toptier", agency_str
                    else:
                        # Default values for simple name
                        agency_type, tier, name = "awarding", "toptier", agency_str

                    agency_obj = {"type": agency_type, "tier": tier, "name": name}

                    # Add toptier_name if tier is subtier and it's provided
                    if (
                        tier == "subtier"
                        and ":" in agency_str
                        and len(agency_str.split(":")) >= 4
                    ):
                        agency_obj["toptier_name"] = agency_str.split(":")[3]

                    agency_objects.append(agency_obj)

                payload["filters"]["agencies"] = agency_objects

            # Handle recipients filter
            if recipients:
                payload["filters"]["recipient_search_text"] = [
                    recipient.strip() for recipient in recipients.split(",")
                ]

            # Handle award IDs filter
            if award_ids:
                payload["filters"]["award_ids"] = [
                    award_id.strip() for award_id in award_ids.split(",")
                ]

            # Make API call
            response = await client.post("search/spending_by_award/", payload)

            # Return raw API response
            return json.dumps(response, indent=2)

        except Exception as e:
            return f"Error searching spending by award: {str(e)}"
