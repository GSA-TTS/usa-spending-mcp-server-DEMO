from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field
from pydantic.functional_validators import field_validator, model_validator


class AwardTypeCode(str, Enum):
    """Award type codes for filtering"""

    BPA_CALL = "A"
    PURCHASE_ORDER = "B"
    DELIVERY_ORDER = "C"
    DEFINITIVE_CONTRACT = "D"
    GRANT_02 = "02"
    GRANT_03 = "03"
    GRANT_04 = "04"
    GRANT_05 = "05"
    DIRECT_PAYMENT_06 = "06"
    DIRECT_PAYMENT_10 = "10"
    LOAN_07 = "07"
    LOAN_08 = "08"
    OTHER_09 = "09"
    OTHER_11 = "11"
    OTHER_NEG1 = "-1"
    IDV = "IDV"


class AgencyTier(str, Enum):
    """Agency tier types"""

    TOPTIER = "toptier"
    SUBTIER = "subtier"


class AgencyType(str, Enum):
    """Agency types for filtering"""

    AWARDING = "awarding"
    FUNDING = "funding"


class SortOrder(str, Enum):
    """Sort order options"""

    ASC = "asc"
    DESC = "desc"


class TimePeriod(BaseModel):
    """Time period filter"""

    start_date: Annotated[str, Field(description="Start date in YYYY-MM-DD format")]
    end_date: Annotated[str, Field(description="End date in YYYY-MM-DD format")]

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_format(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")

    @model_validator(mode="after")
    def validate_date_range(self):
        start_dt = datetime.strptime(self.start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(self.end_date, "%Y-%m-%d")
        if start_dt > end_dt:
            raise ValueError("start_date must be before end_date")
        return self


class Agency(BaseModel):
    """Individual agency filter model"""

    name: Annotated[
        str,
        Field(
            description="Agency name, ex: 'Department of Defense' or Office of the Inspector General"
        ),
    ]
    type: Annotated[AgencyType, Field(default=AgencyType.AWARDING)] = AgencyType.AWARDING
    tier: Annotated[AgencyTier, Field(default=AgencyTier.TOPTIER)] = AgencyTier.TOPTIER
    toptier_name: Annotated[
        str | None, Field(description="Top tier agency name, ex: 'Department of Defense'")
    ] = None


class BaseSearchFilters(BaseModel):
    """Base filters for search requests"""

    time_period: Annotated[
        list[TimePeriod], Field(description="List of time periods for the search")
    ]
    award_type_codes: Annotated[
        list[AwardTypeCode] | None, Field(description="List of award type codes")
    ] = None
    agencies: Annotated[list[Agency] | None, Field(description="List of agencies")] = None
    recipient_search_text: Annotated[
        list[str] | None, Field(description="Recipient search text, ex: ['Amazon']")
    ] = None
    recipient_type_names: Annotated[
        list[str] | None,
        Field(
            description="Recipient type names, ex: ['category_business', 'sole_proprietorship', 'nonprofit', 'community_development_corporations']"
        ),
    ] = None


class BasePagination(BaseModel):
    """Base pagination parameters"""

    page: Annotated[int, Field(default=1, ge=1, description="Page number")]
    limit: Annotated[int, Field(default=100, ge=1, le=100, description="Results per page")]
    order: SortOrder = SortOrder.DESC


class BaseSearchRequest(BaseModel):
    """Base search request with common parameters"""

    model_config = ConfigDict(extra="allow")
    subawards: Annotated[
        bool, Field(default=False, description="Include subawards in the search")
    ] = False
    pagination: Annotated[BasePagination, Field(description="Pagination")] = BasePagination(
        page=1, limit=100
    )


class AgencyListParams(BaseModel):
    """Parameters for agency list requests"""

    fiscal_year: Annotated[int | None, Field(description="Fiscal year, ex: 2022")] = None
    sort: Annotated[
        str | None, Field(description="Value to sort on, default to 'total_obligations'")
    ] = None
    page: Annotated[int | None, Field(description="Page number")] = 1
    limit: Annotated[int | None, Field(description="Results per page")] = 100
