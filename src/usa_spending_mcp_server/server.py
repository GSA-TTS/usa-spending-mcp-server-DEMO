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
# Create FastMCP instance with detailed instructions
mcp = FastMCP(
    name="USASpendingServer",
    instructions="""
    This server provides comprehensive access to USA government spending data through the
    USAspending.gov API.

    ## Quick Tool Selection Guide:

    **"Which agency spent the most on [category] in FY2023?"**
    → Use search_spending_explorer() with type="agency" or type="object_class"

    **"Show me the largest contracts awarded by [agency]"**
    → Use search_spending_by_award() with agencies filter and award_type_codes=["A","B","C","D"]

    **"How much did [state/county] receive in federal spending?"**
    → Use search_spending_by_geography() with appropriate geo_layer and geo_layer_filters

    **"Who are the top contractors/recipients of federal money?"**
    → Use search_recipients() with award_type filter

    **"What are the details of contract XYZ?"**
    → Use search_spending_by_award() with award_ids filter

    ## Tool Categories & When to Use:

    ### 🔍 REFERENCE TOOLS (Always Start Here)
    **Use when:** You need agency codes, award types, or term definitions
    - get_agencies(): Get list of all US agencies with their codes and IDs
    - get_award_types(): Get available award type codes (A=BPA, B=IDV, C=Contract, D=Grant, etc.)
    - get_glossary(): Get definitions of spending terms

    ### 📊 HIGH-LEVEL ANALYSIS (Agency Totals & Comparisons)
    **Use when:** Answering "which agency/category spent the most" questions
    - search_spending_explorer(): **BEST FOR:** 
      * "Which agency had highest contract spending?"
      * "What are DOD's spending categories?"
      * "Compare agencies by object class"
      * "Federal account analysis"
    **Returns:** Aggregated totals, perfect for comparisons and rankings

    ### 🏢 AGENCY DEEP DIVE
    **Use when:** You need to understand agency structure and program spending
    - get_sub_agency_list(): Get subagencies under a main agency
    - get_sub_components_list(): Get bureaus/offices under an agency  
    - get_sub_component_details(): Get detailed info about specific bureau/office
    - list_program_activities(): **BEST FOR:** IT spending analysis, program breakdowns

    ### 📝 INDIVIDUAL AWARDS/CONTRACTS
    **Use when:** You need specific contract details or want to search individual awards
    - search_spending_by_award(): **BEST FOR:**
      * "Show me Amazon's contracts with the government"
      * "Find all cybersecurity contracts over $1M"
      * "What contracts did DOD award in 2023?"
      * "Details of specific award ID"
    **Returns:** Individual award records with full details

    ### 🗺️ GEOGRAPHIC ANALYSIS
    **Use when:** Analyzing spending by location
    - search_spending_by_geography(): **BEST FOR:**
      * "How much federal spending went to California?"
      * "Top counties for defense spending"
      * "ZIP code analysis for grants"
    **Key:** Use place_of_performance vs recipient_location scope appropriately

    ### 🏭 RECIPIENT ANALYSIS  
    **Use when:** Finding top contractors, grantees, or analyzing specific companies
    - search_recipients(): **BEST FOR:**
      * "Top 10 government contractors"
      * "Which companies got the most grants?"
      * "Find recipients with 'Boeing' in the name"

    ## Decision Matrix:

    | Question Type | Primary Tool | Secondary Tools |
    |---------------|-------------|-----------------|
    | Agency spending totals/rankings | search_spending_explorer | get_agencies |
    | Individual contract details | search_spending_by_award | get_award_types |
    | Geographic spending distribution | search_spending_by_geography | - |
    | Company/recipient analysis | search_recipients | search_spending_by_award |
    | Agency organizational structure | get_sub_components_list | list_program_activities |
    | Spending category breakdowns | search_spending_explorer (object_class) | - |

    ## Common Mistakes to Avoid:

    ❌ **Don't use search_spending_by_award for "which agency spent the most"**
    ✅ **Use search_spending_explorer instead**

    ❌ **Don't use search_spending_explorer for individual contract details**  
    ✅ **Use search_spending_by_award instead**

    ❌ **Don't forget to get agency codes first**
    ✅ **Start with get_agencies() to find correct agency names/codes**

    ## Key Parameters:

    ### Time Periods:
    - **FY 2024:** 2023-10-01 to 2024-09-30 (default)
    - **FY 2023:** 2022-10-01 to 2023-09-30
    - Format: YYYY-MM-DD

    ### Award Types:
    - **A:** BPA (Blanket Purchase Agreement)
    - **B:** IDV (Indefinite Delivery Vehicle)  
    - **C:** Contract
    - **D:** Grant
    - **Use get_award_types() for complete list**

    ### Object Classes (for spending_explorer):
    - **"20":** Contractual services and supplies (most contracts)
    - **"10":** Personnel compensation and benefits
    - **"30":** Acquisition of assets
    - **"40":** Grants and fixed charges

    ### Geographic Codes:
    - **States:** Use 2-letter postal codes (CA, TX, NY)
    - **Counties:** Use 5-digit FIPS codes (06037 for Los Angeles County)
    - **Districts:** Use state + district (CA12, TX01)
    - **ZIP:** Use 5-digit ZIP codes (90210, 20500)

    ## Best Practices:

    1. **Always start with reference tools** to get proper agency names and codes
    2. **Match tool to question type** using the decision matrix above
    3. **Use appropriate pagination** (default 100, increase for comprehensive results)
    4. **Verify agency names** - use exact names from get_agencies()
    5. **For contract analysis,** object class "20" captures most contract spending
    6. **For geographic analysis,** choose place_of_performance vs recipient_location carefully

    ## Performance Tips:
    - Limit award details requests to 10 awards per call
    - Use fetch_all_pages=True cautiously with max_pages limits
    - Start with smaller date ranges for large queries

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
