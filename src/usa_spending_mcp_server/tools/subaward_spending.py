from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from usa_spending_mcp_server.client import USASpendingClient


def register_subaward_tools(mcp: FastMCP, client: USASpendingClient):
    """Register subaward search tools."""

    @mcp.tool()
    async def search_subawards(
        award_id: Annotated[
            str | None,
            Field(
                description=(
                    "Optional prime award ID to get subawards for. "
                    "If omitted, returns subawards across all awards."
                )
            ),
        ] = None,
        page: Annotated[int, Field(description="Page number (default: 1)")] = 1,
        limit: Annotated[int, Field(description="Results per page (default: 100, max: 100)")] = 100,
        sort: Annotated[
            str,
            Field(description="Sort field: 'subaward_number', 'amount', 'action_date'"),
        ] = "amount",
        order: Annotated[str, Field(description="'asc' or 'desc'")] = "desc",
    ) -> Any:
        """
        Search for subawards (downstream distributions from prime awards).

        Returns individual subaward records with amounts, recipients, and dates.
        Can be filtered to a specific prime award or searched across all awards.

        A prime award is money from the federal government directly to a recipient.
        A subaward is when that recipient passes funds downstream to sub-recipients.

        DATA QUALITY WARNING: When sorting by amount descending, top results may contain
        astronomically wrong values (e.g., $1 quadrillion) due to data entry errors in the
        source USAspending.gov database. Results with amounts > $1 trillion are flagged
        with a data_quality_warning field. Filter by a specific prime award for reliable data.

        Args:
            award_id: Optional prime award ID to filter by
            page: Page number
            limit: Results per page (max 100)
            sort: Sort field
            order: 'asc' or 'desc'

        Returns:
            Dict with:
            - results: Array of subaward records
            - page_metadata: Pagination info

        Examples:
            # Get all subawards for a specific prime award
            search_subawards(award_id="CONT_AWD_W91ZRS23C0001_9700_-NONE-_-NONE-")

            # Browse top subawards by amount
            search_subawards(sort="amount", order="desc", limit=20)
        """
        try:
            payload = {
                "page": page,
                "limit": limit,
                "sort": sort,
                "order": order,
            }
            if award_id:
                payload["award_id"] = award_id

            response = await client.post("subawards/", payload)

            # Flag data quality issues: subawards > $1T are almost certainly errors
            outlier_threshold = 1_000_000_000_000  # $1 trillion
            results = response.get("results", [])
            outlier_count = 0
            for record in results:
                amt = record.get("amount")
                if amt is not None and abs(amt) > outlier_threshold:
                    record["data_quality_warning"] = (
                        "Amount exceeds $1T — likely a data entry error in USAspending.gov"
                    )
                    outlier_count += 1

            if outlier_count > 0:
                response["data_quality_note"] = (
                    f"{outlier_count} result(s) flagged with amounts > $1T. "
                    "These are known data entry errors in the source database. "
                    "Filter by a specific prime award_id for reliable subaward data."
                )

            return response
        except Exception as e:
            return {"error": f"Error searching subawards: {e}"}

    @mcp.tool()
    async def search_subaward_totals(
        filters: Annotated[
            dict,
            Field(
                description=(
                    "Filters dict with: time_period, award_type_codes, agencies, keywords, etc. "
                    "Same format as search_awards filters."
                )
            ),
        ],
        limit: Annotated[int, Field(description="Number of results (default: 10)")] = 10,
        page: Annotated[int, Field(description="Page number (default: 1)")] = 1,
    ) -> Any:
        """
        Get subaward obligation totals grouped by prime award.

        Returns the total subaward amount and count for each prime award.
        Useful for understanding what fraction of prime awards flows to sub-recipients.

        Args:
            filters: Standard search filters (same as search_awards)
            limit: Number of results
            page: Page number

        Returns:
            Array of entries with prime award ID, subaward count, and total subaward amount.
        """
        try:
            payload = {
                "filters": filters,
                "limit": limit,
                "page": page,
            }
            response = await client.post("search/spending_by_subaward_grouped/", payload)
            return response
        except Exception as e:
            return {"error": f"Error fetching subaward totals: {e}"}
