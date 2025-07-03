import json
from typing import Optional

from fastmcp import FastMCP

from usa_spending_mcp_server.client import USASpendingClient
from usa_spending_mcp_server.models.common_models import AgencyListParams


def register_agency_tools(mcp: FastMCP, client: USASpendingClient):
    """Register agency spending tools"""

    @mcp.tool()
    async def get_agency_overview(
        agency_id: str,
    ) -> str:
        """
        Get agency overview information. This is useful to get information about the active financial year/quarter.
        It will also display information about outlay amount, obligated amount, budget authority amount,
        and current total budget authority amount.

        Args:
            agency_id: The agency_id (not that this is different than the top tier code)

        Returns:
            Raw API response data as JSON string containing agency overview
        """
        try:
            response = await client.get(f"references/agency/{agency_id}/")
            return json.dumps(response, indent=2)

        except Exception as e:
            return f"Error getting agency overview: {str(e)}"

    @mcp.tool()
    async def get_sub_agency_list(
        toptier_code: str,
        fiscal_year: Optional[str] = None,
        sort: Optional[str] = None,
        page: Optional[str] = "1",
        limit: Optional[str] = "100",
    ) -> str:
        """
        Given a toptier_code of an agency, this tool returns the list of subagencies and offices based on provided toptier_code,
        fiscal year, and award type. This can be by either funding agency or awarding agency.

        Args:
            toptier_code: The toptier_code of funding or awarding agency
            fiscal_year: The fiscal year (YYYY) defaults to current fiscal year
            sort: The sort order. One of name,total_obligations (default),transaction_amount,new_award_count
            page: Page number to return (Default 1)
            limit: Number of results (Default 100)
        Returns:
            Raw API response data as JSON string containing list of subagencies and offices
        """
        try:
            agency_list_params = AgencyListParams(
                fiscal_year=fiscal_year, sort=sort, page=page, limit=limit
            ).to_params_dict()

            response = await client.get(
                f"agency/{toptier_code}/sub_agency/", params=agency_list_params
            )
            return json.dumps(response, indent=2)

        except Exception as e:
            return f"Error getting sub-agency list: {str(e)}"

    @mcp.tool()
    async def get_sub_components_list(
        toptier_code: str,
        fiscal_year: Optional[str] = None,
        sort: Optional[str] = None,
        page: Optional[str] = "1",
        limit: Optional[str] = "100",
    ) -> str:
        """
        Get list of all sub-components for a given agency based on toptier_code.
        This returns all the sub-components/bureaus/offices under the specified agency.

        Args:
            toptier_code: The toptier_code of the agency (e.g., '012' for USDA)
            fiscal_year: The fiscal year (YYYY) defaults to current fiscal year
            sort: The sort order. One of name,total_obligations (default),transaction_amount,new_award_count
            page: Page number to return (Default 1)
            limit: Number of results (Default 100)

        Returns:
            Raw API response data as JSON string containing list of sub-components
        """
        try:
            agency_list_params = AgencyListParams(
                fiscal_year=fiscal_year, sort=sort, page=page, limit=limit
            ).to_params_dict()

            response = await client.get(
                f"agency/{toptier_code}/sub_components/", params=agency_list_params
            )
            return json.dumps(response, indent=2)

        except Exception as e:
            return f"Error getting sub-components list: {str(e)}"

    @mcp.tool()
    async def get_sub_component_details(
        toptier_code: str,
        bureau_slug: str,
        fiscal_year: Optional[str] = None,
        sort: Optional[str] = None,
        page: Optional[str] = "1",
        limit: Optional[str] = "100",
    ) -> str:
        """
        Get detailed information about a specific sub-component within an agency.
        This provides detailed spending and budget information for a specific bureau/office.

        Args:
            toptier_code: The toptier_code of the agency (e.g., '012' for USDA)
            bureau_slug: The slug of the sub-component (e.g., 'farm-service-agency')
            fiscal_year: The fiscal year (YYYY) defaults to current fiscal year
            sort: The sort order. One of name,total_obligations (default),transaction_amount,new_award_count
            page: Page number to return (Default 1)
            limit: Number of results (Default 100)

        Returns:
            Raw API response data as JSON string containing detailed sub-component information
        """
        try:
            agency_list_params = AgencyListParams(
                fiscal_year=fiscal_year, sort=sort, page=page, limit=limit
            ).to_params_dict()

            response = await client.get(
                f"agency/{toptier_code}/sub_components/{bureau_slug}/",
                params=agency_list_params,
            )
            return json.dumps(response, indent=2)

        except Exception as e:
            return f"Error getting sub-component details: {str(e)}"
