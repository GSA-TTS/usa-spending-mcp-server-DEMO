from enum import Enum
from typing import Annotated

from pydantic import Field, ValidationInfo, field_validator

from usa_spending_mcp_server.models.common_models import (
    BaseSearchFilters,
    BaseSearchRequest,
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

    scope: Annotated[GeographicScope, Field(description="Geographic scope")]
    geo_layer: Annotated[GeographicLayer, Field(description="Geographic layer")]
    geo_layer_filters: Annotated[list[str], Field(description="Geographic layer filters")]
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
