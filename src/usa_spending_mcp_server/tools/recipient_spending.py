import json
from typing import Optional

from fastmcp import FastMCP

from usa_spending_mcp_server.client import USASpendingClient
from usa_spending_mcp_server.models.recipient_models import RecipientSearchRequest


def register_recipient_search_tools(mcp: FastMCP, client: USASpendingClient):
    """Register recipient search tool"""

    @mcp.tool()
    async def search_recipients(
        keyword: Optional[str] = None,
        award_type: str = "all",
        sort: str = "amount",
        order: str = "desc",
        page: str = "1",
        limit: str = "50",
    ) -> str:
        """
        Search for government spending recipients (contractors, grantees, etc).

        This endpoint returns a list of recipients with their spending amounts,
        DUNS numbers, UEI identifiers, and recipient levels.

        Args:
            keyword: Optional search term to filter by recipient name, UEI, or DUNS
            award_type: Filter by award type (default: 'all')
                - 'all': All award types
                - 'contracts': Only contracts
                - 'grants': Only grants
                - 'loans': Only loans
                - 'direct_payments': Only direct payments
                - 'other_financial_assistance': Other financial assistance
            sort: Field to sort results by (default: 'amount')
                - 'amount': Sort by total spending amount
                - 'name': Sort alphabetically by recipient name
                - 'duns': Sort by DUNS number
            order: Sort direction (default: 'desc')
                - 'desc': Descending order
                - 'asc': Ascending order
            page: Page number for pagination (default: 1)
            limit: Number of results per page (default: 50, max: 1000)

        Returns:
            Raw API response data as JSON string containing:
            - results: Array of recipients with id, name, duns, uei, recipient_level, amount
            - page_metadata: Pagination information

        Examples:
            - Find top contractors: search_recipients(award_type='contracts', limit='10')
            - Search by name: search_recipients(keyword='Boeing')
            - Find all grant recipients: search_recipients(award_type='grants', sort='name')
        """

        try:
            request = RecipientSearchRequest.from_params(
                keyword=keyword,
                award_type=award_type,
                sort=sort,
                order=order,
                page=page,
                limit=limit,
            )
            # Make API call
            response = await client.post("recipient/", request.to_api_payload())

            # Return raw API response
            return json.dumps(response, indent=2)

        except Exception as e:
            return f"Error searching recipients: {str(e)}"
