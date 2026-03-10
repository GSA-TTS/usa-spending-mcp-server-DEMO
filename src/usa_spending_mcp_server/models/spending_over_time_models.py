from enum import StrEnum


class TimeGroup(StrEnum):
    """Time grouping options for spending over time"""

    FISCAL_YEAR = "fiscal_year"
    QUARTER = "quarter"
    MONTH = "month"
