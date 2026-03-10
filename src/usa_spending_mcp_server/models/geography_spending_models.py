from enum import StrEnum
from typing import Annotated

from pydantic import Field, ValidationInfo, field_validator

from usa_spending_mcp_server.models.common_models import (
    BaseSearchFilters,
    BaseSearchRequest,
)


class GeographicScope(StrEnum):
    """Geographic scope options"""

    PLACE_OF_PERFORMANCE = "place_of_performance"
    RECIPIENT_LOCATION = "recipient_location"


class GeographicLayer(StrEnum):
    """Geographic aggregation levels"""

    STATE = "state"
    COUNTY = "county"
    DISTRICT = "district"
    ZIP = "zip"


class GeographySearchFilters(BaseSearchFilters):
    """Filters for geography search - inherits from base filters"""

    keywords: Annotated[
        list[str] | None,
        Field(description="List of keywords to search in award descriptions"),
    ] = None


class GeographySearchRequest(BaseSearchRequest):
    """Geography search request model"""

    scope: Annotated[GeographicScope, Field(description="Geographic scope")]
    geo_layer: Annotated[GeographicLayer, Field(description="Geographic layer")]
    geo_layer_filters: Annotated[
        list[str],
        Field(
            description=(
                "Geographic layer filters. Pass an empty list to return ALL results "
                "for the specified layer (e.g., all states, all districts). "
                "When empty, the field is omitted from the API request."
            )
        ),
    ] = []
    filters: Annotated[
        GeographySearchFilters, Field(description="Filters for the geography search")
    ]
    sort: Annotated[str, Field(default="aggregated_amount", description="Sort field")] = (
        "aggregated_amount"
    )
    subawards: Annotated[bool, Field(default=False, description="Include subawards")] = False

    @field_validator("geo_layer_filters")
    @classmethod
    def validate_geo_filters(cls, v: list[str], info: ValidationInfo) -> list[str]:
        """Validate geographic filters based on geo_layer. Empty list is allowed."""
        geo_layer = info.data.get("geo_layer")
        if not geo_layer or not v:
            return v

        for filter_code in v:
            if geo_layer == GeographicLayer.STATE:
                # States: 2-letter codes or 2-digit FIPS
                if not (len(filter_code) == 2 and (filter_code.isalpha() or filter_code.isdigit())):
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
            elif geo_layer == GeographicLayer.DISTRICT and not (
                len(filter_code) >= 4 and filter_code[:2].isalpha() and filter_code[2:].isdigit()
            ):
                # Districts: State code + district (e.g., WA01, CA12)
                raise ValueError(
                    f"District codes must be state code + district number: {filter_code}"
                )

        return v

    def to_api_payload(self) -> dict:
        """Convert to API payload, omitting geo_layer_filters when empty."""
        payload = self.model_dump(exclude_none=True)
        # The USAspending API rejects empty geo_layer_filters with HTTP 422.
        # Omitting the field entirely returns all results for the layer.
        if not payload.get("geo_layer_filters"):
            payload.pop("geo_layer_filters", None)
        return payload
