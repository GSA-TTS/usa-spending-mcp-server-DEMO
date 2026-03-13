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

    async def test_no_search_term_returns_compact_index(
        self, mock_usa_client, reference_mcp_client
    ):
        """get_glossary without search_term returns compact term index."""
        mock_usa_client.get.return_value = {
            "results": [
                {"term": "obligation", "slug": "obligation", "plain_text": "A binding agreement."},
                {"term": "outlay", "slug": "outlay", "plain_text": "Money paid out."},
            ]
        }

        result = await reference_mcp_client.call_tool("get_glossary", {})
        data = result.data

        assert data["count"] == 2
        assert len(data["terms"]) == 2
        assert data["terms"][0]["term"] == "obligation"
        # Compact format should not include full definitions
        assert "plain_text" not in data["terms"][0]

    async def test_with_search_term_calls_autocomplete(self, mock_usa_client, reference_mcp_client):
        """get_glossary with search_term uses autocomplete endpoint."""
        # Real API returns strings in 'results' and full objects in 'matched_terms'
        autocomplete_response = {
            "results": ["Obligation"],
            "matched_terms": [
                {"term": "Obligation", "slug": "obligation", "plain": "A binding agreement."}
            ],
        }
        mock_usa_client.post.side_effect = None
        mock_usa_client.post.return_value = autocomplete_response

        result = await reference_mcp_client.call_tool("get_glossary", {"search_term": "obligation"})
        data = result.data

        mock_usa_client.post.assert_called_once_with(
            "autocomplete/glossary/", {"search_text": "obligation"}
        )
        # New format: results = list of term name strings; matched_terms = full objects
        assert data["results"][0] == "Obligation"
        assert data["matched_terms"][0]["term"] == "Obligation"
        assert data["count"] == 1


class TestGetAwardTypes:
    """Tests for get_award_types tool."""

    async def test_calls_correct_endpoint(self, mock_usa_client, reference_mcp_client):
        """get_award_types calls /references/award_types/."""
        mock_usa_client.get.return_value = {"results": []}

        await reference_mcp_client.call_tool("get_award_types", {})

        mock_usa_client.get.assert_called_once_with("references/award_types/")


class TestGetDefCodes:
    """Tests for get_def_codes tool."""

    async def test_calls_correct_endpoint(self, mock_usa_client, reference_mcp_client):
        """get_def_codes calls /references/def_codes/."""
        mock_usa_client.get.return_value = {"results": [{"code": "L", "title": "COVID-19"}]}

        result = await reference_mcp_client.call_tool("get_def_codes", {})
        data = result.data

        mock_usa_client.get.assert_called_once_with("references/def_codes/")
        assert data["results"][0]["code"] == "L"
