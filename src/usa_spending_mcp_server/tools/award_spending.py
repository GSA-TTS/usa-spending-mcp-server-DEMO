import json
import logging
from datetime import date
from typing import Any

from fastmcp import FastMCP

from usa_spending_mcp_server.client import USASpendingClient

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def register_award_spending_tools(mcp: FastMCP, client: USASpendingClient):
    """Register geography spending tool"""

    @mcp.tool()
    async def fetch_agency_spending(agency_name: str, pagenum: int) -> Any:
        try:
            payload = {
                "filters": {
                    "award_type_codes": ["A", "B", "C", "D"],
                    "time_period": [
                        {"start_date": "2023-01-01", "end_date": str(date.today())}
                    ],
                },
                "limit": 100,
                "page": pagenum,
                "fields": [
                    "Award ID",
                    "Recipient Name",
                    "Start Date",
                    "End Date",
                    "Award Amount",
                    "Awarding Agency",
                    "Awarding Sub Agency",
                    "Contract Award Type",
                    "Award Type",
                    "Funding Agency",
                    "Funding Sub Agency",
                ],
            }

            response = await client.post("search/spending_by_award/", payload)
            return json.dumps(response, indent=2)
        except Exception as e:
            return f"Error searching spending by award: {str(e)}"
