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
from typing import Optional

import uvicorn
from fastmcp import FastMCP

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from usa_spending_mcp_server.server import mcp as base_mcp
from usa_spending_mcp_server.auth import create_logingov_auth
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


def _require_auth_env() -> bool:
    """Return whether auth is required based on env var REQUIRE_AUTH (default true)."""
    return os.getenv("REQUIRE_AUTH", "true").strip().lower() in ("1", "true", "yes")


def create_mcp_server() -> FastMCP:
    """
    Create FastMCP server with login.gov authentication (or no auth in dev).

    NOTES:
      - If REQUIRE_AUTH is true and create_logingov_auth() returns falsy, raise.
      - If REQUIRE_AUTH is false, allow auth to be None (local dev).
    """
    auth = create_logingov_auth()

    require_auth = _require_auth_env()
    if require_auth and not auth:
        # In production mode we must have auth configured
        raise RuntimeError("Authentication is required in HTTP server mode but no auth was configured")

    logger.info("Creating MCP server (auth %s)", "enabled" if auth else "disabled")
    return FastMCP(
        name="USASpendingServer",
        instructions=base_mcp.instructions,
        auth=auth,
    )


# Create the MCP server at import time, but creation will NOT raise if auth is missing
# when REQUIRE_AUTH=false (local dev). This ensures `app` exists for Uvicorn imports.
mcp: FastMCP = create_mcp_server()

# Global client - initialized lazily on first request/startup
_client: Optional[USASpendingClient] = None

def get_client() -> USASpendingClient:
    """Get the global HTTP client, initializing if needed (synchronous init only)."""
    global _client
    if _client is None:
        _client = USASpendingClient()
    return _client


async def startup():
    """Initialize resources on startup."""
    global _client, mcp
    logger.info("Starting USA Spending MCP Server (HTTP mode)")

    # Ensure client is initialized and enter async context
    if _client is None:
        _client = USASpendingClient()
    # Enter async context for the client (establish connections, etc.)
    await _client.__aenter__()

    # Register tools now that the client is available and app lifecycle is running
    logger.info("Registering tools")
    # Passing the already-created mcp instance
    register_agency_tools(mcp, _client)
    register_award_search_tools(mcp, _client)
    register_geography_tools(mcp, _client)
    register_program_activity_tools(mcp, _client)
    register_recipient_search_tools(mcp, _client)
    register_reference_tools(mcp, _client)
    register_spending_explorer_tools(mcp, _client)
    logger.info("Tools registered")

    logger.info("USA Spending MCP Server ready")


async def shutdown():
    """Cleanup resources on shutdown."""
    global _client
    if _client:
        await _client.__aexit__(None, None, None)
        _client = None
    logger.info("USA Spending MCP Server stopped")


def _health_check(request):
    return JSONResponse({"status": "healthy"})


def create_app():
    """
    Create and return the ASGI Starlette application.

    We obtain the FastMCP HTTP app and use it as the root app. We also add a
    simple health endpoint and lifecycle handlers.
    """
    # Get the HTTP app from FastMCP (includes auth middleware automatically)
    app = mcp.http_app()

    # Add health check endpoint (kept as a simple route)
    app.routes.append(Route("/health", _health_check, methods=["GET"]))

    # Add lifecycle handlers
    app.add_event_handler("startup", startup)
    app.add_event_handler("shutdown", shutdown)

    return app


# Create the app instance for Uvicorn/Gunicorn to import
app = create_app()


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
