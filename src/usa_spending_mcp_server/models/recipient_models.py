from typing import Optional

from pydantic import BaseModel, Field, field_validator

from usa_spending_mcp_server.models.common_models import (
    BasePagination,
    BaseSearchRequest,
    SortOrder,
)


class RecipientSearchRequest(BaseSearchRequest):
    """Model for recipient search request"""

    keyword: Optional[str] = None
    award_type: str = "all"
    sort: str = "amount"
    order: str = "desc"

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

    @classmethod
    def from_params(
        cls,
        keyword: Optional[str] = None,
        award_type: str = "all",
        sort: str = "amount",
        order: str = "desc",
        page: str = "1",
        limit: str = "100",
    ) -> "RecipientSearchRequest":
        """Create request from string parameters"""
        page_int = int(page)
        limit_int = int(limit)
        pagination = BasePagination(
            page=page_int, limit=limit_int, order=SortOrder(order)
        )

        return cls(
            keyword=keyword,
            award_type=award_type,
            sort=sort,
            order=order,
            pagination=pagination,
        )

    def to_api_payload(self) -> dict:
        """Convert to API request payload"""
        payload = {
            "award_type": self.award_type,
            "sort": self.sort,
            "order": self.order,
            "page": self.pagination.page,
            "limit": self.pagination.limit,
        }

        # Only include keyword if provided
        if self.keyword:
            payload["keyword"] = self.keyword

        return payload
