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
        type: str,
        fiscal_year: str,
        quarter: str | None = None,
        period: str | None = None,
        agency: str | None = None,
        federal_account: str | None = None,
        object_class: str | None = None,
        budget_function: str | None = None,
        budget_subfunction: str | None = None,
        recipient: str | None = None,
        program_activity: str | None = None,
    ) -> Any:
        """
        Search USA government spending data using the Spending Explorer endpoint.

        This endpoint powers USAspending.gov's Spending Explorer and allows drilling down
        into specific subsets of data by level of detail.

        Args:
            type: REQUIRED - The type of data to group by:
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

            fiscal_year: REQUIRED - Fiscal year (e.g., "2020")
            quarter: Quarter to limit data to (1, 2, 3, 4). For general explorer, this is required.
                    Data includes all quarters up to and including the specified quarter.
            period: Period to limit data to (1-12). Optional alternative to quarter.
            agency: Agency ID to filter by (from previous general explorer response)
            federal_account: Federal Account ID to filter by (from previous explorer response)
            object_class: Object Class ID to filter by
            budget_function: Budget Function ID to filter by
            budget_subfunction: Budget Subfunction ID to filter by
            recipient: Recipient ID to filter by
            program_activity: Program Activity ID to filter by

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
        """

        try:
            request = SpendingExplorerRequest.from_params(
                type=type,
                fiscal_year=fiscal_year,
                quarter=quarter,
                period=period,
                agency=agency,
                federal_account=federal_account,
                object_class=object_class,
                budget_function=budget_function,
                budget_subfunction=budget_subfunction,
                recipient=recipient,
                program_activity=program_activity,
            )

            # Make API call
            response = await client.post("spending/", request.to_api_payload())

            # Return raw API response
            return response

        except Exception as e:
            return f"Error searching spending explorer: {str(e)}"
