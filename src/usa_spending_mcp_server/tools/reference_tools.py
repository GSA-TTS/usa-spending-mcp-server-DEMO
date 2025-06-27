import json
import logging
from typing import Any, Dict, Optional

from fastmcp import FastMCP

from usa_spending_mcp_server.client import USASpendingClient

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def register_reference_tools(mcp: FastMCP, client: USASpendingClient):
    """Register reference/lookup tools"""

    @mcp.tool()
    async def get_agencies() -> str:
        """
        Get US agencies and their IDs and codes.

        Use this when you want to get a list of all the US agencies and their metadata
        including agency IDs needed for other API calls.

        Returns:
            Raw API response data as JSON string containing agency information
        """
        try:
            # Make API call
            response = await client.get("references/toptier_agencies/")

            # Return raw API response
            return json.dumps(response, indent=2)

        except Exception as e:
            return f"Error fetching agencies: {str(e)}"

    @mcp.tool()
    async def get_agency_by_id(agency_id: int) -> str:
        """
        Get specific US agency information by ID.

        Args:
            agency_id: The agency ID to look up

        Returns:
            Raw API response data as JSON string containing agency details
        """
        try:
            # Make API call
            response = await client.get(f"references/toptier_agencies/{agency_id}/")

            # Return raw API response
            return json.dumps(response, indent=2)

        except Exception as e:
            return f"Error fetching agency {agency_id}: {str(e)}"

    @mcp.tool()
    async def get_award_types() -> str:
        """
        Get all available award types and their codes.

        Use this to understand what award type codes (A, B, C, D, etc.) mean
        for filtering spending data.

        Returns:
            Raw API response data as JSON string containing award type information
        """
        try:
            # Make API call
            response = await client.get("references/filter/")

            # Return raw API response
            return json.dumps(response, indent=2)

        except Exception as e:
            return f"Error fetching award types: {str(e)}"

    @mcp.tool()
    async def get_naics_codes(naics_code: Optional[str] = None) -> str:
        """
        Get NAICS (North American Industry Classification System) codes.

        Args:
            naics_code: Optional specific NAICS code to look up. If not provided,
                       returns all top-level NAICS codes.

        Returns:
            Raw API response data as JSON string containing NAICS code information
        """
        try:
            endpoint = "references/naics/"
            if naics_code:
                endpoint += f"{naics_code}/"

            # Make API call
            response = await client.get(endpoint)

            # Return raw API response
            return json.dumps(response, indent=2)

        except Exception as e:
            return f"Error fetching NAICS codes: {str(e)}"

    @mcp.tool()
    async def get_psc_codes(psc_code: Optional[str] = None) -> str:
        """
        Get PSC (Product and Service Codes) information.

        Args:
            psc_code: Optional specific PSC code to look up. If not provided,
                     returns all top-level PSC codes.

        Returns:
            Raw API response data as JSON string containing PSC code information
        """
        try:
            endpoint = "references/psc/"
            if psc_code:
                endpoint += f"{psc_code}/"

            # Make API call
            response = await client.get(endpoint)

            # Return raw API response
            return json.dumps(response, indent=2)

        except Exception as e:
            return f"Error fetching PSC codes: {str(e)}"

    @mcp.tool()
    async def get_cfda_programs(cfda_code: Optional[str] = None) -> str:
        """
        Get CFDA (Catalog of Federal Domestic Assistance) program information.

        Args:
            cfda_code: Optional specific CFDA code to look up. If not provided,
                      returns all CFDA programs.

        Returns:
            Raw API response data as JSON string containing CFDA program information
        """
        try:
            endpoint = "references/cfda/"
            if cfda_code:
                endpoint += f"{cfda_code}/"

            # Make API call
            response = await client.get(endpoint)

            # Return raw API response
            return json.dumps(response, indent=2)

        except Exception as e:
            return f"Error fetching CFDA programs: {str(e)}"
