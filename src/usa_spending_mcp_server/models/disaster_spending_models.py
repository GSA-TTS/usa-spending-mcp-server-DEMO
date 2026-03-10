from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field

from usa_spending_mcp_server.models.common_models import AwardTypeCode


class DisasterSpendingType(StrEnum):
    """Spending type for disaster spending queries"""

    OBLIGATION = "obligation"
    OUTLAY = "outlay"
    FACE_VALUE_OF_LOAN = "face_value_of_loan"


class DisasterBaseFilters(BaseModel):
    """Base filters for disaster spending queries"""

    def_codes: Annotated[
        list[str],
        Field(
            description=(
                "List of Disaster Emergency Fund Codes (DEFC). "
                "Use get_def_codes() to see available codes. "
                "Common: 'L','M','N' (COVID-19), 'O' (Infrastructure), "
                "'P' (Inflation Reduction Act), 'V','W' (disaster relief)."
            )
        ),
    ]
    award_type_codes: Annotated[
        list[AwardTypeCode] | None,
        Field(description="Optional award type filter"),
    ] = None
    query: Annotated[
        str | None,
        Field(description="Optional text search within disaster awards"),
    ] = None
