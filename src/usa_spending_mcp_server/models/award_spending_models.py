from typing import Any

from pydantic import BaseModel

from usa_spending_mcp_server.models.common_models import (
    Agency,
    AwardTypeCode,
    BasePagination,
    BaseSearchFilters,
    BaseSearchRequest,
    SortOrder,
    TimePeriod,
)


class AwardDetailsRequest(BaseModel):
    """Award details request model for single or multiple awards"""

    award_ids: list[str]
    max_concurrent: int = 10

    @classmethod
    def from_params(
        cls,
        award_id: str,
        max_concurrent: str = "10",
    ) -> "AwardDetailsRequest":
        """Create AwardDetailsRequest from comma-separated award IDs

        Args:
            award_id: Single award ID or comma-separated list of award IDs
            max_concurrent: Maximum number of concurrent requests (default: 10)
        """
        # Parse comma-separated award IDs
        award_ids = [aid.strip() for aid in award_id.split(",") if aid.strip()]
        max_concurrent_int = min(int(max_concurrent), 10)  # Cap at 10

        return cls(award_ids=award_ids, max_concurrent=max_concurrent_int)


class AwardAmount(BaseModel):
    """Award amount range filter"""

    lower_bound: float | None = None
    upper_bound: float | None = None


class ProgramActivityObject(BaseModel):
    name: str | None = None
    code: str | None = None


class AwardSearchFilters(BaseSearchFilters):
    """Filters specific to award search"""

    award_ids: list[str] | None = None
    keywords: list[str] | None = None
    award_amounts: list[AwardAmount] | None = None
    program_activities: list[ProgramActivityObject] | None = None


class AwardSearchRequest(BaseSearchRequest):
    """Award search request model"""

    filters: AwardSearchFilters
    fields: list[str] = [
        "Award ID",
        "Recipient Name",
        "Start Date",
        "End Date",
        "Award Amount",
        "Awarding Agency",
        "Awarding Sub Agency",
        "Award Type",
    ]
    sort: str | None = None
    subawards: bool = False

    @classmethod
    def from_params(
        cls,
        award_type_codes: str,
        start_date: str = "2023-10-01",
        end_date: str = "2024-09-30",
        agencies: str | None = None,
        program_activities: str | None = None,
        recipients: str | None = None,
        award_ids: str | None = None,
        keywords: str | None = None,
        award_amounts: str | None = None,
        fields: str | None = None,
        subawards: str = "false",  # Changed to str
        page: str = "1",  # Changed to str
        limit: str = "10",  # Changed to str
        sort: str | None = None,
        order: str = "desc",
    ) -> "AwardSearchRequest":
        """Create AwardSearchRequest from individual parameters

        Args:
            award_type_codes: Comma-separated award type codes
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            agencies: Comma-separated agency strings
            recipients: Comma-separated recipient names
            award_ids: Comma-separated award IDs
            keywords: Comma-separated keywords to search in award descriptions
            award_amounts: Semicolon-separated ranges in format "min-max" or "min-" or "-max"
                          Example: "1000-5000;10000-50000" or "100000-" or "-1000"
            fields: Comma-separated field names
            subawards: Whether to include subawards
            page: Page number
            limit: Results per page
            sort: Sort field
            order: Sort order (asc/desc)
        """

        # Convert string parameters to proper types
        subawards_bool = str(subawards).lower() in ("true", "1", "yes", "on")
        page_int = int(page)
        limit_int = int(limit)

        # Parse award type codes
        award_types = [AwardTypeCode(code.strip()) for code in award_type_codes.split(",")]

        # Parse agencies
        agency_objects = []
        if agencies:
            for agency_str in agencies.split(","):
                agency_objects.append(Agency.parse_agency_string(agency_str))

        program_activity_list = None
        if program_activities:
            program_activity_list = []
            for entry in program_activities.split(";"):
                name, *code = entry.split("|")
                program_activity_list.append(
                    ProgramActivityObject(
                        name=name.strip() if name else None,
                        code=code[0].strip() if code else None,
                    )
                )

        # Parse recipients
        recipient_list = None
        if recipients:
            recipient_list = [r.strip() for r in recipients.split(",")]

        # Parse award IDs
        award_id_list = None
        if award_ids:
            award_id_list = [aid.strip() for aid in award_ids.split(",")]

        # Parse keywords
        keyword_list = None
        if keywords:
            keyword_list = [k.strip() for k in keywords.split(",")]

        # Parse award amounts
        award_amount_list = None
        if award_amounts:
            award_amount_list = []
            for amount_range in award_amounts.split(";"):
                amount_range = amount_range.strip()
                if "-" in amount_range:
                    parts = amount_range.split("-", 1)
                    lower = float(parts[0]) if parts[0] else None
                    upper = float(parts[1]) if parts[1] else None
                    award_amount_list.append(AwardAmount(lower_bound=lower, upper_bound=upper))

        # Parse fields
        field_list = None
        if fields:
            field_list = [f.strip() for f in fields.split(",")]

        # Create filters
        filters = AwardSearchFilters(
            time_period=[TimePeriod(start_date=start_date, end_date=end_date)],
            award_type_codes=award_types,
            agencies=agency_objects if agency_objects else None,
            recipient_search_text=recipient_list,
            award_ids=award_id_list,
            keywords=keyword_list,
            award_amounts=award_amount_list,
            program_activities=program_activity_list,
        )

        # Create pagination
        pagination = BasePagination(page=page_int, limit=limit_int, order=SortOrder(order))

        return cls(
            filters=filters,
            fields=field_list or cls.model_fields["fields"].default,
            sort=sort,
            subawards=subawards_bool,
            pagination=pagination,
        )

    def to_api_payload(self) -> dict[str, Any]:
        """Convert to API payload format"""
        payload = {
            "subawards": self.subawards,
            "page": self.pagination.page,
            "limit": self.pagination.limit,
            "order": self.pagination.order.value,
            "fields": self.fields,
            "filters": {
                "time_period": [tp.dict() for tp in self.filters.time_period],
                "award_type_codes": (
                    [code.value for code in self.filters.award_type_codes]
                    if self.filters.award_type_codes
                    else None
                ),
            },
        }

        if self.sort:
            payload["sort"] = self.sort

        if self.filters.agencies:
            payload["filters"]["agencies"] = [
                agency.model_dump(exclude_none=True) for agency in self.filters.agencies
            ]

        if self.filters.recipient_search_text:
            payload["filters"]["recipient_search_text"] = self.filters.recipient_search_text

        if self.filters.award_ids:
            payload["filters"]["award_ids"] = self.filters.award_ids

        if self.filters.keywords:
            payload["filters"]["keywords"] = self.filters.keywords

        if self.filters.award_amounts:
            payload["filters"]["award_amounts"] = [
                amount.dict() for amount in self.filters.award_amounts
            ]

        if self.filters.program_activities:
            payload["filters"]["program_activities"] = [
                pa.dict() for pa in self.filters.program_activities
            ]

        # Remove None values from filters
        payload["filters"] = {k: v for k, v in payload["filters"].items() if v is not None}

        # Remove None values from top level
        return {k: v for k, v in payload.items() if v is not None}
