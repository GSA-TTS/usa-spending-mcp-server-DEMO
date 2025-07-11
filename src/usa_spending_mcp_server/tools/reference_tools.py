from typing import Any

from fastmcp import FastMCP

from usa_spending_mcp_server.client import USASpendingClient


def register_reference_tools(mcp: FastMCP, client: USASpendingClient):
    """Register reference/lookup tools"""

    @mcp.tool()
    async def get_agencies() -> Any:
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
            return response

        except Exception as e:
            return f"Error fetching agencies: {str(e)}"

    @mcp.tool()
    async def get_award_types() -> Any:
        """
        Get all available award types and their codes.

        Use this to understand what award type codes (A, B, C, D, etc.) mean
        for filtering spending data.

        Returns:
            Raw API response data as JSON string containing award type information
        """
        try:
            # Make API call
            response = await client.get("references/award_types/")

            # Return raw API response
            return response

        except Exception as e:
            return f"Error fetching award types: {str(e)}"

    @mcp.tool()
    async def get_glossary() -> Any:
        """
        Get glossary terms to help understand and present analysis of data

        Returns:
            Raw API response data as JSON string containing glossary terms
        """
        try:
            endpoint = "references/glossary/"

            # Make API call
            response = await client.get(endpoint)

            # Return raw API response
            return response

        except Exception as e:
            return f"Error fetching glossary:  {str(e)}"
