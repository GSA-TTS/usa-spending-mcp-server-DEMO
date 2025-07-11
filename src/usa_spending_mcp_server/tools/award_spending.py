from typing import Any

from fastmcp import FastMCP

from usa_spending_mcp_server.client import USASpendingClient
from usa_spending_mcp_server.models.award_spending_models import AwardSearchRequest


def register_award_search_tools(mcp: FastMCP, client: USASpendingClient):
    """Register spending by award search tool"""

    @mcp.tool()
    async def search_spending_by_award(
        award_search_request: AwardSearchRequest,
        fetch_all_pages: bool = True,
        max_pages: int = 3,
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
                - fields: List of field names to include in response (default: basic award fields)
                - pagination: BasePagination with page, limit, order (asc/desc)
                - sort: Sort field name
                - subawards: Include subaward data (default: False)
            fetch_all_pages: Whether to fetch all available pages (default: True)
            max_pages: Maximum number of pages to fetch when fetch_all_pages=True (default: 3)

        Returns:
            Raw API response data as JSON string containing:
            - results: Array of award records
            - page_metadata: Pagination information including total_results_fetched
                and pages_fetched

        Examples:
            - Search DOD contracts over $1M in FY2024:
                AwardSearchRequest with filters containing
                    agencies=[Agency(name="Department of Defense")],
                award_amounts=[AwardAmount(lower_bound=1000000)],
                    time_period=[TimePeriod(start_date="2023-10-01", end_date="2024-09-30")]
            - Search by keywords:
                AwardSearchRequest with filters containing
                    keywords=["cybersecurity", "IT services"]
            - Search specific award IDs:
                AwardSearchRequest with filters containing
                    award_ids=["CONT_AWD_W91ZRS23C0001_9700_-NONE-_-NONE-"]
        """
        try:
            # Make initial API call
            response = await client.post(
                "search/spending_by_award/", award_search_request.model_dump(exclude_none=True)
            )

            # If not fetching all pages, return first page
            if not fetch_all_pages:
                return response

            # Initialize collection
            all_results = response.get("results", [])
            pages_fetched = 1
            current_page = award_search_request.pagination.page or 1

            # Get pagination metadata
            page_metadata = response.get("page_metadata", {})
            has_next = page_metadata.get("hasNext", False)
            total_pages = (
                page_metadata.get("total", 0) // award_search_request.pagination.limit + 1
            )

            # Calculate actual max pages to fetch
            max_pages_to_fetch = min(max_pages, total_pages) if total_pages > 0 else max_pages

            # Continue fetching while there are more pages and under limit
            while has_next and pages_fetched < max_pages_to_fetch:
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
                    print(f"Error fetching page {current_page}: {str(e)}")
                    break

            # Build final response with enhanced metadata
            final_response = response.copy()
            final_response["results"] = all_results
            final_response["page_metadata"].update(
                {
                    "total_results_fetched": len(all_results),
                    "pages_fetched": pages_fetched,
                    "requested_max_pages": max_pages,
                    "has_more_pages": has_next,
                    "fetch_completed": not has_next or pages_fetched >= max_pages_to_fetch,
                }
            )

            return final_response

        except Exception as e:
            return f"Error searching spending by award: {str(e)}"
