from enum import Enum
from typing import Annotated, Union

from pydantic import BaseModel, Field
from pydantic.functional_validators import field_validator


class ExplorerType(str, Enum):
    """Types of spending explorer data groupings"""

    # General Explorer (top-level entry points)
    BUDGET_FUNCTION = "budget_function"
    AGENCY = "agency"
    OBJECT_CLASS = "object_class"

    # Specific Explorer (drill-down types)
    FEDERAL_ACCOUNT = "federal_account"
    RECIPIENT = "recipient"
    AWARD = "award"
    BUDGET_SUBFUNCTION = "budget_subfunction"
    PROGRAM_ACTIVITY = "program_activity"


class Quarter(str, Enum):
    """Fiscal year quarters"""

    Q1 = "1"
    Q2 = "2"
    Q3 = "3"
    Q4 = "4"


class Period(str, Enum):
    """Fiscal year periods (months)"""

    P1 = "1"
    P2 = "2"
    P3 = "3"
    P4 = "4"
    P5 = "5"
    P6 = "6"
    P7 = "7"
    P8 = "8"
    P9 = "9"
    P10 = "10"
    P11 = "11"
    P12 = "12"


class GeneralFilter(BaseModel):
    """Filter for general spending explorer requests"""

    fy: Annotated[str, Field(description="Fiscal year")]
    quarter: Annotated[Quarter, Field(description="Quarter (required for general explorer)")]

    @field_validator("fy")
    @classmethod
    def validate_fiscal_year(cls, v):
        """Validate fiscal year format"""
        try:
            year = int(v)
            if year < 2017:
                raise ValueError("Data not available prior to FY 2017")
            return str(year)
        except ValueError as e:
            if "Data not available" in str(e):
                raise e
            raise ValueError("Fiscal year must be a valid year")


class DetailedFilter(BaseModel):
    """Filter for specific spending explorer requests"""

    fy: Annotated[str, Field(description="Fiscal year")]
    quarter: Annotated[Quarter | None, Field(None, description="Quarter")]
    period: Annotated[Period | None, Field(None, description="Period")]
    agency: Annotated[str | None, Field(None, description="Agency ID")]
    federal_account: Annotated[str | None, Field(None, description="Federal Account ID")]
    object_class: Annotated[str | None, Field(None, description="Object Class ID")]
    budget_function: Annotated[str | None, Field(None, description="Budget Function ID")]
    budget_subfunction: Annotated[str | None, Field(None, description="Budget Subfunction ID")]
    recipient: Annotated[str | None, Field(None, description="Recipient ID")]
    program_activity: Annotated[str | None, Field(None, description="Program Activity ID")]

    @field_validator("fy")
    @classmethod
    def validate_fiscal_year(cls, v):
        """Validate fiscal year format"""
        try:
            year = int(v)
            if year < 2017:
                raise ValueError("Data not available prior to FY 2017")
            return str(year)
        except ValueError as e:
            if "Data not available" in str(e):
                raise e
            raise ValueError("Fiscal year must be a valid year")


class SpendingExplorerRequest(BaseModel):
    """Request model for spending explorer"""

    type: Annotated[ExplorerType, Field(description="Type of data grouping")]
    filters: Annotated[Union[GeneralFilter, DetailedFilter], Field(description="Filter criteria")]
