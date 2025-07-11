from typing import Any

from fastmcp import FastMCP

from usa_spending_mcp_server.client import USASpendingClient
from usa_spending_mcp_server.models.recipient_models import RecipientSearchRequest


def register_recipient_search_tools(mcp: FastMCP, client: USASpendingClient):
    """Register recipient search tool"""

    @mcp.tool()
    async def search_recipients(
        recipient_search_request: RecipientSearchRequest,
    ) -> Any:
        """
        Search for government spending recipients (contractors, grantees, etc) in the
        last 12 months.

        This endpoint returns a list of recipients with their spending amounts,
        DUNS numbers, UEI identifiers, and recipient levels.

        Args:
            recipient_search_request: RecipientSearchRequest object containing:
                - keyword: Optional search term to filter by recipient name, UEI, or DUNS
                - award_type: Filter by award type (default: 'all')
                    - 'all': All award types
                    - 'contracts': Only contracts
                    - 'grants': Only grants
                    - 'loans': Only loans
                    - 'direct_payments': Only direct payments
                    - 'other_financial_assistance': Other financial assistance
                - sort: Field to sort results by (default: 'amount')
                    - 'amount': Sort by total spending amount
                    - 'name': Sort alphabetically by recipient name
                    - 'duns': Sort by DUNS number
                - order: Sort direction (default: 'desc')
                    - 'desc': Descending order
                    - 'asc': Ascending order
                - pagination: BasePagination object with page, limit, order
                    - page: Page number for pagination (default: 1)
                    - limit: Number of results per page (default: 100, max: 100)
                - subawards: Include subawards in the search (default: False)

        Returns:
            Raw API response data as JSON string containing:
            - results: Array of recipients with id, name, duns, uei, recipient_level, amount
            - page_metadata: Pagination information

        Examples:
            - Find top contractors:
                search_recipients(RecipientSearchRequest(award_type='contracts',
                    pagination=BasePagination(limit=10)))
            - Search by name:
                search_recipients(RecipientSearchRequest(keyword='Boeing'))
            - Find all grant recipients:
                search_recipients(RecipientSearchRequest(award_type='grants', sort='name'))
        """

        try:
            # Make API call
            response = await client.post(
                "recipient/", recipient_search_request.model_dump(exclude_none=True)
            )

            # Return raw API response
            return response

        except Exception as e:
            return f"Error searching recipients: {str(e)}"
