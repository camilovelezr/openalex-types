"""OpenAlex Funder Object."""

# pylint: disable=too-few-public-methods

from typing import Optional

from openalex_types.common import (
    BaseCountByYear,
    CountryCode,
    Date8601,
    DateTimeNoTZ,
    OpenAlexObject,
    Role,
    SummaryStats,
)
from pydantic import BaseModel, field_validator


class FunderIDs(BaseModel):
    """Funder ID."""
    openalex: Optional[str] = None
    ror: Optional[str] = None
    wikidata: Optional[str] = None
    crossref: Optional[str] = None
    doi: Optional[str] = None

    @field_validator("crossref", mode="before")
    @classmethod
    def crossref_to_str(cls, value) -> str:
        """Convert crossref to string.

        Crossref values like "1000002" are converted
        to int by `json.loads`.
        """
        return str(value) if value is not None else None


class Funder(OpenAlexObject):
    """OpenAlex Funder Object."""
    alternate_titles: Optional[list[str]] = None
    cited_by_count: Optional[int] = None
    country_code: Optional[CountryCode] = None
    counts_by_year: Optional[list[BaseCountByYear]] = None
    created_date: Optional[Date8601] = None
    description: Optional[str] = None
    display_name: Optional[str] = None
    grants_count: Optional[int] = None
    homepage_url: Optional[str] = None
    ids: Optional[FunderIDs] = None
    image_thumbnail_url: Optional[str] = None
    image_url: Optional[str] = None
    roles: Optional[list[Role]] = None
    summary_stats: Optional[SummaryStats] = None
    updated_date: Optional[DateTimeNoTZ] = None
    works_count: Optional[int] = None
