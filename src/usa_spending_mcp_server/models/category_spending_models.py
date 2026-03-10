from enum import StrEnum
from typing import Annotated

from pydantic import Field

from usa_spending_mcp_server.models.common_models import BaseSearchFilters


class SpendingCategory(StrEnum):
    """Available spending category types for aggregation"""

    AWARDING_AGENCY = "awarding_agency"
    AWARDING_SUBAGENCY = "awarding_subagency"
    FUNDING_AGENCY = "funding_agency"
    FUNDING_SUBAGENCY = "funding_subagency"
    RECIPIENT = "recipient"
    RECIPIENT_DUNS = "recipient_duns"
    CFDA = "cfda"
    NAICS = "naics"
    PSC = "psc"
    STATE_TERRITORY = "state_territory"
    COUNTY = "county"
    DISTRICT = "district"
    COUNTRY = "country"
    FEDERAL_ACCOUNT = "federal_account"
    DEFC = "defc"


class CategorySearchFilters(BaseSearchFilters):
    """Filters for category spending search — inherits from base filters.

    Supports all standard filters: time_period, award_type_codes, agencies,
    recipient_search_text, recipient_type_names, place_of_performance_locations,
    recipient_locations.
    """

    keywords: Annotated[
        list[str] | None,
        Field(description="List of keywords to search in award descriptions"),
    ] = None
