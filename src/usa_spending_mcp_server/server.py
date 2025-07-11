import asyncio
import logging

from fastmcp import FastMCP

from usa_spending_mcp_server.client import USASpendingClient
from usa_spending_mcp_server.tools.agency_spending import register_agency_tools
from usa_spending_mcp_server.tools.award_spending import register_award_search_tools
from usa_spending_mcp_server.tools.geography_spending import register_geography_tools
from usa_spending_mcp_server.tools.program_activity_spending import (
    register_program_activity_tools,
)
from usa_spending_mcp_server.tools.recipient_spending import (
    register_recipient_search_tools,
)
from usa_spending_mcp_server.tools.reference_tools import register_reference_tools
from usa_spending_mcp_server.tools.spending_explorer import (
    register_spending_explorer_tools,
)

logger = logging.getLogger(__name__)

# Create FastMCP instance with detailed instructions
mcp = FastMCP(
    name="USASpendingServer",
    instructions="""
    This server provides comprehensive access to USA government spending data through the
    USAspending.gov API.

    ## Available Tools Overview:

    ### Reference Tools (Start Here):
    - get_agencies(): Get list of all US agencies with their codes and IDs
    - get_award_types(): Get available award type codes (A=BPA, B=IDV, C=Contract, D=Grant, etc.)
    - get_glossary(): Get definitions of spending terms

    ### Agency Analysis:
    - get_sub_agency_list(): Get subagencies under a main agency
    - get_sub_components_list(): Get bureaus/offices under an agency
    - get_sub_component_details(): Get detailed info about specific bureau/office
    - list_program_activities(): Get program activities for an agency (useful for IT spending
      analysis)

    ### Award Search & Details:
    - search_spending_by_award(): Search for specific contracts, grants, loans by various criteria
    - get_award_details(): Get comprehensive details about specific award(s)

    ### Geographic Analysis:
    - search_spending_by_geography(): Analyze spending by state, county, district, or ZIP code

    ### Recipient Analysis:
    - search_recipients(): Find top contractors, grantees, and other recipients

    ### High-Level Spending Analysis:
    - search_spending_explorer(): Drill down into spending by budget function, agency, object class

    ## Best Practices:

    1. **Start with Reference Tools**: Always begin analysis by getting agencies and award types
    2. **Use Proper Date Ranges**: Default is FY2024 (2023-10-01 to 2024-09-30)
    3. **Agency Formats**: Use proper agency name formats (see agencies tool for exact names)
    4. **Award Type Codes**:
        - A: BPA (Blanket Purchase Agreement)
        - B: IDV (Indefinite Delivery Vehicle)
        - C: Contract
        - D: Grant
        - (Use get_award_types() for complete list)
    5. **Geographic Codes**: Use proper FIPS codes for counties, postal codes for states
    6. **Pagination**: Most tools support pagination - use fetch_all_pages=True for comprehensive
       results

    ## Common Analysis Patterns:

    ### Agency Spending Analysis:
    1. Get agencies list to find toptier_code
    2. Use search_spending_explorer with type="agency" for high-level view
    3. Use get_sub_components_list for detailed breakdown
    4. Use list_program_activities for specific program analysis

    ### Contract Analysis:
    1. Use search_spending_by_award with award_type_codes="C" for contracts
    2. Use get_award_details for comprehensive contract information
    3. Filter by agencies, recipients, keywords, or amounts as needed

    ### Geographic Analysis:
    1. Use search_spending_by_geography with proper geo_layer_filters
    2. Choose scope: place_of_performance vs recipient_location
    3. Use appropriate geo_layer: state, county, district, or zip

    ### Recipient Analysis:
    1. Use search_recipients to find top contractors/grantees
    2. Filter by award_type for specific analysis (contracts, grants, etc.)
    3. Use keyword search for specific company analysis

    ## Error Handling:
    - All tools return descriptive error messages
    - Check tool responses for "Error:" prefix
    - Verify agency names and codes using reference tools
    - Ensure date formats are YYYY-MM-DD

    ## Performance Tips:
    - Use appropriate page limits (default 100, max varies by endpoint)
    - Use fetch_all_pages=True cautiously (set reasonable max_pages)
    - For award details, limit to 10 awards per request for optimal performance

    Always provide clear, actionable insights based on the spending data retrieved.
    """,
)


def main():
    """Main entry point"""
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting USA Spending MCP Server")

    # Run the asynchronous main function
    asyncio.run(async_main())


async def async_main():
    """Async entry point"""
    # Initialize HTTP client
    async with USASpendingClient() as client:
        # Register tools
        logger.info("Registering tools")
        register_agency_tools(mcp, client)
        register_award_search_tools(mcp, client)
        register_geography_tools(mcp, client)
        register_program_activity_tools(mcp, client)
        register_recipient_search_tools(mcp, client)
        register_reference_tools(mcp, client)
        register_spending_explorer_tools(mcp, client)

        logger.info("Running USA Spending MCP Server")
        await mcp.run_async()


if __name__ == "__main__":
    main()
