from datetime import datetime
from enum import Enum
from typing import Annotated, Any

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

    name: str
    type: AgencyType = AgencyType.AWARDING
    tier: AgencyTier = AgencyTier.TOPTIER
    top_tier_name: str | None = None

    @classmethod
    def parse_agency_string(cls, agency_str: str) -> "Agency":
        """Parse single agency string in format 'type:tier:top_tier_name:name' or variations"""
        agency_str = agency_str.strip()

        if ":" not in agency_str:
            return cls(name=agency_str)

        parts = agency_str.split(":")
        if len(parts) == 2:
            # Must be type:name
            type_val, name = parts
            return cls(type=AgencyType(type_val), name=name)
        elif len(parts) == 3:
            tier, top_tier_name, name = parts
            return cls(tier=AgencyTier(tier), top_tier_name=top_tier_name, name=name)
        elif len(parts) == 4:
            type_val, tier, top_tier_name, name = parts
            return cls(
                type=AgencyType(type_val),
                tier=AgencyTier(tier),
                top_tier_name=top_tier_name,
                name=name,
            )
        else:
            return cls(name=agency_str)


class BaseSearchFilters(BaseModel):
    """Base filters for search requests"""

    time_period: list[TimePeriod]
    award_type_codes: list[AwardTypeCode] | None = None
    agencies: list[Agency] | None = None
    recipient_search_text: list[str] | None = None


class BasePagination(BaseModel):
    """Base pagination parameters"""

    page: Annotated[int, Field(default=1, ge=1, description="Page number")]
    limit: Annotated[int, Field(default=100, ge=1, le=100, description="Results per page")]
    order: SortOrder = SortOrder.DESC


class BaseSearchRequest(BaseModel):
    """Base search request with common parameters"""

    model_config = ConfigDict(extra="allow")
    subawards: bool = True
    pagination: BasePagination = Field(default_factory=lambda: BasePagination(page=1, limit=100))


class AgencyListParams(BaseModel):
    """Parameters for agency list requests"""

    fiscal_year: str | None = None
    sort: str | None = None
    page: str | None = "1"
    limit: str | None = "100"

    def to_params_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API params, excluding None values"""
        return {k: v for k, v in self.model_dump().items() if v is not None}
