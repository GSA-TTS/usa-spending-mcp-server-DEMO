from typing import Any

from fastmcp import FastMCP

from usa_spending_mcp_server.client import USASpendingClient


def register_program_activity_tools(mcp: FastMCP, client: USASpendingClient):
    """Register program activity tools"""

    @mcp.tool()
    async def list_program_activities(
        toptier_code: str,
        fiscal_year: str | None = None,
        filter: str | None = None,
        order: str | None = "desc",
        sort: str | None = "obligated_amount",
        page: str | None = "1",
        limit: str | None = "100",
    ) -> Any:
        """
        List program activities for a specific agency and fiscal year.

        Use this to retrieve details about how an agency's funds were allocated
        by program activity. Example, you can look at agency IT spending

        Args:
            toptier_code: The toptier code of the agency (e.g., "086")
            fiscal_year: The fiscal year to query (optional; defaults to current FY)
            filter: Filter program activities by name (e.g. IT Spending) (optional)
            order: Sort direction: "asc" or "desc" (optional; default: "desc")
            sort: Field to sort by: "name", "obligated_amount", or "gross_outlay_amount"
                  (optional; default: "obligated_amount")
            page: Page number (optional; default: 1)
            limit: Number of results per page (optional; default: 10)

        Returns:
            JSON string of the response including totals and program activity list
        """
        try:
            endpoint = f"agency/{toptier_code}/program_activity/"
            params = {
                "fiscal_year": fiscal_year,
                "filter": filter,
                "order": order,
                "sort": sort,
                "page": page,
                "limit": limit,
            }

            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}

            response = await client.get(endpoint, params=params)
            return response

        except Exception as e:
            return f"Error fetching program activities: {str(e)}"
