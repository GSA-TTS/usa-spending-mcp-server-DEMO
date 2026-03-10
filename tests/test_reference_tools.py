"""Tests for reference tools using FastMCP Client."""


class TestGetAgencies:
    """Tests for get_agencies tool."""

    async def test_calls_correct_endpoint(self, mock_usa_client, reference_mcp_client):
        """get_agencies calls /references/toptier_agencies/."""
        mock_usa_client.get.return_value = {"results": [{"name": "DOD", "toptier_code": "097"}]}

        await reference_mcp_client.call_tool("get_agencies", {})

        mock_usa_client.get.assert_called_once_with("references/toptier_agencies/")

    async def test_returns_api_response(self, mock_usa_client, reference_mcp_client):
        """get_agencies returns the raw API response."""
        expected = {"results": [{"name": "DOD"}]}
        mock_usa_client.get.return_value = expected

        result = await reference_mcp_client.call_tool("get_agencies", {})
        data = result.data

        assert data == expected


class TestGetGlossary:
    """Tests for get_glossary tool."""

    async def test_calls_correct_endpoint(self, mock_usa_client, reference_mcp_client):
        """get_glossary calls /references/glossary/."""
        mock_usa_client.get.return_value = {"results": []}

        await reference_mcp_client.call_tool("get_glossary", {})

        mock_usa_client.get.assert_called_once_with("references/glossary/")

    async def test_returns_api_response(self, mock_usa_client, reference_mcp_client):
        """get_glossary returns the raw API response."""
        expected = {"results": [{"term": "obligation", "plain_text": "A binding agreement."}]}
        mock_usa_client.get.return_value = expected

        result = await reference_mcp_client.call_tool("get_glossary", {})
        data = result.data

        assert data == expected


class TestGetAwardTypes:
    """Tests for get_award_types tool."""

    async def test_calls_correct_endpoint(self, mock_usa_client, reference_mcp_client):
        """get_award_types calls /references/award_types/."""
        mock_usa_client.get.return_value = {"results": []}

        await reference_mcp_client.call_tool("get_award_types", {})

        mock_usa_client.get.assert_called_once_with("references/award_types/")
