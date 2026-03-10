import asyncio
import base64
import json
import logging
from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from usa_spending_mcp_server.client import USASpendingClient
from usa_spending_mcp_server.models.award_spending_models import AwardSearchRequest

logger = logging.getLogger(__name__)


def _encode_cursor(page: int) -> str:
    return base64.b64encode(json.dumps({"page": page}).encode()).decode()


def _decode_cursor(cursor: str) -> int:
    return json.loads(base64.b64decode(cursor.encode()))["page"]


def register_award_search_tools(mcp: FastMCP, client: USASpendingClient):
    """Register award search tools."""

    @mcp.tool()
    async def search_awards(
        award_search_request: AwardSearchRequest,
        cursor: Annotated[
            str | None,
            Field(
                description=(
                    "Opaque pagination cursor from a previous call's awards.next_cursor. "
                    "When provided, only fetches the next page of awards (skips aggregate calls)."
                )
            ),
        ] = None,
        include_time_trends: Annotated[
            bool,
            Field(
                description="Fetch spending_over_time trends (default: True). Set False to reduce latency."
            ),
        ] = True,
        include_geography: Annotated[
            bool,
            Field(description="Fetch state-level spending_by_geography breakdown (default: True)."),
        ] = True,
        include_categories: Annotated[
            bool,
            Field(
                description="Fetch awarding agency spending_by_category breakdown (default: True)."
            ),
        ] = True,
    ) -> Any:
        """
        Comprehensive award search mirroring the USASpending website's multi-API pattern.

        On the **first call** (no cursor), fetches award records AND aggregate data in parallel:
        - Individual award records (spending_by_award)
        - Award counts by type (spending_by_award_count)
        - Total transaction count + obligation sum (transaction_spending_summary)
        - Spending trends by fiscal year (spending_over_time) [if include_time_trends=True]
        - State-level geographic breakdown (spending_by_geography) [if include_geography=True]
        - Awarding agency breakdown (spending_by_category) [if include_categories=True]

        On **subsequent calls** (cursor provided), only fetches the next page of awards.
        Use awards.next_cursor from the previous response as the cursor argument.

        Args:
            award_search_request: Filters, fields, pagination, sort, subawards.
                - filters.time_period: List of {start_date, end_date} in YYYY-MM-DD
                - filters.award_type_codes: e.g. ["A","B","C","D"] for contracts
                - filters.agencies: List of agency objects
                - filters.recipient_search_text: e.g. ["Ernst & Young"]
                - filters.keywords: e.g. ["broadband", "cybersecurity"]
                - filters.award_amounts: e.g. [{lower_bound: 1000000}]
            cursor: Pagination cursor from previous response (awards.next_cursor).
            include_time_trends: Whether to fetch spending_over_time (default: True).
            include_geography: Whether to fetch spending_by_geography (default: True).
            include_categories: Whether to fetch spending_by_category (default: True).

        Returns:
            First call — dict with keys:
              awards: {results, page_metadata, next_cursor}
              summary: {award_counts_by_type, totals}
              trends: {group, results} or {error}
              geography: {scope, geo_layer, results} or {error}
              categories: {category, results} or {error}

            Subsequent calls (cursor provided) — dict with key:
              awards: {results, page_metadata, next_cursor}

        Examples:
            # Search HHS OIG contracts in FY2023
            search_awards(AwardSearchRequest(filters=AwardSearchFilters(
                agencies=[Agency(name="Office of the Inspector General",
                                 toptier_name="Department of Defense",
                                 type=AgencyType.AWARDING, tier=AgencyTier.TOPTIER)],
                award_type_codes=["A","B","C","D"],
                time_period=[TimePeriod(start_date="2022-10-01", end_date="2023-09-30")]
            )))

            # Get next page
            search_awards(previous_request, cursor=previous_response["awards"]["next_cursor"])

        Known API quirks:
            - recipient_search_text + agencies filters may not work together reliably.
              Workaround: use `keywords` instead, or search broadly and filter results.
            - award_type_codes must all be from the same group (contracts, grants, IDVs,
              loans, etc.). Mixing groups returns HTTP 422. Make separate calls per group.
            - transaction_spending_summary requires `keywords` in filters; the tool skips
              this call automatically when keywords are absent.
            - Award Amount in results is the *total award value*, not FY-specific obligations.
              For FY-specific obligation data, use get_award_details on individual awards.
        """
        filters_payload = award_search_request.model_dump(exclude_none=True)

        # --- Cursor path: only fetch next page of awards ---
        if cursor is not None:
            try:
                next_page = _decode_cursor(cursor)
            except Exception:
                return {"error": f"Invalid cursor: {cursor}"}

            paginated = award_search_request.model_copy(deep=True)
            paginated.pagination.page = next_page
            payload = paginated.model_dump(exclude_none=True)

            try:
                response = await client.post("search/spending_by_award/", payload)
            except Exception as e:
                return {"error": f"Error fetching awards page {next_page}: {e}"}

            page_meta = response.get("page_metadata", {})
            has_next = page_meta.get("hasNext", False)
            return {
                "awards": {
                    "results": response.get("results", []),
                    "page_metadata": page_meta,
                    "next_cursor": _encode_cursor(next_page + 1) if has_next else None,
                }
            }

        # --- First call: parallel fetch of awards + all aggregate data ---
        base_filters = award_search_request.filters.model_dump(exclude_none=True)

        async def fetch_awards():
            return await client.post("search/spending_by_award/", filters_payload)

        async def fetch_award_count():
            return await client.post("search/spending_by_award_count/", {"filters": base_filters})

        async def fetch_spending_summary():
            return await client.post(
                "search/transaction_spending_summary/", {"filters": base_filters}
            )

        async def fetch_over_time():
            return await client.post(
                "search/spending_over_time/",
                {"group": "fiscal_year", "filters": base_filters},
            )

        async def fetch_geography():
            return await client.post(
                "search/spending_by_geography/",
                {
                    "scope": "place_of_performance",
                    "geo_layer": "state",
                    "filters": base_filters,
                },
            )

        async def fetch_category():
            return await client.post(
                "search/spending_by_category/awarding_agency/",
                {"filters": base_filters},
            )

        # Build list of coroutines; supplementary ones are conditional
        supplementary_tasks = []
        task_keys = []

        supplementary_tasks.append(fetch_award_count())
        task_keys.append("award_count")

        has_keywords = bool(base_filters.get("keywords"))
        if has_keywords:
            supplementary_tasks.append(fetch_spending_summary())
            task_keys.append("spending_summary")

        # Always fetch spending_over_time — it provides obligation totals
        # even without keywords (unlike transaction_spending_summary)
        supplementary_tasks.append(fetch_over_time())
        task_keys.append("over_time")

        if include_geography:
            supplementary_tasks.append(fetch_geography())
            task_keys.append("geography")

        if include_categories:
            supplementary_tasks.append(fetch_category())
            task_keys.append("category")

        # Gather awards + all supplementary in parallel
        all_coros = [fetch_awards(), *supplementary_tasks]
        results = await asyncio.gather(*all_coros, return_exceptions=True)

        awards_result = results[0]
        supplementary_results = dict(zip(task_keys, results[1:], strict=False))

        # Handle primary awards failure
        if isinstance(awards_result, Exception):
            return {"error": f"Error fetching awards: {awards_result}"}

        page_meta = awards_result.get("page_metadata", {})
        has_next = page_meta.get("hasNext", False)

        awards_section = {
            "results": awards_result.get("results", []),
            "page_metadata": page_meta,
            "next_cursor": _encode_cursor(2) if has_next else None,
        }

        # Build summary (award_count + spending_summary)
        def _safe_result(key):
            r = supplementary_results.get(key)
            if isinstance(r, Exception):
                return None, str(r)
            return r, None

        count_data, count_err = _safe_result("award_count")
        summary_data, summary_err = _safe_result("spending_summary")
        over_time_data, over_time_err = _safe_result("over_time")

        summary_section: dict[str, Any] = {}
        if count_data is not None:
            summary_section["award_counts_by_type"] = count_data.get("results", count_data)
        elif count_err:
            summary_section["award_counts_error"] = count_err

        if summary_data is not None:
            summary_section["totals"] = summary_data.get("results", summary_data)
        elif summary_err:
            summary_section["totals_error"] = summary_err

        # Fallback: compute totals from spending_over_time when
        # transaction_spending_summary is unavailable (no keywords)
        if "totals" not in summary_section and over_time_data is not None:
            ot_results = over_time_data.get("results", [])
            total_obligations = sum(r.get("aggregated_amount", 0) for r in ot_results)
            summary_section["totals"] = {
                "prime_awards_obligation_amount": total_obligations,
                "source": "spending_over_time",
            }

        # Build trends section
        if include_time_trends:
            if over_time_data is not None:
                trends_section: dict[str, Any] = {
                    "group": over_time_data.get("group", "fiscal_year"),
                    "results": over_time_data.get("results", []),
                }
            else:
                trends_section = {"error": over_time_err}
        else:
            trends_section = {}

        # Build geography section
        geo_data, geo_err = _safe_result("geography")
        if include_geography:
            if geo_data is not None:
                geography_section: dict[str, Any] = {
                    "scope": "place_of_performance",
                    "geo_layer": "state",
                    "results": geo_data.get("results", []),
                }
            else:
                geography_section = {"error": geo_err}
        else:
            geography_section = {}

        # Build categories section
        cat_data, cat_err = _safe_result("category")
        if include_categories:
            if cat_data is not None:
                categories_section: dict[str, Any] = {
                    "category": "awarding_agency",
                    "results": cat_data.get("results", []),
                }
            else:
                categories_section = {"error": cat_err}
        else:
            categories_section = {}

        response_body: dict[str, Any] = {
            "awards": awards_section,
            "summary": summary_section,
        }
        if include_time_trends:
            response_body["trends"] = trends_section
        if include_geography:
            response_body["geography"] = geography_section
        if include_categories:
            response_body["categories"] = categories_section

        return response_body

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

        Fetches comprehensive award details including amounts, dates, recipients, agencies,
        and transaction history. Supports up to 10 awards per call, fetched in parallel.

        Args:
            award_ids: List of award IDs (found via search_awards generated_internal_id field).
                - Contracts start with: CONT_AWD_...
                - Grants vary by agency
            max_concurrent: Max parallel requests (default: 10, max: 10).

        Returns:
            Dict with:
            - success_count: Number of successfully fetched awards
            - error_count: Number of failed fetches
            - results: {award_id: award_detail_object}
            - errors: {award_id: error_message} (if any failures)

        Examples:
            get_award_details(award_ids=["CONT_AWD_W91ZRS23C0001_9700_-NONE-_-NONE-"])
        """
        try:
            max_concurrent = min(max_concurrent, 10, len(award_ids))
            semaphore = asyncio.Semaphore(max_concurrent)

            async def fetch_award(aid: str) -> dict[str, Any]:
                async with semaphore:
                    try:
                        data = await client.get(f"awards/{aid}/")
                        return {"award_id": aid, "success": True, "data": data}
                    except Exception as e:
                        return {"award_id": aid, "success": False, "error": str(e)}

            results = await asyncio.gather(*[fetch_award(aid) for aid in award_ids])

            success_results = {}
            error_results = {}
            for result in results:
                if result["success"]:
                    success_results[result["award_id"]] = result["data"]
                else:
                    error_results[result["award_id"]] = result["error"]

            response: dict[str, Any] = {
                "success_count": len(success_results),
                "error_count": len(error_results),
                "results": success_results,
            }
            if error_results:
                response["errors"] = error_results
            return response

        except Exception as e:
            return f"Error processing award details request: {str(e)}"
