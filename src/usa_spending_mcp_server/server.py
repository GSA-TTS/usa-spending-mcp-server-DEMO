from fastmcp import FastMCP

from usa_spending_mcp_server.client import USASpendingClient
from usa_spending_mcp_server.tools.agency_spending import register_agency_tools
from usa_spending_mcp_server.tools.award_spending import register_award_search_tools
from usa_spending_mcp_server.tools.geography_spendingy import register_geography_tools
from usa_spending_mcp_server.tools.recipient_spending import (
    register_recipient_search_tools,
)
from usa_spending_mcp_server.tools.reference_tools import register_reference_tools
from usa_spending_mcp_server.tools.spending_explorer import (
    register_spending_explorer_tools,
)


def main():
    """Main entry point"""
    # Initialize client
    client = USASpendingClient()

    # Initialize FastMCP
    mcp = FastMCP("USA Spending API")

    # Register tools
    register_geography_tools(mcp, client)
    register_award_search_tools(mcp, client)
    register_reference_tools(mcp, client)
    register_agency_tools(mcp, client)
    register_spending_explorer_tools(mcp, client)
    register_recipient_search_tools(mcp, client)

    try:
        # Run the server (this blocks and manages its own event loop)
        mcp.run()
    except KeyboardInterrupt:
        print("Shutting down gracefully...")


if __name__ == "__main__":
    main()
