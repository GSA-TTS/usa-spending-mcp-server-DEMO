from typing import Annotated

from pydantic import BaseModel, Field

from usa_spending_mcp_server.models.common_models import (
    BaseSearchFilters,
    BaseSearchRequest,
)


class AwardDetailsRequest(BaseModel):
    """Award details request model for single or multiple awards"""

    award_ids: Annotated[list[str], Field(description="List of award IDs")] = []
    max_concurrent: Annotated[
        int, Field(default=10, description="Maximum number of concurrent requests")
    ] = 10


class AwardAmount(BaseModel):
    """Award amount range filter"""

    lower_bound: Annotated[float | None, Field(description="Lower bound of the award amount")] = (
        None
    )
    upper_bound: Annotated[float | None, Field(description="Upper bound of the award amount")] = (
        None
    )


class ProgramActivityObject(BaseModel):
    name: Annotated[str | None, Field(description="Program activity name")] = None
    code: Annotated[str | None, Field(description="Program activity code")] = None


class AwardSearchFilters(BaseSearchFilters):
    """Filters specific to award search"""

    award_ids: Annotated[list[str] | None, Field(description="List of award IDs")] = None
    keywords: Annotated[
        list[str] | None, Field(description="List of keywords to search in award descriptions")
    ] = None
    award_amounts: Annotated[
        list[AwardAmount] | None, Field(description="List of award amount ranges")
    ] = None
    program_activities: Annotated[
        list[ProgramActivityObject] | None, Field(description="List of program activities")
    ] = None


class AwardSearchRequest(BaseSearchRequest):
    """Award search request model"""

    filters: Annotated[AwardSearchFilters, Field(description="Filters for the award search")]
    fields: Annotated[
        list[str], Field(description="List of fields to include in the response")
    ] = [
        "Award ID",
        "Recipient Name",
        "Start Date",
        "End Date",
        "Award Amount",
        "Awarding Agency",
        "Awarding Sub Agency",
        "Award Type",
    ]
    sort: Annotated[str | None, Field(description="Sort order for the award search")] = None
    subawards: Annotated[
        bool, Field(default=False, description="Include subawards in the search")
    ] = False
