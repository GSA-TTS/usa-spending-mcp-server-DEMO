from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from usa_spending_mcp_server.client import USASpendingClient


def register_reference_tools(mcp: FastMCP, client: USASpendingClient):
    """Register reference/lookup tools"""

    @mcp.tool()
    async def get_agencies() -> Any:
        """
        Get US agencies and their IDs and codes.

        Use this when you want to get a list of all the US agencies and their metadata
        including agency IDs needed for other API calls.

        Returns:
            Raw API response data as JSON string containing agency information
        """
        try:
            response = await client.get("references/toptier_agencies/")
            return response
        except Exception as e:
            return f"Error fetching agencies: {str(e)}"

    @mcp.tool()
    async def get_award_types() -> Any:
        """
        Get all available award types and their codes.

        Use this to understand what award type codes (A, B, C, D, etc.) mean
        for filtering spending data.

        Returns:
            Raw API response data as JSON string containing award type information
        """
        try:
            response = await client.get("references/award_types/")
            return response
        except Exception as e:
            return f"Error fetching award types: {str(e)}"

    @mcp.tool()
    async def get_glossary(
        search_term: Annotated[
            str | None,
            Field(
                description=(
                    "Optional search term to filter glossary entries. "
                    "If provided, returns only matching terms with full definitions. "
                    "If omitted, returns a compact index of all term names."
                )
            ),
        ] = None,
    ) -> Any:
        """
        Get glossary terms to help understand and present analysis of data.

        When called without a search_term, returns a compact list of all available
        glossary term names (to avoid overwhelming context). Use a search_term to
        get full definitions for specific terms.

        Args:
            search_term: Optional text to search for in glossary terms.
                Examples: "obligation", "outlay", "award", "de-obligation",
                "prime award", "sub-award"

        Returns:
            If search_term provided: Matching glossary entries with full definitions.
            If no search_term: Compact list of all term names.

        Examples:
            get_glossary(search_term="obligation")
            get_glossary(search_term="prime award")
            get_glossary()  # returns term names only
        """

        def _glossary_variants(term: str) -> list[str]:
            """Return search variants to improve recall for hyphenated/compound terms."""
            variants = [term]
            # "subaward" → also try "sub-award"; "deobligation" → "de-obligation"
            no_hyphen = term.replace("-", "").replace(" ", "")
            if no_hyphen != term and no_hyphen not in variants:
                variants.append(no_hyphen)
            # Try inserting hyphens after common prefixes
            for prefix in ("sub", "de", "re", "pre", "co"):
                if term.startswith(prefix) and len(term) > len(prefix) and "-" not in term:
                    hyphenated = prefix + "-" + term[len(prefix) :]
                    if hyphenated not in variants:
                        variants.append(hyphenated)
            return variants

        async def _query_glossary(term: str) -> list[dict]:
            """Query autocomplete/glossary and return matched_terms list (full objects)."""
            try:
                resp = await client.post("autocomplete/glossary/", {"search_text": term})
                if not isinstance(resp, dict):
                    return []
                return resp.get("matched_terms", resp.get("results", []))
            except Exception:
                return []

        try:
            if search_term:
                # Collect all candidate query words (original + variants for each word)
                words = search_term.split()
                query_terms: list[str] = []
                for word in words:
                    for variant in _glossary_variants(word):
                        if variant not in query_terms:
                            query_terms.append(variant)

                all_results: list[dict] = []
                seen_slugs: set[str] = set()
                result_names: list[str] = []

                for term in query_terms:
                    entries = await _query_glossary(term)
                    for entry in entries:
                        slug = entry.get("slug", "")
                        if slug not in seen_slugs:
                            seen_slugs.add(slug)
                            all_results.append(entry)
                            result_names.append(entry.get("term", ""))

                return {
                    "search_text": search_term,
                    "results": result_names,
                    "count": len(all_results),
                    "matched_terms": all_results,
                }

            # Without search term, get full glossary but return compact index
            response = await client.get("references/glossary/")
            results = response.get("results", [])
            compact = [{"term": r.get("term", ""), "slug": r.get("slug", "")} for r in results]
            return {
                "count": len(compact),
                "terms": compact,
                "hint": "Use get_glossary(search_term='...') to get full definitions for specific terms.",
            }
        except Exception as e:
            return f"Error fetching glossary: {str(e)}"

    @mcp.tool()
    async def get_def_codes() -> Any:
        """
        Get Disaster Emergency Fund (DEF) Codes and their titles.

        Use this to understand DEFC codes for filtering disaster/emergency spending data.
        Common codes include 'L' (COVID-19), 'M' (COVID-19), 'N' (COVID-19),
        'O' (Infrastructure), etc.

        Returns:
            List of DEFC objects with code, public_law, title, and other metadata.
        """
        try:
            response = await client.get("references/def_codes/")
            return response
        except Exception as e:
            return f"Error fetching DEF codes: {str(e)}"

    @mcp.tool()
    async def get_data_dictionary() -> Any:
        """
        Get the USAspending data dictionary (Rosetta Crosswalk).

        Returns field definitions, data types, and mappings between
        different data sources used in USAspending.gov.

        Returns:
            JSON structure of the data dictionary.
        """
        try:
            response = await client.get("references/data_dictionary/")
            return response
        except Exception as e:
            return f"Error fetching data dictionary: {str(e)}"
