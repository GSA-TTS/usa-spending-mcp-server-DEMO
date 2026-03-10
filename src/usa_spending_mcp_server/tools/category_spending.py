from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from usa_spending_mcp_server.client import USASpendingClient
from usa_spending_mcp_server.models.category_spending_models import (
    CategorySearchFilters,
    SpendingCategory,
)


def register_category_spending_tools(mcp: FastMCP, client: USASpendingClient):
    """Register spending by category tools."""

    @mcp.tool()
    async def search_spending_by_category(
        category: Annotated[
            SpendingCategory,
            Field(
                description=(
                    "Category to aggregate spending by. Options: "
                    "'recipient' (top recipients), "
                    "'awarding_agency', 'awarding_subagency', "
                    "'funding_agency', 'funding_subagency', "
                    "'cfda' (assistance listings), 'naics' (industry codes), "
                    "'psc' (product/service codes), "
                    "'state_territory', 'county', 'district', 'country', "
                    "'federal_account', 'recipient_duns', 'defc' (disaster codes)"
                )
            ),
        ],
        filters: Annotated[
            CategorySearchFilters,
            Field(description="Search filters (time_period required, others optional)"),
        ],
        limit: Annotated[
            int,
            Field(description="Number of results to return (default: 10, max: 100)"),
        ] = 10,
        page: Annotated[
            int,
            Field(description="Page number (default: 1)"),
        ] = 1,
        subawards: Annotated[
            bool,
            Field(description="If True, aggregate subaward spending instead of prime awards"),
        ] = False,
    ) -> Any:
        """
        Get spending aggregated by category — one of the most powerful analysis tools.

        Returns the top N entries for a given category (recipients, agencies, states, etc.)
        with their total spending amounts. Supports all standard search filters.

        Use this for:
        - "Who are the top recipients in California?" → category=recipient + recipient_locations
        - "Which agencies fund the most grants?" → category=awarding_agency + award_type_codes
        - "Top NAICS codes for DOD contracts?" → category=naics + agencies + award_type_codes
        - "Spending by state for HHS?" → category=state_territory + agencies
        - "Top CFDA programs for disaster spending?" → category=cfda + keywords
        - "Which congressional districts get the most HHS funding?" → category=district + agencies
        - "Top recipients of broadband funding?" → category=recipient + keywords

        Args:
            category: Category to group by (recipient, awarding_agency, state_territory, etc.)
            filters: Search filters:
                - time_period: REQUIRED. List of {start_date, end_date}
                - award_type_codes: Filter by type (contracts, grants, etc.)
                - agencies: Filter by awarding/funding agency
                - keywords: Search in award descriptions
                - recipient_search_text: Filter by recipient name
                - recipient_type_names: e.g. ['nonprofit', 'category_business']
                - place_of_performance_locations: Filter by work location
                - recipient_locations: Filter by recipient location
            limit: Number of results (default: 10, max: 100)
            page: Page number for pagination
            subawards: Aggregate subaward spending instead of prime awards

        Returns:
            Dict with:
            - category: The category used
            - results: Array of {name, code, id, amount} entries, sorted by amount desc
            - page_metadata: Pagination info

        Examples:
            # Top 10 recipients in Texas for HHS grants
            search_spending_by_category(
                category="recipient",
                filters=CategorySearchFilters(
                    time_period=[TimePeriod(start_date="2022-10-01", end_date="2023-09-30")],
                    agencies=[Agency(name="Department of Health and Human Services")],
                    award_type_codes=["02","03","04","05"],
                    recipient_locations=[LocationFilter(country="USA", state="TX")]
                ),
                limit=10
            )

            # Top agencies by contract spending
            search_spending_by_category(
                category="awarding_agency",
                filters=CategorySearchFilters(
                    time_period=[TimePeriod(start_date="2022-10-01", end_date="2023-09-30")],
                    award_type_codes=["A","B","C","D"]
                ),
                limit=20
            )
        """
        try:
            endpoint = f"search/spending_by_category/{category.value}/"
            payload = {
                "filters": filters.model_dump(exclude_none=True),
                "limit": limit,
                "page": page,
                "subawards": subawards,
            }
            response = await client.post(endpoint, payload)
            return {
                "category": category.value,
                "results": response.get("results", []),
                "page_metadata": response.get("page_metadata", {}),
            }
        except Exception as e:
            return {"error": f"Error fetching spending by category: {e}"}
