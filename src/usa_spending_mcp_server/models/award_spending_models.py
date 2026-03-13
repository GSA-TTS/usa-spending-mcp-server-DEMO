from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from usa_spending_mcp_server.models.common_models import (
    AwardTypeCode,
    BaseSearchFilters,
    BaseSearchRequest,
)

AWARD_TYPE_GROUPS = {
    "contracts": {"A", "B", "C", "D"},
    "grants": {"02", "03", "04", "05", "F001", "F002"},
    "idvs": {"IDV_A", "IDV_B", "IDV_B_A", "IDV_B_B", "IDV_B_C", "IDV_C", "IDV_D", "IDV_E"},
    "loans": {"07", "08", "F003", "F004"},
    "other_financial_assistance": {"06", "10", "F006", "F007"},
    "direct_payments": {"09", "11", "-1", "F005", "F008", "F009", "F010"},
}


class AwardDetailsRequest(BaseModel):
    """Award details request model for single or multiple awards"""

    award_ids: Annotated[list[str], Field(description="List of award IDs")] = []
    max_concurrent: Annotated[
        int, Field(default=10, description="Maximum number of concurrent requests")
    ] = 10


class AwardAmount(BaseModel):
    """Award amount range filter"""

    lower_bound: Annotated[float | None, Field(description="Lower bound of the award amount")] = (
        None
    )
    upper_bound: Annotated[float | None, Field(description="Upper bound of the award amount")] = (
        None
    )


class ProgramActivityObject(BaseModel):
    name: Annotated[str | None, Field(description="Program activity name")] = None
    code: Annotated[str | None, Field(description="Program activity code")] = None


class AwardSearchFilters(BaseSearchFilters):
    """Filters specific to award search"""

    award_ids: Annotated[list[str] | None, Field(description="List of award IDs")] = None
    keywords: Annotated[
        list[str] | None, Field(description="List of keywords to search in award descriptions")
    ] = None
    award_type_codes: Annotated[
        list[AwardTypeCode] | None,
        Field(
            description=(
                "List of award type codes. Defaults to contracts only [A, B, C, D]. "
                "IMPORTANT: All codes must be from the same group — mixing groups returns HTTP 422. "
                "For cross-type totals, make separate calls per group and sum the results, "
                "or use search_spending_by_category() which aggregates across all types. "
                "Groups: Contracts=[A,B,C,D], Grants=[02,03,04,05], "
                "DirectPayments=[06,10], Loans=[07,08], Other=[09,11,-1]"
            )
        ),
    ] = [
        AwardTypeCode.BPA_CALL,
        AwardTypeCode.PURCHASE_ORDER,
        AwardTypeCode.DELIVERY_ORDER,
        AwardTypeCode.DEFINITIVE_CONTRACT,
    ]
    award_amounts: Annotated[
        list[AwardAmount] | None, Field(description="List of award amount ranges")
    ] = None
    program_activities: Annotated[
        list[ProgramActivityObject] | None, Field(description="List of program activities")
    ] = None

    @model_validator(mode="after")
    def validate_award_type_codes(self):
        codes = self.award_type_codes
        if not codes:
            return self
        code_values = {c.value if hasattr(c, "value") else c for c in codes}
        matched_groups = [
            group_name
            for group_name, group_codes in AWARD_TYPE_GROUPS.items()
            if code_values & group_codes
        ]
        if len(matched_groups) > 1:
            raise ValueError(
                f"award_type_codes mixes groups {matched_groups}. "
                f"The USASpending API requires all codes from a single group. "
                f"Make separate calls for each group."
            )
        return self


class AwardSearchRequest(BaseSearchRequest):
    """Award search request model"""

    model_config = ConfigDict(extra="ignore")

    filters: Annotated[AwardSearchFilters, Field(description="Filters for the award search")]
    fields: Annotated[list[str], Field(description="List of fields to include in the response")] = [
        "Award ID",
        "Recipient Name",
        "Start Date",
        "End Date",
        "Award Amount",
        "Awarding Agency",
        "Awarding Sub Agency",
        "Award Type",
        "generated_internal_id",
    ]
    sort: Annotated[str | None, Field(description="Sort order for the award search")] = None
    subawards: Annotated[
        bool, Field(default=False, description="Include subawards in the search")
    ] = False
