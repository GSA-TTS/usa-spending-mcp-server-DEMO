"""
login.gov authentication for MCP servers.

This module provides login.gov OIDC authentication for FastMCP servers.
It can be used standalone or as a reference for a reusable package.

Architecture:
    MCP Client (Claude Desktop) -> MCP Server (OIDCProxy) -> login.gov

The MCP server uses FastMCP's OIDCProxy configured as a public client:
    - login.gov doesn't support client_secret authentication
    - Instead, we use PKCE (Proof Key for Code Exchange) for security
    - OIDCProxy handles the OAuth flow and issues its own JWTs to MCP clients

Flow:
    1. MCP client requests a protected resource
    2. Server returns 401 with WWW-Authenticate header pointing to resource metadata
    3. Client fetches /.well-known/oauth-protected-resource
    4. Client initiates OAuth flow with the server's authorization endpoint
    5. Server redirects to login.gov with PKCE + nonce
    6. User authenticates at login.gov
    7. login.gov redirects back with auth code
    8. Server exchanges code for token (using PKCE, no client_secret)
    9. Server validates user via login.gov userinfo endpoint
    10. Server issues its own JWT to the MCP client
    11. Client uses JWT for subsequent requests

Environment Variables:
    BASE_URL: Public URL of the MCP server (e.g., https://my-mcp.app.cloud.gov)
    LOGINGOV_CLIENT_ID: Client ID registered with login.gov
    LOGINGOV_CONFIG_URL: OIDC discovery URL (defaults to sandbox)
    JWT_SIGNING_KEY: Secret key for signing JWTs issued to MCP clients
    REQUIRE_AUTH: Set to "false" to disable authentication (for local dev)

login.gov Setup:
    1. Register at https://partners.login.gov/
    2. Create a new application with:
       - Protocol: OpenID Connect (OIDC) with PKCE
       - Redirect URI: {BASE_URL}/auth/callback
    3. Note the client ID (no client secret needed for PKCE)

Usage:
    from usa_spending_mcp_server.auth import create_logingov_auth

    mcp = FastMCP(
        name="MyServer",
        auth=create_logingov_auth(),  # Returns None if REQUIRE_AUTH=false
    )
"""

import logging
import os
import secrets
from typing import Any

import httpx
from fastmcp.server.auth import AccessToken, TokenVerifier
from fastmcp.server.auth.oidc_proxy import OIDCProxy

logger = logging.getLogger(__name__)

# login.gov OIDC configuration URLs
LOGINGOV_SANDBOX_CONFIG_URL = "https://idp.int.identitysandbox.gov/.well-known/openid-configuration"
LOGINGOV_PRODUCTION_CONFIG_URL = "https://secure.login.gov/.well-known/openid-configuration"


def _require_auth_env() -> bool:
    """Return whether authentication is required (default: true)."""
    return os.getenv("REQUIRE_AUTH", "true").strip().lower() in ("1", "true", "yes")


