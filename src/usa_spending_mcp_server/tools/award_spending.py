import asyncio
from typing import Any

from fastmcp import FastMCP

from usa_spending_mcp_server.client import USASpendingClient
from usa_spending_mcp_server.models.award_spending_models import AwardSearchRequest


def register_award_search_tools(mcp: FastMCP, client: USASpendingClient):
    """Register spending by award search tool"""

    @mcp.tool()
    async def search_spending_by_award(
        award_type_codes: str,
        start_date: str = "2023-10-01",
        end_date: str = "2024-09-30",
        agencies: str | None = None,
        recipients: str | None = None,
        award_ids: str | None = None,
        keywords: str | None = None,
        award_amounts: str | None = None,
        program_activities: str | None = None,
        fields: str | None = None,
        subawards: str = "False",
        page: str = "1",
        limit: str = "100",
        sort: str | None = None,
        order: str = "desc",
        fetch_all_pages: str = "True",
        max_pages: str = "3",
    ) -> Any:
        """
        Search USA government spending data by award with filtering capabilities.

        Args:
            award_type_codes: Comma-separated award type codes (A, B, C, D, etc.)
            start_date: Start date in YYYY-MM-DD format (default: 2023-10-01)
            end_date: End date in YYYY-MM-DD format (default: 2024-09-30)
            agencies: Agency names to filter by. Format options:
                - Just name: "Department of Defense" (defaults to awarding:toptier)
                - type:name: "awarding:Department of Defense"
                - subtier:top_tier_name:name:
                    "awarding:subtier:Department of Defense:Office of Inspector General"
                - type:subtier:top_tier_name:name:
                    "awarding:subtier:Department of Defense:Office of Inspector General"
                - Multiple agencies:
                    "Department of Defense,Department of Health and Human Services"
            recipients: Comma-separated recipient names
            award_ids: Comma-separated award IDs
            keywords: Comma-separated keywords to search in award descriptions
            award_amounts: Semicolon-separated ranges in format "min-max" or "min-" or "-max"
                          Example: "1000-5000;10000-50000" or "100000-" or "-1000"
            program_activities: Semicolon-separated entries in the format "name|code".
                Examples:
                - "Information Technology|456"
                - "Education Grants|" (code optional)
                - "|123" (name optional)
                - Multiple: "Education|101;Health|202"
            fields: Comma-separated field names
            subawards: Whether to include subawards (default: False)
            page: Page number (default: 1)
            limit: Results per page (default: 100)
            sort: Sort field
            order: Sort order - asc or desc (default: desc)
            fetch_all_pages: Whether to fetch all available pages (default: True)
            max_pages: Maximum number of pages to fetch when fetch_all_pages=True (default: 3)

        Returns:
            Raw API response data as JSON string containing:
            - results: Array of award records
            - page_metadata: Pagination information
            - total_results_fetched: Total number of results when fetching all pages
            - pages_fetched: Number of pages fetched
        """

        try:
            request = AwardSearchRequest.from_params(
                award_type_codes=award_type_codes,
                start_date=start_date,
                end_date=end_date,
                agencies=agencies,
                recipients=recipients,
                award_ids=award_ids,
                keywords=keywords,
                award_amounts=award_amounts,
                program_activities=program_activities,
                fields=fields,
                subawards=subawards,
                page=page,
                limit=limit,
                sort=sort,
                order=order,
            )

            # Make initial API call
            response = await client.post("search/spending_by_award/", request.to_api_payload())

            # If not fetching all pages, return first page
            if fetch_all_pages.lower() != "true":
                return response

            # Collect all results across pages
            all_results = response.get("results", [])
            current_page = int(page)
            max_pages_int = int(max_pages)

            # Continue fetching while there are more pages
            while (
                response.get("page_metadata", {}).get("hasNext", False)
                and current_page < max_pages_int
            ):

                current_page += 1

                # Update request for next page
                next_request = AwardSearchRequest.from_params(
                    award_type_codes=award_type_codes,
                    start_date=start_date,
                    end_date=end_date,
                    agencies=agencies,
                    recipients=recipients,
                    award_ids=award_ids,
                    keywords=keywords,
                    award_amounts=award_amounts,
                    program_activities=program_activities,
                    fields=fields,
                    subawards=subawards,
                    page=str(current_page),
                    limit=limit,
                    sort=sort,
                    order=order,
                )

                # Fetch next page
                next_response = await client.post(
                    "search/spending_by_award/", next_request.to_api_payload()
                )

                # Append results
                all_results.extend(next_response.get("results", []))

                # Update response for next iteration
                response = next_response

            # Return combined response with all results
            final_response = response.copy()
            final_response["results"] = all_results
            final_response["page_metadata"]["total_results_fetched"] = len(all_results)
            final_response["page_metadata"]["pages_fetched"] = current_page

            return final_response

        except Exception as e:
            return f"Error searching spending by award: {str(e)}"

    @mcp.tool()
    async def get_award_details(
        award_id: str,
        max_concurrent: int = 10,
    ) -> Any:
        """
        Get detailed information about specific government award(s).

        This endpoint provides comprehensive details about one or more contracts, grants, loans,
        or other awards including amounts, dates, recipients, agencies, and transaction history.

        Args:
            award_id: Single award ID or comma-separated list of award IDs
                - Single: 'CONT_AWD_W91ZRS23C0001_9700_-NONE-_-NONE-'
                - Multiple: 'CONT_AWD_W91ZRS23C0001_9700_-NONE-_-NONE-,
                    CONT_AWD_W91ZRS23C0001_9702_-NONE-_-NONE-'
                - Contract IDs typically start with letters followed by numbers
                - Grant IDs vary by agency
                - Can be found using search_spending_by_award (generated_internal_id field) tool
                - Maximum 10 awards when using comma-separated list
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
                get_award_details(award_id='CONT_AWD_W91ZRS23C0001_9700_-NONE-_-NONE-')
            - Multiple contracts:
                get_award_details(award_id='CONT_AWD_W91ZRS23C0001_9700_-NONE-_-NONE-,
                    CONT_AWD_W91ZRS23C0001_9701_-NONE-_-NONE-')
            - Custom concurrency:
                get_award_details(award_id='CONT_AWD_W91ZRS23C0001_9700_-NONE-_-NONE-,
                    CONT_AWD_W91ZRS23C0001_9702_-NONE-_-NONE-', max_concurrent=5)
        """

        try:
            # Parse comma-separated award IDs
            award_ids = [aid.strip() for aid in award_id.split(",") if aid.strip()]

            if not award_ids:
                return "Error: No valid award IDs provided"

            # Handle single award ID - simple case
            if len(award_ids) == 1:
                try:
                    return await client.get(f"awards/{award_ids[0]}/")
                except Exception as e:
                    return f"Error getting award details for {award_ids[0]}: {str(e)}"

            # Handle multiple award IDs
            if len(award_ids) > 10:
                return "Error: Maximum 10 awards allowed per request"

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
