from typing import Annotated

from pydantic import Field, field_validator

from usa_spending_mcp_server.models.common_models import (
    BaseSearchRequest,
)


class RecipientSearchRequest(BaseSearchRequest):
    """Model for recipient search request"""

    keyword: Annotated[str | None, Field(description="Search keyword")] = None
    award_type: Annotated[str, Field(description="Filter by award type (default: 'all')")] = "all"
    sort: Annotated[str, Field(description="Field to sort by (default: 'amount')")] = "amount"
    order: Annotated[str, Field(description="Sort direction (default: 'desc')")] = "desc"

    @field_validator("award_type")
    @classmethod
    def validate_award_type(cls, v):
        valid_types = [
            "all",
            "contracts",
            "grants",
            "loans",
            "direct_payments",
            "other_financial_assistance",
        ]
        if v not in valid_types:
            raise ValueError(f"award_type must be one of {valid_types}")
        return v

    @field_validator("sort")
    @classmethod
    def validate_sort(cls, v):
        valid_sorts = ["amount", "name", "duns"]
        if v not in valid_sorts:
            raise ValueError(f"sort must be one of {valid_sorts}")
        return v

    @field_validator("order")
    @classmethod
    def validate_order(cls, v):
        valid_orders = ["asc", "desc"]
        if v not in valid_orders:
            raise ValueError(f"order must be one of {valid_orders}")
        return v
