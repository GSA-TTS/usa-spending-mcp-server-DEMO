import asyncio
import logging

from fastmcp import FastMCP
from fastmcp.experimental.transforms.code_mode import CodeMode

from usa_spending_mcp_server.client import USASpendingClient
from usa_spending_mcp_server.tools.agency_spending import register_agency_tools
from usa_spending_mcp_server.tools.award_spending import register_award_search_tools
from usa_spending_mcp_server.tools.category_spending import (
    register_category_spending_tools,
)
from usa_spending_mcp_server.tools.disaster_spending import (
    register_disaster_spending_tools,
)
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
from usa_spending_mcp_server.tools.spending_over_time import (
    register_spending_over_time_tools,
)
from usa_spending_mcp_server.tools.subaward_spending import register_subaward_tools

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
    → Use search_spending_by_category(category="recipient") for filtered recipient rankings

    **"What are the details of contract XYZ?"**
    → Use search_awards() with award_ids filter, then get_award_details() for full details

    **"How has spending changed over time?"**
    → Use search_spending_over_time() with group="fiscal_year", "quarter", or "month"

    **"What is disaster/emergency spending?"**
    → Use get_def_codes() then search_disaster_spending() with DEFC codes

    **"Which agency had highest contract spending?"**
    → Use get_agency_obligations_by_award_category() for per-agency award type breakdown

    **"What's the gap between obligations and actual spending?"**
    → Use get_agency_budgetary_resources() for obligations vs outlays comparison

    **"Top recipients in a specific state?"**
    → Use search_spending_by_category(category="recipient", filters with recipient_locations)

    **"What are the top NAICS codes/industries for DOD?"**
    → Use search_spending_by_category(category="naics", filters with agencies)

    ## Tool Categories & When to Use:

    ### REFERENCE TOOLS (Always Start Here)
    **Use when:** You need agency codes, award types, or term definitions
    - get_agencies(): Get list of all US agencies with their codes and IDs
    - get_award_types(): Get available award type codes
    - get_glossary(search_term): Get definitions of spending terms (use search_term to filter)
    - get_def_codes(): Get Disaster Emergency Fund Codes (DEFC)

    ### COMPREHENSIVE AWARD SEARCH (Primary Search Tool)
    **Use when:** Searching for individual awards — returns awards + aggregates in one call
    - search_awards(): Returns individual award records + counts + totals +
      time trends + geographic breakdown + awarding agency breakdown
      * Now always includes obligation totals (even without keywords)
      * Supports cursor-based pagination via awards.next_cursor

    ### SPENDING BY CATEGORY (Aggregated Rankings)
    **Use when:** You need top-N rankings by any dimension
    - search_spending_by_category(): Aggregate by recipient, agency, NAICS, PSC,
      CFDA, state, county, district, federal_account, defc
      * Supports all standard filters + geographic location filters
      * Best for "top recipients in state X" or "top industries for agency Y"

    ### TIME SERIES ANALYSIS
    **Use when:** Analyzing trends over time
    - search_spending_over_time(): Standalone time-series with fiscal_year/quarter/month grouping
    - search_new_awards_over_time(): Track new award creation trends

    ### HIGH-LEVEL ANALYSIS (Agency Totals & Comparisons)
    **Use when:** Answering "which agency/category spent the most" questions
    - search_spending_explorer(): Aggregated totals by agency, budget function, object class
    - get_agency_obligations_by_award_category(): Per-agency contract/grant/loan breakdown
    - get_agency_budgetary_resources(): Obligations vs outlays vs budget authority

    ### AGENCY DEEP DIVE
    - get_sub_agency_list(): Get subagencies under a main agency
    - get_sub_components_list(): Get bureaus/offices under an agency
    - get_sub_component_details(): Get detailed bureau/office info
    - list_program_activities(): IT spending analysis, program breakdowns

    ### AWARD DETAILS
    - get_award_details(): Fetch full details for specific award IDs
      (use generated_internal_id from search_awards results)

    ### GEOGRAPHIC ANALYSIS
    - search_spending_by_geography(): State/county/district/ZIP spending breakdowns
      * Pass empty geo_layer_filters to get ALL results for a layer
    - search_disaster_spending_by_geography(): Disaster spending by geography

    ### DISASTER/EMERGENCY SPENDING
    - get_disaster_overview(): High-level disaster spending totals
    - search_disaster_spending(): Agency-level disaster spending with DEFC filters
    - search_disaster_spending_by_geography(): Geographic disaster spending

    ### RECIPIENT ANALYSIS
    - search_recipients(): Top contractors, grantees; search by company name

    ### SUBAWARD ANALYSIS
    - search_subawards(): Individual subaward records
    - search_subaward_totals(): Subaward totals grouped by prime award

    ## Key Parameters:

    ### Time Periods:
    - **FY 2025:** 2024-10-01 to 2025-09-30
    - **FY 2024:** 2023-10-01 to 2024-09-30
    - **FY 2023:** 2022-10-01 to 2023-09-30
    - Format: YYYY-MM-DD
    - **Earliest date: 2007-10-01** (for older data, use bulk download)

    ### Award Types (must NOT mix groups in search_awards):
    - **Contracts:** A, B, C, D
    - **Grants:** 02, 03, 04, 05
    - **Direct Payments:** 06, 10
    - **Loans:** 07, 08
    - **Other:** 09, 11, -1
    - Use get_award_types() for complete list

    ### Important Distinctions:
    - **Award Amount** in search results = total award value (all years)
    - **Obligations** = money committed in a specific fiscal year
    - **Outlays** = money actually paid out
    - For FY-specific obligation data, use search_spending_over_time()
    - Defense spending may be delayed 90 days and some classified data excluded

    ### Known Quirks:
    - recipient_search_text + agencies filters may not work together reliably.
      Use `keywords` instead, or use search_spending_by_category(category="recipient")
    - award_type_codes must be from same group in search_awards.
      For cross-type analysis, make separate calls or use search_spending_over_time
    - **Subtier agency names must be exact.** Names like "Bureau of Indian Affairs"
      may actually be "Bureau of Indian Affairs and Bureau of Indian Education" in the API.
      Always use get_sub_agency_list() first to discover exact subtier names.
    - **keywords + subtier agencies** may return 0 results even when data exists.
      Workaround: search at toptier level with keywords, or use subtier without keywords.
    - **Contract totals from get_agency_obligations_by_award_category()** report
      "contracts" and "idvs" (Indefinite Delivery Vehicles) separately. For total
      contract spending, sum both categories.

    ### Pagination:
    - search_awards() returns awards.next_cursor when more pages exist
    - Pass cursor back to search_awards() to get next page (skips aggregate calls)

    ## Best Practices:
    1. Start with reference tools to get proper agency names and codes
    2. Use search_awards() for individual award-level queries
    3. Use search_spending_by_category() for top-N rankings
    4. Use search_spending_over_time() for trends and total obligation amounts
    5. Use search_spending_explorer() for cross-agency budget comparisons
    6. Use get_agency_obligations_by_award_category() for contract vs grant breakdowns
    7. For geographic analysis, choose place_of_performance vs recipient_location carefully
    8. For disaster spending, always use dedicated disaster tools with DEFC codes
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
        register_category_spending_tools(mcp, client)
        register_disaster_spending_tools(mcp, client)
        register_geography_tools(mcp, client)
        register_program_activity_tools(mcp, client)
        register_recipient_search_tools(mcp, client)
        register_reference_tools(mcp, client)
        register_spending_explorer_tools(mcp, client)
        register_spending_over_time_tools(mcp, client)
        register_subaward_tools(mcp, client)

        logger.info("Running USA Spending MCP Server")
        await mcp.run_async()


if __name__ == "__main__":
    main()
