import json
import logging
from typing import Optional

from fastmcp import FastMCP

from usa_spending_mcp_server.client import USASpendingClient

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def register_spending_tools(mcp: FastMCP, client: USASpendingClient):
    """Register spending search tool"""

    @mcp.tool()
    async def search_spending(
        type: str,  # Required parameter
        agencies: Optional[str] = None,
        recipient_id: Optional[str] = None,
        federal_accounts: Optional[str] = None,
        object_class: Optional[str] = None,
        program_activities: Optional[str] = None,
        fiscal_year: str = "2024",
        period: Optional[str] = "12",
        quarter: Optional[str] = None,
    ) -> str:
        """
        Search USA government spending data with comprehensive filtering options.

        Args:
            type: Type of search data to return (required). Valid values:
                - 'federal_account': Federal account data
                - 'object_class': Object class data
                - 'recipient': Recipient data
                - 'award': Award data
                - 'budget_function': Budget function data
                - 'budget_subfunction': Budget subfunction data
                - 'agency': Agency data
                - 'program_activity': Program activity data
            agencies: Comma-separated list of agency names to filter by
            recipient_id: Specific recipient ID (DUNS, UEI, etc.)
            federal_accounts: Federal account codes to filter by
            object_class: Object class codes to filter by
            program_activities: Program activity codes to filter by
            fiscal_year: Fiscal year to filter by (default: '2024'). Format: YYYY
            period: Fiscal period to filter by (1-12, default: '12'). Required if quarter not provided.
            quarter: Fiscal quarter to filter by (1-4). Alternative to period parameter.

        Returns:
            Raw API response data as JSON string
        """

        try:
            # Validate type parameter
            valid_types = [
                "federal_account",
                "object_class",
                "recipient",
                "award",
                "budget_function",
                "budget_subfunction",
                "agency",
                "program_activity",
            ]
            if type not in valid_types:
                return f"Error: Invalid type '{type}'. Must be one of: {', '.join(valid_types)}"

            # Validate period/quarter parameters
            if period and quarter:
                return "Error: Cannot specify both 'period' and 'quarter' parameters. Choose one."

            # Default to quarter 4 if neither period nor quarter is specified
            if not period and not quarter:
                quarter = "4"

            if period and period not in [
                "1",
                "2",
                "3",
                "4",
                "5",
                "6",
                "7",
                "8",
                "9",
                "10",
                "11",
                "12",
            ]:
                return f"Error: Invalid period '{period}'. Must be 1-12."

            if quarter and quarter not in ["1", "2", "3", "4"]:
                return f"Error: Invalid quarter '{quarter}'. Must be 1-4."

            # Build the request payload according to API documentation
            payload = {
                "type": type,
                "filters": {
                    "fy": fiscal_year,
                },
            }

            # Add period or quarter to filters (required by API)
            if period:
                payload["filters"]["period"] = period
            elif quarter:
                payload["filters"]["quarter"] = quarter

            # Add optional filters based on provided parameters
            if agencies:
                payload["filters"]["agency"] = agencies.strip()

            if federal_accounts:
                payload["filters"]["federal_account"] = federal_accounts.strip()

            if object_class:
                payload["filters"]["object_class"] = object_class.strip()

            if recipient_id:
                payload["filters"]["recipient"] = recipient_id.strip()

            if program_activities:
                payload["filters"]["program_activity"] = program_activities.strip()

            # Make API call
            response = await client.post("spending/", payload)

            # Return raw API response
            return json.dumps(response, indent=2)

        except Exception as e:
            return f"Error searching spending data: {str(e)}"
