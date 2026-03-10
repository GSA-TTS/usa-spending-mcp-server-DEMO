from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from usa_spending_mcp_server.client import USASpendingClient
from usa_spending_mcp_server.models.common_models import AgencyListParams


def register_agency_tools(mcp: FastMCP, client: USASpendingClient):
    """Register agency spending tools"""

    @mcp.tool()
    async def get_sub_agency_list(
        toptier_code: Annotated[str, Field(description="The toptier code of the agency")],
        agency_list_params: Annotated[
            AgencyListParams, Field(description="Agency list parameters")
        ],
    ) -> Any:
        """
        Given a toptier_code of an agency, this tool returns the list of subagencies and offices
        based on provided toptier_code,
        fiscal year, and award type. This can be by either funding agency or awarding agency.

        Args:
            toptier_code: The toptier_code of funding or awarding agency
            fiscal_year: The fiscal year (YYYY) defaults to current fiscal year
            sort: The sort order. One of name,total_obligations
                  (default),transaction_amount,new_award_count
            page: Page number to return (Default 1)
            limit: Number of results (Default 100)
        Returns:
            Raw API response data as JSON string containing list of subagencies and offices
        """
        try:
            response = await client.get(
                f"agency/{toptier_code}/sub_agency/",
                params=agency_list_params.model_dump(exclude_none=True),
            )
            return response

        except Exception as e:
            return f"Error getting sub-agency list: {str(e)}"

    @mcp.tool()
    async def get_sub_components_list(
        toptier_code: Annotated[str, Field(description="The toptier code of the agency")],
        agency_list_params: Annotated[
            AgencyListParams, Field(description="Agency list parameters")
        ],
    ) -> Any:
        """
        Get list of all sub-components for a given agency based on toptier_code.
        This returns all the sub-components/bureaus/offices under the specified agency.

        Args:
            toptier_code: The toptier_code of the agency (e.g., '012' for USDA)
            fiscal_year: The fiscal year (YYYY) defaults to current fiscal year
            sort: The sort order. One of name,total_obligations
                  (default),transaction_amount,new_award_count
            page: Page number to return (Default 1)
            limit: Number of results (Default 100)

        Returns:
            Raw API response data as JSON string containing list of sub-components
        """
        try:
            response = await client.get(
                f"agency/{toptier_code}/sub_components/",
                params=agency_list_params.model_dump(exclude_none=True),
            )
            return response

        except Exception as e:
            return f"Error getting sub-components list: {str(e)}"

    @mcp.tool()
    async def get_sub_component_details(
        toptier_code: Annotated[str, Field(description="The toptier code of the agency")],
        bureau_slug: Annotated[str, Field(description="The slug of the sub-component")],
        agency_list_params: Annotated[
            AgencyListParams, Field(description="Agency list parameters")
        ],
    ) -> Any:
        """
        Get detailed information about a specific sub-component within an agency.
        This provides detailed spending and budget information for a specific bureau/office.

        Args:
            toptier_code: The toptier_code of the agency (e.g., '012' for USDA)
            bureau_slug: The slug of the sub-component (e.g., 'farm-service-agency')
            fiscal_year: The fiscal year (YYYY) defaults to current fiscal year
            sort: The sort order.
                One of name,total_obligations (default),transaction_amount,new_award_count
            page: Page number to return (Default 1)
            limit: Number of results (Default 100)

        Returns:
            Raw API response data as JSON string containing detailed sub-component information
        """
        try:
            response = await client.get(
                f"agency/{toptier_code}/sub_components/{bureau_slug}/",
                params=agency_list_params.model_dump(exclude_none=True),
            )
            return response

        except Exception as e:
            return f"Error getting sub-component details: {str(e)}"

    @mcp.tool()
    async def get_agency_budgetary_resources(
        toptier_code: Annotated[str, Field(description="The toptier code of the agency")],
    ) -> Any:
        """
        Get budgetary resources, obligations, and outlays for an agency across fiscal years.

        Returns multi-year data showing:
        - Budget authority (total resources available)
        - Total obligations (commitments to spend)
        - Total outlays (actual money paid out)

        Use this to compare obligations vs actual spending (outlays) and identify
        discrepancies. Also useful for tracking budget trends over time.

        Args:
            toptier_code: The toptier_code of the agency (e.g., '097' for DOD,
                '075' for HHS). Use get_agencies() to find codes.

        Returns:
            Dict with agency_data_by_year: array of fiscal year entries, each with:
            - fiscal_year
            - agency_budgetary_resources
            - agency_total_obligated
            - agency_total_outlays
            - total_budgetary_resources (government-wide)

        Examples:
            get_agency_budgetary_resources(toptier_code="097")  # DOD
            get_agency_budgetary_resources(toptier_code="075")  # HHS
        """
        try:
            response = await client.get(f"agency/{toptier_code}/budgetary_resources/")
            return response
        except Exception as e:
            return f"Error getting budgetary resources: {str(e)}"

    @mcp.tool()
    async def get_agency_obligations_by_award_category(
        toptier_code: Annotated[str, Field(description="The toptier code of the agency")],
        fiscal_year: Annotated[
            int | None,
            Field(description="Fiscal year (e.g., 2023). Defaults to current FY."),
        ] = None,
    ) -> Any:
        """
        Get agency obligations broken down by award category (contracts, grants, loans, etc.).

        Returns how an agency's obligations are split across award types within a single
        fiscal year. Essential for answering "how much did agency X spend on contracts
        vs grants?"

        **Important**: "contracts" and "idvs" (Indefinite Delivery Vehicles) are reported
        as separate categories. IDVs are umbrella contracts under which individual task
        orders are issued. For total contract spending, you may need to sum both
        "contracts" and "idvs" amounts. The IDV amount may appear as $0 if all spending
        is attributed to the individual task orders (contracts) underneath.

        Args:
            toptier_code: The toptier_code of the agency (e.g., '097' for DOD)
            fiscal_year: The fiscal year (optional, defaults to current FY)

        Returns:
            Dict with:
            - total_aggregated_amount: Total obligations across all award types
            - results: Breakdown by category (contracts, direct_payments, grants,
              idvs, loans, other)

        Examples:
            # DOD FY2023 breakdown
            get_agency_obligations_by_award_category(toptier_code="097", fiscal_year=2023)
        """
        try:
            params = {}
            if fiscal_year:
                params["fiscal_year"] = fiscal_year
            response = await client.get(
                f"agency/{toptier_code}/obligations_by_award_category/",
                params=params or None,
            )
            return response
        except Exception as e:
            return f"Error getting obligations by award category: {str(e)}"
