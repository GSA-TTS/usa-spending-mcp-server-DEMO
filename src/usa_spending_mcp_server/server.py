import asyncio
import logging

from fastmcp import FastMCP
from fastmcp.experimental.transforms.code_mode import CodeMode

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

mcp = FastMCP(
    name="USASpendingServer",
    # Paginate tool listings so clients handle large catalogs gracefully
    list_page_size=50,
    # Code mode: LLM discovers and chains tools via meta-tools rather than
    # loading the full catalog upfront — reduces context overhead
    transforms=[CodeMode()],
    instructions="""
    This server provides comprehensive access to USA government spending data through the
    USAspending.gov API.

    ## Quick Tool Selection Guide:

    **"Which agency spent the most on [category] in FY2023?"**
    → Use search_spending_explorer() with type="agency" or type="object_class"

    **"Show me the largest contracts awarded by [agency]"**
    → Use search_awards() with agencies filter and award_type_codes=["A","B","C","D"]

    **"How much did [state/county] receive in federal spending?"**
    → Use search_spending_by_geography() with appropriate geo_layer and geo_layer_filters

    **"Who are the top contractors/recipients of federal money?"**
    → Use search_recipients() with award_type filter

    **"What are the details of contract XYZ?"**
    → Use search_awards() with award_ids filter, then get_award_details() for full details

    ## Tool Categories & When to Use:

    ### 🔍 REFERENCE TOOLS (Always Start Here)
    **Use when:** You need agency codes, award types, or term definitions
    - get_agencies(): Get list of all US agencies with their codes and IDs
    - get_award_types(): Get available award type codes (A=BPA, B=IDV, C=Contract, D=Grant, etc.)
    - get_glossary(): Get definitions of spending terms

    ### 🏆 COMPREHENSIVE AWARD SEARCH (Primary Search Tool)
    **Use when:** Searching for awards — returns awards + aggregates in one call
    - search_awards(): **BEST FOR:**
      * "How much did Ernst & Young get from HHS OIG in FY2023?"
      * "Which states get the most broadband funding?"
      * "Find all DOD contracts over $1M"
      * Returns: individual award records + counts by type + totals +
        time trends + geographic breakdown + awarding agency breakdown
      * Supports cursor-based pagination via awards.next_cursor

    ### 📊 HIGH-LEVEL ANALYSIS (Agency Totals & Comparisons)
    **Use when:** Answering "which agency/category spent the most" questions
    - search_spending_explorer(): **BEST FOR:**
      * "Which agency had highest contract spending?"
      * "Compare agencies by object class"
      * "Federal account analysis"
    **Returns:** Aggregated totals, perfect for comparisons and rankings

    ### 🏢 AGENCY DEEP DIVE
    - get_sub_agency_list(): Get subagencies under a main agency
    - get_sub_components_list(): Get bureaus/offices under an agency
    - get_sub_component_details(): Get detailed bureau/office info
    - list_program_activities(): IT spending analysis, program breakdowns

    ### 📝 AWARD DETAILS
    - get_award_details(): Fetch full details for specific award IDs
      (use generated_internal_id from search_awards results)

    ### 🗺️ GEOGRAPHIC ANALYSIS
    - search_spending_by_geography(): State/county/district/ZIP spending breakdowns

    ### 🏭 RECIPIENT ANALYSIS
    - search_recipients(): Top contractors, grantees; search by company name

    ## Key Parameters:

    ### Time Periods:
    - **FY 2024:** 2023-10-01 to 2024-09-30 (default)
    - **FY 2023:** 2022-10-01 to 2023-09-30
    - Format: YYYY-MM-DD

    ### Award Types:
    - **A:** BPA Call  **B:** Purchase Order  **C:** Delivery Order  **D:** Definitive Contract
    - **02-05:** Grants  **06,10:** Direct Payments  **07,08:** Loans
    - **Use get_award_types() for complete list**

    ### Pagination:
    - search_awards() returns awards.next_cursor when more pages exist
    - Pass cursor back to search_awards() to get next page (skips aggregate calls)

    ## Best Practices:
    1. Start with reference tools to get proper agency names and codes
    2. Use search_awards() for all award-level queries — it returns aggregates too
    3. Use search_spending_explorer() for cross-agency budget comparisons
    4. For geographic analysis, choose place_of_performance vs recipient_location carefully
    """,
)


def main():
    """Main entry point"""
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting USA Spending MCP Server")
    asyncio.run(async_main())


async def async_main():
    """Async entry point"""
    async with USASpendingClient() as client:
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
