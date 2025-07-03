from enum import Enum
from typing import Any, Dict, Optional, Union

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

    fy: str = Field(..., description="Fiscal year")
    quarter: Quarter = Field(..., description="Quarter (required for general explorer)")

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

    fy: str = Field(..., description="Fiscal year")
    quarter: Optional[Quarter] = Field(None, description="Quarter")
    period: Optional[Period] = Field(None, description="Period")
    agency: Optional[int] = Field(None, description="Agency ID")
    federal_account: Optional[int] = Field(None, description="Federal Account ID")
    object_class: Optional[int] = Field(None, description="Object Class ID")
    budget_function: Optional[int] = Field(None, description="Budget Function ID")
    budget_subfunction: Optional[int] = Field(None, description="Budget Subfunction ID")
    recipient: Optional[int] = Field(None, description="Recipient ID")
    program_activity: Optional[int] = Field(None, description="Program Activity ID")

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

    type: ExplorerType = Field(..., description="Type of data grouping")
    filters: Union[GeneralFilter, DetailedFilter] = Field(
        ..., description="Filter criteria"
    )

    @classmethod
    def from_params(
        cls,
        type: str,
        fiscal_year: str,
        quarter: Optional[str] = None,
        period: Optional[str] = None,
        agency: Optional[str] = None,
        federal_account: Optional[str] = None,
        object_class: Optional[str] = None,
        budget_function: Optional[str] = None,
        budget_subfunction: Optional[str] = None,
        recipient: Optional[str] = None,
        program_activity: Optional[str] = None,
    ) -> "SpendingExplorerRequest":
        """Create request from string parameters"""

        explorer_type = ExplorerType(type)

        # Determine if this is a general or detailed request
        # General requests are for top-level entry points and require quarter
        is_general = explorer_type in [
            ExplorerType.BUDGET_FUNCTION,
            ExplorerType.AGENCY,
            ExplorerType.OBJECT_CLASS,
        ]

        if is_general:
            # General explorer requires quarter
            if not quarter:
                raise ValueError("Quarter is required for general explorer requests")

            filters = GeneralFilter(fy=fiscal_year, quarter=Quarter(quarter))
        else:
            # Detailed explorer - convert string parameters to integers where applicable
            filters_dict = {"fy": fiscal_year}

            if quarter:
                filters_dict["quarter"] = Quarter(quarter)
            if period:
                filters_dict["period"] = Period(period)
            if agency:
                filters_dict["agency"] = agency
            if federal_account:
                filters_dict["federal_account"] = federal_account
            if object_class:
                filters_dict["object_class"] = object_class
            if budget_function:
                filters_dict["budget_function"] = budget_function
            if budget_subfunction:
                filters_dict["budget_subfunction"] = budget_subfunction
            if recipient:
                filters_dict["recipient"] = recipient
            if program_activity:
                filters_dict["program_activity"] = program_activity

            filters = DetailedFilter(**filters_dict)

        return cls(type=explorer_type, filters=filters)

    def to_api_payload(self) -> Dict[str, Any]:
        """Convert to API payload format"""

        payload = {"type": self.type.value, "filters": {}}

        # Add filters based on type
        if isinstance(self.filters, GeneralFilter):
            payload["filters"]["fy"] = self.filters.fy
            payload["filters"]["quarter"] = self.filters.quarter.value
        else:
            # DetailedFilter
            payload["filters"]["fy"] = self.filters.fy

            # Add optional fields that are not None
            if self.filters.quarter:
                payload["filters"]["quarter"] = self.filters.quarter.value
            if self.filters.period:
                payload["filters"]["period"] = self.filters.period.value
            if self.filters.agency is not None:
                payload["filters"]["agency"] = self.filters.agency
            if self.filters.federal_account is not None:
                payload["filters"]["federal_account"] = self.filters.federal_account
            if self.filters.object_class is not None:
                payload["filters"]["object_class"] = self.filters.object_class
            if self.filters.budget_function is not None:
                payload["filters"]["budget_function"] = self.filters.budget_function
            if self.filters.budget_subfunction is not None:
                payload["filters"][
                    "budget_subfunction"
                ] = self.filters.budget_subfunction
            if self.filters.recipient is not None:
                payload["filters"]["recipient"] = self.filters.recipient
            if self.filters.program_activity is not None:
                payload["filters"]["program_activity"] = self.filters.program_activity

        return payload
