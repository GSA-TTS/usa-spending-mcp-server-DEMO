from enum import Enum
from typing import Any

from pydantic import ValidationInfo, field_validator

from usa_spending_mcp_server.models.common_models import (
    Agency,
    AwardTypeCode,
    BasePagination,
    BaseSearchFilters,
    BaseSearchRequest,
    SortOrder,
    TimePeriod,
)


class GeographicScope(str, Enum):
    """Geographic scope options"""

    PLACE_OF_PERFORMANCE = "place_of_performance"
    RECIPIENT_LOCATION = "recipient_location"


class GeographicLayer(str, Enum):
    """Geographic aggregation levels"""

    STATE = "state"
    COUNTY = "county"
    DISTRICT = "district"
    ZIP = "zip"


class GeographySearchFilters(BaseSearchFilters):
    """Filters for geography search - inherits from base filters"""

    pass


class GeographySearchRequest(BaseSearchRequest):
    """Geography search request model"""

    scope: GeographicScope
    geo_layer: GeographicLayer
    geo_layer_filters: list[str]
    filters: GeographySearchFilters
    sort: str = "aggregated_amount"
    subawards: bool = False

    @field_validator("geo_layer_filters")
    @classmethod
    def validate_geo_filters(cls, v: list[str], info: ValidationInfo) -> list[str]:
        """Validate geographic filters based on geo_layer"""
        # Get geo_layer from the data being validated
        geo_layer = info.data.get("geo_layer")
        if not geo_layer:
            return v

        for filter_code in v:
            if geo_layer == GeographicLayer.STATE:
                # States: 2-letter codes or 2-digit FIPS
                if not (
                    len(filter_code) == 2 and (filter_code.isalpha() or filter_code.isdigit())
                ):
                    raise ValueError(
                        "State codes must be 2-letter postal codes or 2-digit FIPS codes: "
                        f"{filter_code}"
                    )
            elif geo_layer == GeographicLayer.COUNTY:
                # Counties: 5-digit FIPS codes
                if not (len(filter_code) == 5 and filter_code.isdigit()):
                    raise ValueError(f"County codes must be 5-digit FIPS codes: {filter_code}")
            elif geo_layer == GeographicLayer.ZIP:
                # ZIP: 5-digit ZIP codes
                if not (len(filter_code) == 5 and filter_code.isdigit()):
                    raise ValueError(f"ZIP codes must be 5-digit codes: {filter_code}")
            elif geo_layer == GeographicLayer.DISTRICT:
                # Districts: State code + district (e.g., WA01, CA12)
                if not (
                    len(filter_code) >= 4
                    and filter_code[:2].isalpha()
                    and filter_code[2:].isdigit()
                ):
                    raise ValueError(
                        f"District codes must be state code + district number: {filter_code}"
                    )

        return v

    @classmethod
    def from_params(
        cls,
        scope: str,
        geo_layer: str,
        geo_layer_filters: str,
        award_types: str | None = None,
        agencies: str | None = None,
        recipients: str | None = None,
        start_date: str = "2023-10-01",
        end_date: str = "2024-09-30",
        subawards: str = "false",
        page: str = "1",
        limit: str = "100",
        sort: str = "aggregated_amount",
        order: str = "desc",
    ) -> "GeographySearchRequest":
        """Create GeographySearchRequest from individual parameters (MCP string format)"""

        # Convert string parameters to proper types
        subawards_bool = str(subawards).lower() in ("true", "1", "yes", "on")
        page_int = int(page)
        limit_int = int(limit)

        # Parse geographic filters
        geo_filters = [code.strip() for code in geo_layer_filters.split(",")]

        # Parse award types
        award_type_list = None
        if award_types:
            award_type_list = [AwardTypeCode(code.strip()) for code in award_types.split(",")]

        # Parse recipients
        recipient_list = None
        if recipients:
            recipient_list = [r.strip() for r in recipients.split(",")]

        agency_objects = []
        if agencies:
            for agency_str in agencies.split(","):
                agency_objects.append(Agency.parse_agency_string(agency_str))

        # Create filters
        filters = GeographySearchFilters(
            time_period=[TimePeriod(start_date=start_date, end_date=end_date)],
            award_type_codes=award_type_list,
            agencies=agency_objects,
            recipient_search_text=recipient_list,
        )

        # Create pagination
        pagination = BasePagination(page=page_int, limit=limit_int, order=SortOrder(order))

        # Create instance
        instance = cls(
            scope=GeographicScope(scope),
            geo_layer=GeographicLayer(geo_layer),
            geo_layer_filters=geo_filters,
            filters=filters,
            sort=sort,
            subawards=subawards_bool,
            pagination=pagination,
        )

        return instance

    def to_api_payload(self) -> dict[str, Any]:
        """Convert to API payload format"""

        # Build filters dictionary
        filters = {}

        # Add time_period filters
        if self.filters.time_period:
            filters["time_period"] = [tp.dict() for tp in self.filters.time_period]

        # Add award_type_codes if present
        if self.filters.award_type_codes:
            filters["award_type_codes"] = [code.value for code in self.filters.award_type_codes]

        # Add agencies - use parsed agencies from MCP string parsing
        if self.filters.agencies:
            filters["agencies"] = [
                agency.model_dump(exclude_none=True) for agency in self.filters.agencies
            ]

        # Add recipient_search_text if present
        if self.filters.recipient_search_text:
            filters["recipient_search_text"] = self.filters.recipient_search_text

        # Build the main payload
        payload = {
            "scope": self.scope,
            "geo_layer": self.geo_layer,
            "geo_layer_filters": self.geo_layer_filters,
            "subawards": self.subawards,
            "page": self.pagination.page,
            "limit": self.pagination.limit,
            "sort": self.sort,
            "order": self.pagination.order.value,
            "filters": filters,
        }

        return payload
