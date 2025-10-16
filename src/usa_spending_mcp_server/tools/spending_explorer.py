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
        Use for agency spending totals, budget functions, object classes.
            - 'What is the total spending for HHS OIG in FY2023?'
            - 'Which agency spent the most on contracts in FY2023?'
            - 'How much did DOD spend on personnel vs contracts?'
            - 'What are the top spending categories for HHS?'"

        WORKFLOW FOR DRILLING DOWN:
        1. Start with a GENERAL search using one of the top-level types (agency, budget_function, or object_class)
        2. Use the 'id' from results to drill down with DETAILED searches using other types
        3. Combine multiple filters to narrow scope (e.g., specific agency + object_class for contract spending)

        Args:
            spending_explorer_request: SpendingExplorerRequest object containing:
                - type: REQUIRED - ExplorerType enum value for data grouping:

                    GENERAL Explorer (top-level entry points - use GeneralFilter):
                    - "budget_function": Budget Functions (e.g., National Defense, Education)
                    - "agency": Agencies (e.g., Department of Defense, Department of Education)
                    - "object_class": Object Classes (e.g., Personnel compensation, Contractual services)

                    DETAILED Explorer (drill-down types - use DetailedFilter with constraints):
                    - "federal_account": Federal Accounts within an agency/budget function
                    - "recipient": Recipients within a scope (contractors, grantees)
                    - "award": Individual awards within a scope
                    - "budget_subfunction": Budget Subfunctions within a budget function
                    - "program_activity": Program Activities within an agency

                - filters: Union[GeneralFilter, DetailedFilter] containing:

                    For GeneralFilter (top-level searches):
                    - fy: REQUIRED - Fiscal year (e.g., "2024")
                    - quarter: REQUIRED - Quarter enum ("1", "2", "3", "4")

                    For DetailedFilter (drill-down searches):
                    - fy: REQUIRED - Fiscal year (e.g., "2024")
                    - quarter: Optional - Quarter enum ("1", "2", "3", "4")
                    - period: Optional - Period enum ("1" through "12")
                    - agency: Optional - Agency ID from previous agency search
                    - federal_account: Optional - Federal Account ID from previous search
                    - object_class: Optional - Object Class ID (for contract spending analysis)
                    - budget_function: Optional - Budget Function ID from previous search
                    - budget_subfunction: Optional - Budget Subfunction ID from previous search
                    - recipient: Optional - Recipient ID from previous search
                    - program_activity: Optional - Program Activity ID from previous search

        Returns:
            Raw API response data as JSON string containing:
            - total: Total spending amount for the filtered scope
            - end_date: As-of date for the data
            - results: Array of spending records with amount, name, code, id, etc.
                - Use the 'id' field from results for subsequent drill-down queries

        CONTRACT SPENDING ANALYSIS EXAMPLE:
            1. First, get all agencies:
                SpendingExplorerRequest(
                    type=ExplorerType.AGENCY,
                    filters=GeneralFilter(fy="2024", quarter=Quarter.Q4)
                )

            2. Then, drill down to object classes for a specific agency to see contract spending:
                SpendingExplorerRequest(
                    type=ExplorerType.OBJECT_CLASS,
                    filters=DetailedFilter(fy="2024", agency="012", quarter=Quarter.Q4)
                )
                # Look for object classes like "25.1" (Advisory and assistance services)
                # or "25.2" (Other services) which typically represent contracts

            3. Further drill down to see recipients (contractors) within that scope:
                SpendingExplorerRequest(
                    type=ExplorerType.RECIPIENT,
                    filters=DetailedFilter(
                        fy="2024",
                        agency="012",
                        object_class="25.1",  # Contractual services
                        quarter=Quarter.Q4
                    )
                )

        IMPORTANT NOTES:
            - Data is not available prior to FY 2017 Q2
            - Data for latest complete quarter not available until 45 days after quarter close
            - For general explorer, you MUST specify one of: budget_function, agency, or object_class
            - For detailed explorer, combine multiple filter fields to narrow scope
            - Always use the 'id' field from API responses for subsequent drill-down queries
            - Object classes like "25.X" typically represent contractual services/spending

        MORE EXAMPLES:
            - Get HHS OIG Spending FY2023:
                SpendingExplorerRequest(
                    type=ExplorerType.FEDERAL_ACCOUNT,
                    filters=GeneralFilter(fy="2023", quarter=Quarter.Q4, agency="806")
                )

            - Get all agencies for FY2024 Q4:
                SpendingExplorerRequest(
                    type=ExplorerType.AGENCY,
                    filters=GeneralFilter(fy="2024", quarter=Quarter.Q4)
                )

            - Get Department of Defense spending by object class:
                SpendingExplorerRequest(
                    type=ExplorerType.OBJECT_CLASS,
                    filters=DetailedFilter(fy="2024", agency="097")  # Use ID from previous query
                )

            - Get top contractors for DOD contractual services:
                SpendingExplorerRequest(
                    type=ExplorerType.RECIPIENT,
                    filters=DetailedFilter(fy="2024", agency="097", object_class="25.1")
                )
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
