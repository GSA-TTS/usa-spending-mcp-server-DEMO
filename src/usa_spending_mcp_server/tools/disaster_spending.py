import asyncio
from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from usa_spending_mcp_server.client import USASpendingClient
from usa_spending_mcp_server.models.disaster_spending_models import (
    DisasterBaseFilters,
    DisasterSpendingType,
)


def register_disaster_spending_tools(mcp: FastMCP, client: USASpendingClient):
    """Register disaster/emergency spending tools."""

    @mcp.tool()
    async def get_disaster_overview() -> Any:
        """
        Get high-level overview of all disaster/emergency spending.

        Returns total funding and spending amounts for all Disaster Emergency Fund
        Codes (DEFC), including COVID-19, infrastructure, and other disaster relief.

        Returns:
            Dict with overview of disaster funding including totals by DEFC.
        """
        try:
            # disaster/overview/ is a POST endpoint requiring spending_type
            response = await client.post("disaster/overview/", {"spending_type": "obligation"})
            return response
        except Exception as e:
            return {"error": f"Error fetching disaster overview: {e}"}

    @mcp.tool()
    async def search_disaster_spending(
        filters: Annotated[
            DisasterBaseFilters,
            Field(description="Disaster spending filters (def_codes required)"),
        ],
        spending_type: Annotated[
            DisasterSpendingType,
            Field(description="Type of spending: 'obligation', 'outlay', or 'face_value_of_loan'"),
        ] = DisasterSpendingType.OBLIGATION,
    ) -> Any:
        """
        Get disaster/emergency spending by agency, with total award amounts.

        Fetches agency-level disaster spending AND total award amounts in parallel.
        Uses DEFC (Disaster Emergency Fund Codes) to filter specific emergency/disaster funds.

        Use get_def_codes() first to find the right DEFC codes.
        Common codes:
        - COVID-19: L, M, N
        - Infrastructure: O
        - Inflation Reduction Act: P
        - Disaster relief: V, W

        Args:
            filters: Disaster filters:
                - def_codes: REQUIRED. List of DEFC codes (e.g., ["L", "M", "N"])
                - award_type_codes: Optional award type filter
                - query: Optional text search
            spending_type: 'obligation' (default), 'outlay', or 'face_value_of_loan'

        Returns:
            Dict with:
            - agency_spending: Array of agencies with obligation/outlay amounts
            - award_totals: Aggregate award amounts (obligations and outlays)
            - award_count: Count of awards

        Examples:
            # COVID-19 spending by agency
            search_disaster_spending(
                filters=DisasterBaseFilters(def_codes=["L", "M", "N"])
            )

            # Infrastructure disaster grants only
            search_disaster_spending(
                filters=DisasterBaseFilters(
                    def_codes=["O"],
                    award_type_codes=["02","03","04","05"]
                )
            )
        """
        try:
            # The disaster/agency/spending/ endpoint only accepts
            # spending_type='total' or 'award', not 'obligation'/'outlay'.
            # Map accordingly: obligation→total, outlay→total, face_value_of_loan→total
            agency_spending_type = "total"
            if spending_type == DisasterSpendingType.FACE_VALUE_OF_LOAN:
                agency_spending_type = "award"

            payload = {
                "filter": filters.model_dump(exclude_none=True),
                "spending_type": agency_spending_type,
            }
            count_payload = {
                "filter": filters.model_dump(exclude_none=True),
            }

            async def fetch_agency_spending():
                return await client.post("disaster/agency/spending/", payload)

            async def fetch_award_amounts():
                return await client.post("disaster/award/amount/", count_payload)

            async def fetch_award_count():
                return await client.post("disaster/award/count/", count_payload)

            results = await asyncio.gather(
                fetch_agency_spending(),
                fetch_award_amounts(),
                fetch_award_count(),
                return_exceptions=True,
            )

            def _safe(r, label):
                if isinstance(r, Exception):
                    return {"error": f"Error fetching {label}: {r}"}
                return r

            return {
                "agency_spending": _safe(results[0], "agency spending"),
                "award_totals": _safe(results[1], "award totals"),
                "award_count": _safe(results[2], "award count"),
            }
        except Exception as e:
            return {"error": f"Error fetching disaster spending: {e}"}

    @mcp.tool()
    async def search_disaster_spending_by_geography(
        filters: Annotated[
            DisasterBaseFilters,
            Field(description="Disaster spending filters (def_codes required)"),
        ],
        geo_layer: Annotated[
            str,
            Field(description="Geographic layer: 'state', 'county', or 'district'"),
        ] = "state",
        spending_type: Annotated[
            DisasterSpendingType,
            Field(description="Type of spending: 'obligation', 'outlay', or 'face_value_of_loan'"),
        ] = DisasterSpendingType.OBLIGATION,
        scope: Annotated[
            str,
            Field(description="'place_of_performance' or 'recipient_location'"),
        ] = "recipient_location",
    ) -> Any:
        """
        Get disaster/emergency spending by geographic area.

        Returns state/county/district-level disaster spending data.

        Args:
            filters: Disaster filters (def_codes required)
            geo_layer: 'state', 'county', or 'district'
            spending_type: 'obligation' (default), 'outlay', or 'face_value_of_loan'
            scope: 'place_of_performance' or 'recipient_location'

        Returns:
            Geographic spending breakdown with state/county/district amounts.

        Examples:
            # COVID spending by state
            search_disaster_spending_by_geography(
                filters=DisasterBaseFilters(def_codes=["L", "M", "N"]),
                geo_layer="state"
            )
        """
        try:
            payload = {
                "filter": filters.model_dump(exclude_none=True),
                "geo_layer": geo_layer,
                "spending_type": spending_type.value,
                "scope": scope,
            }
            response = await client.post("disaster/spending_by_geography/", payload)
            return response
        except Exception as e:
            return {"error": f"Error fetching disaster spending by geography: {e}"}
