"""Short words or phrases assigned to works using AI.

No SQL table.
"""
# pylint: disable=too-few-public-methods

from typing import Optional

from openalex_types.common import Date8601, DateTimeNoTZ, OpenAlexObject


class Keyword(OpenAlexObject):
    """OpenAlex Keyword Object."""

    cited_by_count: Optional[int] = None
    created_date: Optional[Date8601] = None
    display_name: Optional[str] = None
    updated_date: Optional[DateTimeNoTZ] = None
    works_count: Optional[int] = None
