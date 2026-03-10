from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field
from pydantic.functional_validators import field_validator, model_validator


class AwardTypeCode(StrEnum):
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
    IDV_A = "IDV_A"  # GWAC
    IDV_B = "IDV_B"  # IDC Multi-Agency Contract
    IDV_B_A = "IDV_B_A"  # IDC / Requirements
    IDV_B_B = "IDV_B_B"  # IDC / Indefinite Quantity
    IDV_B_C = "IDV_B_C"  # IDC / Definite Quantity
    IDV_C = "IDV_C"  # FSS Federal Supply Schedule
    IDV_D = "IDV_D"  # BOA Basic Ordering Agreement
    IDV_E = "IDV_E"  # BPA Blanket Purchase Agreement
    F001 = "F001"  # Grant
    F002 = "F002"  # Cooperative Agreement
    F003 = "F003"  # Direct Loan
    F004 = "F004"  # Loan Guarantee
    F005 = "F005"  # Indemnity / Insurance
    F006 = "F006"  # Direct Payment for Specified Use
    F007 = "F007"  # Direct Payment with Unrestricted Use
    F008 = "F008"  # Asset Forfeiture / Equitable Sharing
    F009 = "F009"  # Sale, Exchange, or Donation
    F010 = "F010"  # Other Financial Assistance


class AgencyTier(StrEnum):
    """Agency tier types"""

    TOPTIER = "toptier"
    SUBTIER = "subtier"


class AgencyType(StrEnum):
    """Agency types for filtering"""

    AWARDING = "awarding"
    FUNDING = "funding"


class SortOrder(StrEnum):
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
        except ValueError as e:
            raise ValueError("Date must be in YYYY-MM-DD format") from e

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
