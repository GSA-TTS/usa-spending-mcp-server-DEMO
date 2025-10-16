import asyncio
import logging
from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from usa_spending_mcp_server.client import USASpendingClient
from usa_spending_mcp_server.models.award_spending_models import AwardSearchRequest

logger = logging.getLogger(__name__)


def register_award_search_tools(mcp: FastMCP, client: USASpendingClient):
    """Register spending by award search tool"""

    @mcp.tool()
    async def search_spending_by_award(
        award_search_request: AwardSearchRequest,
        pages_to_fetch: int = 3,
    ) -> Any:
        """
        Search USA government spending data by award with filtering capabilities.

        Args:
            award_search_request: Structured request object containing:
                - filters: AwardSearchFilters with optional fields:
                    - time_period: List of TimePeriod objects with start_date and end_date
                        (YYYY-MM-DD)
                    - award_type_codes: List of award type codes (A, B, C, D, etc.)
                    - agencies: List of Agency objects with name, type (awarding/funding), tier
                         (toptier/subtier)
                    - recipient_search_text: List of recipient names to search for
                    - award_ids: List of specific award IDs to filter by
                    - keywords: List of keywords to search in award descriptions
                    - award_amounts: List of AwardAmount objects with lower_bound/upper_bound
                    - program_activities: List of ProgramActivityObject with name/code
                    - recipient_type_names: List of recipient type names to filter by
                        (e.g., 'category_business', 'sole_proprietorship', 'nonprofit',
                        'community_development_corporations', 'tribally_owned_firm')
                - fields: List of field names to include in response (default: basic award fields)
                - pagination: BasePagination with page, limit, order (asc/desc)
                - sort: Sort field name
                - subawards: Include subaward data (default: False)
            pages_to_fetch: Maximum number of pages to fetch (default: 3)

        Returns:
            Raw API response data as JSON string containing:
            - results: Array of award records
            - page_metadata: Pagination information including total_results_fetched
                and pages_fetched

        Examples:
            - Search DOD OIG contracts over $1M in FY2024:
                AwardSearchRequest with filters containing
                    agencies=[
                        Agency(
                            name="Office of the Inspector General",
                            toptier_name="Department of Defense",
                            type=AgencyType.AWARDING,
                            tier=AgencyTier.TOPTIER
                        )
                    ],
                award_amounts=[AwardAmount(lower_bound=1000000)],
                    time_period=[TimePeriod(start_date="2023-10-01", end_date="2024-09-30")]
            - Search by keywords:
                AwardSearchRequest with filters containing
                    keywords=["cybersecurity", "IT services"]
            - Search specific award IDs:
                AwardSearchRequest with filters containing
                    award_ids=["CONT_AWD_W91ZRS23C0001_9700_-NONE-_-NONE-"]
            - Search for nonprofit grant recipients:
                AwardSearchRequest with filters containing
                    award_type_codes=["02", "03", "04", "05"],
                    recipient_type_names=["nonprofit"],
                    time_period=[TimePeriod(start_date="2024-01-01", end_date="2024-12-31")]
        """

        try:
            # Make initial API call
            response = await client.post(
                "search/spending_by_award/", award_search_request.model_dump(exclude_none=True)
            )
            logger.info(response)

            # If not fetching all pages, return first page
            if pages_to_fetch <= 1:
                return response

            # Initialize collection
            all_results = response.get("results", [])
            pages_fetched = 1
            current_page = award_search_request.pagination.page or 1

            # Get pagination metadata
            page_metadata = response.get("page_metadata", {})
            has_next = page_metadata.get("hasNext", False)
            logger.info("Page metadata: %s", page_metadata)
            logger.info(f"Has next page: {has_next}")

            # Continue fetching while there are more pages and under limit
            while has_next and pages_fetched < pages_to_fetch:
                current_page += 1
                pages_fetched += 1

                # Create next page request (shallow copy is sufficient)
                next_request = award_search_request.model_copy()
                next_request.pagination.page = current_page

                try:
                    # Fetch next page
                    next_response = await client.post(
                        "search/spending_by_award/", next_request.model_dump(exclude_none=True)
                    )

                    # Append results
                    page_results = next_response.get("results", [])
                    all_results.extend(page_results)

                    # Update pagination info
                    page_metadata = next_response.get("page_metadata", {})
                    has_next = page_metadata.get("hasNext", False)

                    # Break if no results on this page
                    if not page_results:
                        break

                except Exception as e:
                    # Log error but don't fail completely - return what we have
                    logger.error(f"Error fetching page {current_page}: {str(e)}")
                    break

            # Build final response with enhanced metadata
            final_response = response.copy()
            final_response["results"] = all_results
            final_response["page_metadata"].update(
                {
                    "total_results_fetched": len(all_results),
                    "pages_fetched": pages_fetched,
                    "requested_max_pages": pages_to_fetch,
                    "has_more_pages": has_next,
                    "fetch_completed": not has_next or pages_fetched >= pages_to_fetch,
                }
            )

            return final_response

        except Exception as e:
            return f"Error searching spending by award: {str(e)}"

    @mcp.tool()
    async def get_award_details(
        award_ids: Annotated[
            list[str], Field(description="List of award IDs", min_length=1, max_length=10)
        ],
        max_concurrent: Annotated[
            int, Field(default=10, description="Maximum number of concurrent requests")
        ] = 10,
    ) -> Any:
        """
        Get detailed information about specific government award(s).

        This endpoint provides comprehensive details about one or more contracts, grants, loans,
        or other awards including amounts, dates, recipients, agencies, and transaction history.

        Args:
            award_ids: List of award IDs
                - Single: ['CONT_AWD_W91ZRS23C0001_9700_-NONE-_-NONE-']
                - Multiple: ['CONT_AWD_W91ZRS23C0001_9700_-NONE-_-NONE-',
                    'CONT_AWD_W91ZRS23C0001_9702_-NONE-_-NONE-']
                - Contract IDs typically start with letters followed by numbers
                - Grant IDs vary by agency
                - Can be found using search_spending_by_award (generated_internal_id field) tool
            max_concurrent: Maximum number of concurrent requests (default: 10, max: 10)

        Returns:
            Raw API response data as JSON string containing:
            - For single award: Award details object
            - For multiple awards: Dictionary with award_id as key and details as value
            - Award overview (total obligation, dates, type)
            - Recipient details (name, address, DUNS/UEI)
            - Agency information (awarding and funding agencies)
            - Place of performance
            - Transaction history
            - Contract details (if applicable)
            - Federal account funding
            - Executive compensation (if disclosed)

        Examples:
            - Single contract:
                get_award_details(award_ids=['CONT_AWD_W91ZRS23C0001_9700_-NONE-_-NONE-'])
            - Multiple contracts:
                get_award_details(award_ids=['CONT_AWD_W91ZRS23C0001_9700_-NONE-_-NONE-,
                    CONT_AWD_W91ZRS23C0001_9701_-NONE-_-NONE-'])
        """

        try:
            if not award_ids:
                return "Error: No valid award IDs provided"

            # Limit concurrent requests
            max_concurrent = min(max_concurrent, 10, len(award_ids))
            semaphore = asyncio.Semaphore(max_concurrent)

            # Simple parallel fetch function
            async def fetch_award(aid: str) -> dict[str, Any]:
                async with semaphore:
                    try:
                        data = await client.get(f"awards/{aid}/")
                        return {"award_id": aid, "success": True, "data": data}
                    except Exception as e:
                        return {"award_id": aid, "success": False, "error": str(e)}

            # Execute all requests concurrently
            results = await asyncio.gather(*[fetch_award(aid) for aid in award_ids])

            # Build response
            success_results = {}
            error_results = {}

            for result in results:
                if result["success"]:
                    success_results[result["award_id"]] = result["data"]
                else:
                    error_results[result["award_id"]] = result["error"]

            response = {
                "success_count": len(success_results),
                "error_count": len(error_results),
                "results": success_results,
            }

            if error_results:
                response["errors"] = error_results

            return response

        except Exception as e:
            return f"Error processing award details request: {str(e)}"
