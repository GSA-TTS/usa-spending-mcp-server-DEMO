"""Tests for login.gov authentication module."""

import os
from unittest.mock import patch

import pytest

from usa_spending_mcp_server.auth import (
    LOGINGOV_SANDBOX_CONFIG_URL,
    LoginGovTokenVerifier,
    create_logingov_auth,
)


class TestLoginGovTokenVerifier:
    """Tests for LoginGovTokenVerifier."""

    def test_init(self):
        """Test verifier initialization."""
        verifier = LoginGovTokenVerifier(
            userinfo_url="https://example.com/userinfo",
            timeout_seconds=5,
        )
        assert verifier.userinfo_url == "https://example.com/userinfo"
        assert verifier.timeout_seconds == 5


class TestCreateLogingovAuth:
    """Tests for create_logingov_auth factory function."""

    def test_returns_none_when_auth_disabled(self):
        """Test that auth is disabled when REQUIRE_AUTH=false."""
        with patch.dict(os.environ, {"REQUIRE_AUTH": "false"}):
            result = create_logingov_auth()
            assert result is None

    def test_raises_when_missing_base_url(self):
        """Test that missing BASE_URL raises ValueError."""
        env = {
            "REQUIRE_AUTH": "true",
            "LOGINGOV_CLIENT_ID": "test-client",
            "JWT_SIGNING_KEY": "test-key",
        }
        with patch.dict(os.environ, env, clear=True), pytest.raises(ValueError, match="BASE_URL"):
            create_logingov_auth()

    def test_raises_when_missing_client_id(self):
        """Test that missing LOGINGOV_CLIENT_ID raises ValueError."""
        env = {
            "REQUIRE_AUTH": "true",
            "BASE_URL": "https://example.com",
            "JWT_SIGNING_KEY": "test-key",
        }
        with (
            patch.dict(os.environ, env, clear=True),
            pytest.raises(ValueError, match="LOGINGOV_CLIENT_ID"),
        ):
            create_logingov_auth()

    def test_raises_when_missing_jwt_key(self):
        """Test that missing JWT_SIGNING_KEY raises ValueError."""
        env = {
            "REQUIRE_AUTH": "true",
            "BASE_URL": "https://example.com",
            "LOGINGOV_CLIENT_ID": "test-client",
        }
        with (
            patch.dict(os.environ, env, clear=True),
            pytest.raises(ValueError, match="JWT_SIGNING_KEY"),
        ):
            create_logingov_auth()


class TestConstants:
    """Tests for module constants."""

    def test_sandbox_config_url(self):
        """Test sandbox config URL is correct."""
        assert "identitysandbox.gov" in LOGINGOV_SANDBOX_CONFIG_URL
        assert ".well-known/openid-configuration" in LOGINGOV_SANDBOX_CONFIG_URL
