"""
HTTP server for USA Spending MCP Server.

This module provides an HTTP entry point for running the MCP server
on cloud.gov with login.gov authentication via OIDC.

Uses FastMCP's OIDCProxy with auto-discovery as a public client with PKCE
(login.gov doesn't support client_secret authentication).

Usage:
    # Local development (no auth)
    REQUIRE_AUTH=false python -m usa_spending_mcp_server.server_http

    # Production (with login.gov auth)
    python -m usa_spending_mcp_server.server_http

Environment variables:
    HOST: Host to bind to (default: 0.0.0.0)
    PORT: Port to bind to (default: 8080)
    REQUIRE_AUTH: Require authentication (default: true)
    BASE_URL: Public URL of this server (required for auth)
    LOGINGOV_CLIENT_ID: login.gov client ID (register at partners.login.gov)
    LOGINGOV_CONFIG_URL: OIDC discovery URL (default: sandbox, set to production URL for prod)
    JWT_SIGNING_KEY: Secret for signing JWTs issued to MCP clients
"""

import logging
import os

import uvicorn
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from usa_spending_mcp_server.auth import create_logingov_auth
from usa_spending_mcp_server.client import USASpendingClient
from usa_spending_mcp_server.server import mcp as base_mcp
from usa_spending_mcp_server.tools.agency_spending import register_agency_tools
from usa_spending_mcp_server.tools.award_spending import register_award_search_tools
from usa_spending_mcp_server.tools.category_spending import register_category_spending_tools
from usa_spending_mcp_server.tools.disaster_spending import register_disaster_spending_tools
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
from usa_spending_mcp_server.tools.spending_over_time import register_spending_over_time_tools
from usa_spending_mcp_server.tools.subaward_spending import register_subaward_tools
from usa_spending_mcp_server.tools.spending_over_time import register_spending_over_time_tools

logger = logging.getLogger(__name__)


def _require_auth_env() -> bool:
    """Return whether auth is required based on env var REQUIRE_AUTH (default true)."""
    return os.getenv("REQUIRE_AUTH", "true").strip().lower() in ("1", "true", "yes")


def create_server() -> FastMCP:
    """Create and configure the MCP server."""
    auth = create_logingov_auth()

    require_auth = _require_auth_env()
    if require_auth and not auth:
        raise RuntimeError(
            "Authentication is required in HTTP server mode but no auth was configured"
        )

    client = USASpendingClient()

    logger.info("Creating MCP server (auth %s)", "enabled" if auth else "disabled")
    server = FastMCP(
        name="USASpendingServer",
        instructions=base_mcp.instructions,
        auth=auth if require_auth else None,
    )

    logger.info("Registering tools")
    register_agency_tools(server, client)
    register_award_search_tools(server, client)
    register_category_spending_tools(server, client)
    register_disaster_spending_tools(server, client)
    register_geography_tools(server, client)
    register_program_activity_tools(server, client)
    register_recipient_search_tools(server, client)
    register_reference_tools(server, client)
    register_spending_explorer_tools(server, client)
    register_spending_over_time_tools(server, client)
    register_subaward_tools(server, client)
    logger.info("Tools registered")

    return server


mcp = create_server()


@mcp.custom_route("/health", methods=["GET"])
async def health_check(_request: Request) -> JSONResponse:
    """Health check endpoint for monitoring and load balancers."""
    return JSONResponse({"status": "healthy", "service": "usa-spending-mcp"})


app = mcp.http_app()


def main():
    """Main entry point for HTTP server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))

    logger.info(f"Starting server on {host}:{port}")
    logger.info(f"Health check: http://{host}:{port}/health")

    uvicorn.run(
        "usa_spending_mcp_server.server_http:app",
        host=host,
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
