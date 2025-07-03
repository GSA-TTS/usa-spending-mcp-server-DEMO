import json
from typing import Optional

from fastmcp import FastMCP

from usa_spending_mcp_server.client import USASpendingClient
from usa_spending_mcp_server.models.award_spending_models import AwardSearchRequest


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
        subawards: str = "False",
        page: str = "1",
        limit: str = "10",
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
            request = AwardSearchRequest.from_params(
                award_type_codes=award_type_codes,
                start_date=start_date,
                end_date=end_date,
                agencies=agencies,
                recipients=recipients,
                award_ids=award_ids,
                fields=fields,
                subawards=subawards,
                page=page,
                limit=limit,
                sort=sort,
                order=order,
            )
            # Make API call
            response = await client.post(
                "search/spending_by_award/", request.to_api_payload()
            )

            # Return raw API response
            return json.dumps(response, indent=2)

        except Exception as e:
            return f"Error searching spending by award: {str(e)}"
