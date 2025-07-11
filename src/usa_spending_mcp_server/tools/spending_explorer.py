from typing import Any

from fastmcp import FastMCP

from usa_spending_mcp_server.client import USASpendingClient
from usa_spending_mcp_server.models.spending_explorer_models import (
    SpendingExplorerRequest,
)


def register_spending_explorer_tools(mcp: FastMCP, client: USASpendingClient):
    """Register spending explorer search tools"""

    @mcp.tool()
    async def search_spending_explorer(
        spending_explorer_request: SpendingExplorerRequest,
    ) -> Any:
        """
        Search USA government spending data using the Spending Explorer endpoint.

        This endpoint powers USAspending.gov's Spending Explorer and allows drilling down
        into specific subsets of data by level of detail.

        Args:
            spending_explorer_request: SpendingExplorerRequest object containing:
                - type: REQUIRED - ExplorerType enum value for data grouping:
                    General Explorer (top-level entry points):
                    - "budget_function": Budget Functions
                    - "agency": Agencies
                    - "object_class": Object Classes

                    Specific Explorer (drill-down types):
                    - "federal_account": Federal Accounts
                    - "recipient": Recipients
                    - "award": Awards
                    - "budget_subfunction": Budget Subfunctions
                    - "program_activity": Program Activities

                - filters: Union[GeneralFilter, DetailedFilter] containing:
                    For GeneralFilter:
                    - fy: REQUIRED - Fiscal year (e.g., "2020")
                    - quarter: REQUIRED - Quarter enum ("1", "2", "3", "4")

                    For DetailedFilter:
                    - fy: REQUIRED - Fiscal year (e.g., "2020")
                    - quarter: Optional - Quarter enum ("1", "2", "3", "4")
                    - period: Optional - Period enum ("1" through "12")
                    - agency: Optional - Agency ID to filter by
                    - federal_account: Optional - Federal Account ID to filter by
                    - object_class: Optional - Object Class ID to filter by
                    - budget_function: Optional - Budget Function ID to filter by
                    - budget_subfunction: Optional - Budget Subfunction ID to filter by
                    - recipient: Optional - Recipient ID to filter by
                    - program_activity: Optional - Program Activity ID to filter by

        Returns:
            Raw API response data as JSON string containing:
            - total: Total spending amount
            - end_date: As-of date for the data
            - results: Array of spending records with amount, name, code, etc.

        Notes:
            - Data is not available prior to FY 2017 Q2
            - Data for latest complete quarter not available until 45 days after quarter close
            - For general explorer, you must specify one of: budget_function, agency,
                or object_class
            - For specific explorer, you filter by combining multiple grouping fields

        Examples:
            - General agency search:
                search_spending_explorer(SpendingExplorerRequest(
                    type=ExplorerType.AGENCY,
                    filters=GeneralFilter(fy="2024", quarter=Quarter.Q4)
                ))
            - Detailed federal account search:
                search_spending_explorer(SpendingExplorerRequest(
                    type=ExplorerType.FEDERAL_ACCOUNT,
                    filters=DetailedFilter(fy="2024", agency="012", quarter=Quarter.Q2)
                ))
        """

        try:
            # Make API call
            response = await client.post(
                "spending/", spending_explorer_request.model_dump(exclude_none=True)
            )

            # Return raw API response
            return response

        except Exception as e:
            return f"Error searching spending explorer: {str(e)}"
