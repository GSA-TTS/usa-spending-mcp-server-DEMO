from datetime import date
from typing import Any

import httpx
import mcp.types as mcp_types
from mcp.server.fastmcp import FastMCP
from mcp.shared.exceptions import McpError

from usa_spending_mcp_server.utils import async_http_post

USA_SPENDING_API_BASE_ENDPOINT = "https://api.usaspending.gov/api/v2/"

mcp = FastMCP("Demo")


@mcp.tool()
async def fetch_agency_spending(agency_name: str) -> Any:
    endoint = f"{USA_SPENDING_API_BASE_ENDPOINT}search/spending_by_award/"
    payload = {
        "filters": {
            "award_type_codes": ["A", "B", "C", "D"],
            "time_period": {
                "start_date": "2022-01-01",
                "end_date": str(date.today()),
            },
        },
        "limit": 100,
        "field": [
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
    try:
        response = await async_http_post(endoint, json=payload)
        return response.json()
    except httpx.HTTPStatusError as e:
        raise McpError(
            mcp_types.ErrorData(
                code=mcp_types.INTERNAL_ERROR,
                message=f"Received {e.response.status_code} from {e.request.url}",
            )
        )
    except httpx.RequestError as e:
        raise McpError(
            mcp_types.ErrorData(
                code=mcp_types.INTERNAL_ERROR,
                message=f"Received {e} while requesting {e.request.url}.",
            )
        )


def main():
    """Main entry point for the application."""
    mcp.run()


if __name__ == "__main__":
    main()