class LoginGovTokenVerifier(TokenVerifier):
    """
    Token verifier for login.gov that validates access tokens via the userinfo endpoint.

    login.gov issues opaque access tokens (not JWTs), so validation is performed
    by calling the OIDC userinfo endpoint. A successful response implies a valid token.
    """

    def __init__(self, userinfo_url: str, timeout_seconds: int = 10):
        super().__init__()
        self.userinfo_url = userinfo_url
        self.timeout_seconds = timeout_seconds
        self.logger = logging.getLogger(__name__)

    async def verify_token(self, token: str) -> AccessToken | None:
        """Verify token by calling the login.gov userinfo endpoint."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(
                    self.userinfo_url,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/json",
                    },
                )

            if response.status_code != 200:
                self.logger.debug("Userinfo validation failed: HTTP %d", response.status_code)
                return None

            userinfo = response.json()

            # 'sub' is the stable login.gov user identifier
            sub = userinfo.get("sub")
            if not sub:
                self.logger.debug("Userinfo response missing 'sub' claim")
                return None

            # NOTE:
            # AccessToken.client_id is used by FastMCP to identify the authenticated
            # principal. We intentionally set it to the login.gov subject ('sub'),
            # which uniquely identifies the user in this system.
            return AccessToken(
                token=token,
                client_id=str(sub),
                scopes=["openid", "email"],
                expires_at=None,  # userinfo does not return expiration
                claims=userinfo,
            )

        except httpx.TimeoutException:
            self.logger.debug("Userinfo request timed out")
            return None
        except Exception:
            self.logger.exception("Userinfo validation error")
            return None


class LoginGovOIDCProxy(OIDCProxy):
    """
    OIDCProxy subclass that adds nonce support required by login.gov.

    login.gov requires a nonce parameter (minimum 22 characters) in the
    authorization request. This subclass injects a compliant nonce.
    """

    def _build_upstream_authorize_url(self, txn_id: str, transaction: dict[str, Any]) -> str:
        # Generate a nonce (minimum 22 chars per login.gov requirements)
        nonce = txn_id if len(txn_id) >= 22 else secrets.token_urlsafe(32)

        # Persist nonce with the transaction for later validation
        transaction["nonce"] = nonce

        # Build base authorization URL using parent logic
        url = super()._build_upstream_authorize_url(txn_id, transaction)

        # Append nonce parameter
        separator = "&" if "?" in url else "?"
        return f"{url}{separator}nonce={nonce}"


def get_userinfo_url_from_config(config_url: str) -> str:
    """Fetch the userinfo endpoint from the OIDC discovery document."""
    try:
        response = httpx.get(config_url, timeout=30)
        response.raise_for_status()
        doc = response.json()

        userinfo_url = doc.get("userinfo_endpoint")
        if not userinfo_url:
            raise RuntimeError("OIDC discovery document missing 'userinfo_endpoint'")

        return userinfo_url

    except Exception:
        logger.exception("Failed to fetch OIDC discovery document from %s", config_url)
        raise


def create_logingov_auth(
    base_url: str | None = None,
    client_id: str | None = None,
    jwt_signing_key: str | None = None,
    config_url: str | None = None,
) -> LoginGovOIDCProxy | None:
    """
    Create a login.gov authentication provider for FastMCP.

    Configuration is read from parameters or environment variables.

    Returns None if REQUIRE_AUTH=false.
    """
    if not _require_auth_env():
        logger.info("Authentication disabled (REQUIRE_AUTH=false)")
        return None

    # Resolve configuration
    base_url = base_url or os.getenv("BASE_URL")
    client_id = client_id or os.getenv("LOGINGOV_CLIENT_ID")
    jwt_signing_key = jwt_signing_key or os.getenv("JWT_SIGNING_KEY")
    config_url = config_url or os.getenv("LOGINGOV_CONFIG_URL") or LOGINGOV_SANDBOX_CONFIG_URL

    if not base_url or not client_id:
        raise ValueError("BASE_URL and LOGINGOV_CLIENT_ID are required when REQUIRE_AUTH=true")

    if not jwt_signing_key:
        raise ValueError(
            "JWT_SIGNING_KEY is required. "
            'Generate one with: python -c "import secrets; print(secrets.token_hex(32))"'
        )

    logger.info("Configuring login.gov OIDC authentication (public client with PKCE)")
    logger.info("Base URL: %s", base_url)
    logger.info("Client ID: %s", client_id)
    logger.info("OIDC Config URL: %s", config_url)

    # Fetch userinfo endpoint for token verification
    userinfo_url = get_userinfo_url_from_config(config_url)
    logger.info("Userinfo endpoint: %s", userinfo_url)

    token_verifier = LoginGovTokenVerifier(userinfo_url=userinfo_url)

    return LoginGovOIDCProxy(
        config_url=config_url,
        client_id=client_id,
        # OIDCProxy requires client_secret to be set even when using
        # token_endpoint_auth_method="none" (public PKCE client).
        client_secret="unused",
        token_endpoint_auth_method="none",
        token_verifier=token_verifier,
        base_url=base_url,
        jwt_signing_key=jwt_signing_key,
        extra_authorize_params={
            "scope": "openid email",
            "acr_values": "urn:acr.login.gov:auth-only",
        },
    )
