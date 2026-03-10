import base64
import json
from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from usa_spending_mcp_server.client import USASpendingClient
from usa_spending_mcp_server.models.recipient_models import RecipientSearchRequest


def _encode_cursor(page: int) -> str:
    return base64.b64encode(json.dumps({"page": page}).encode()).decode()


def _decode_cursor(cursor: str) -> int:
    return json.loads(base64.b64decode(cursor.encode()))["page"]


def register_recipient_search_tools(mcp: FastMCP, client: USASpendingClient):
    """Register recipient search tool"""

    @mcp.tool()
    async def search_recipients(
        recipient_search_request: RecipientSearchRequest,
        cursor: Annotated[
            str | None,
            Field(
                description=(
                    "Opaque pagination cursor from a previous call's next_cursor. "
                    "When provided, fetches the indicated page."
                )
            ),
        ] = None,
    ) -> Any:
        """
        Search for government spending recipients (contractors, grantees, etc) in the
        last 12 months.

        Returns a list of recipients with their spending amounts, UEI identifiers, and
        recipient levels. Supports cursor-based pagination via next_cursor.

        Args:
            recipient_search_request: RecipientSearchRequest object containing:
                - keyword: Optional search term to filter by recipient name, UEI, or DUNS
                - award_type: Filter by award type (default: 'all')
                    - 'all', 'contracts', 'grants', 'loans', 'direct_payments',
                      'other_financial_assistance'
                - sort: Field to sort results by — 'amount' (default), 'name', 'duns'
                - order: 'desc' (default) or 'asc'
                - pagination: BasePagination with page, limit (max 100)
            cursor: Opaque pagination cursor from previous response's next_cursor.

        Returns:
            Dict with:
            - results: Array of recipients with id, name, duns, uei, recipient_level, amount
            - page_metadata: Pagination information
            - next_cursor: Cursor string for next page, or null if exhausted

        Examples:
            - Find top contractors:
                search_recipients(RecipientSearchRequest(award_type='contracts'))
            - Search by name with pagination:
                search_recipients(RecipientSearchRequest(keyword='Boeing'))
                # then: search_recipients(RecipientSearchRequest(keyword='Boeing'),
                #                         cursor=previous_response["next_cursor"])
        """
        try:
            payload = recipient_search_request.model_dump(exclude_none=True)

            if cursor is not None:
                try:
                    page = _decode_cursor(cursor)
                except Exception:
                    return {"error": f"Invalid cursor: {cursor}"}
                payload["page"] = page

            response = await client.post("recipient/", payload)

            page_meta = response.get("page_metadata", {})
            has_next = page_meta.get("hasNext", False)
            current_page = page_meta.get("page", 1)

            return {
                "results": response.get("results", []),
                "page_metadata": page_meta,
                "next_cursor": _encode_cursor(current_page + 1) if has_next else None,
            }

        except Exception as e:
            return f"Error searching recipients: {str(e)}"
