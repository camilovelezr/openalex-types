"""Topics Models."""
# pylint: disable=too-few-public-methods

from typing import Optional

from openalex_types.common import DateTimeNoTZ, OpenAlexObject, SQLTable
from openalex_types.utils import check
import orjson
from pydantic import AnyUrl, BaseModel, model_validator


class TopicDomainOrField(BaseModel):
    """Model for Topic Domain / Field."""
    id: str
    display_name: str


class TopicIDs(BaseModel):
    """Topic IDs."""
    openalex: Optional[str] = None
    wikipedia: Optional[str] = None


class Topic(OpenAlexObject, SQLTable):
    """OpenAlex Topics."""
    display_name: Optional[str] = None
    subfield_id: Optional[str] = None
    subfield_display_name: Optional[str] = None
    field_id: Optional[str] = None
    field_display_name: Optional[str] = None
    domain_id: Optional[str] = None
    domain_display_name: Optional[str] = None
    description: Optional[str] = None
    # keywords: Optional[str] = None  # NOTE: not list?
    works_api_url: Optional[AnyUrl] = None
    wikipedia_id: Optional[str] = None
    works_count: Optional[int] = None
    cited_by_count: Optional[int] = None
    updated_date: Optional[DateTimeNoTZ] = None
    domain: Optional[TopicDomainOrField] = None
    field: Optional[TopicDomainOrField] = None
    ids: Optional[TopicIDs] = None
    keywords: Optional[list[str]] = None  # NOTE: SQL is str, not list
    subfield: Optional[TopicDomainOrField] = None
    _sql_table_name = "openalex.topics"
    _sql_order = ["id", "display_name", "subfield_id", "subfield_display_name",
                  "field_id", "field_display_name", "domain_id",
                  "domain_display_name", "description", "keywords",
                  "works_api_url", "wikipedia_id", "works_count",
                  "cited_by_count", "updated_date"]
    # NOTE: siblings present in data, not in docs

    @model_validator(mode="before")
    def _replicate_id(self):
        """Replicate ID if no ID in IDs."""
        if check("ids", self):
            self["ids"]["openalex"] = self["id"]
        return self

    @model_validator(mode="after")
    def _check_ids(self):
        """Check IDs."""
        if self.ids is not None:
            if self.ids.openalex != self.id:
                raise ValueError(
                    "IDs' ID and object's OpenAlex ID do not match")
        return self
    
    @model_validator(mode="before")
    def _str_to_list(self):
        """Convert keywords to list."""
        if self["keywords"] is not None:
            if isinstance(self["keywords"], str):
                self["keywords"] = orjson.loads(self["keywords"])
        return self

    @model_validator(mode="after")
    def _flatten(self):
        """Flatten and populate."""
        if self.domain is not None:
            self.domain_id = self.domain.id
            self.domain_display_name = self.domain.display_name
        if self.field is not None:
            self.field_id = self.field.id
            self.field_display_name = self.field.display_name
        if self.subfield is not None:
            self.subfield_id = self.subfield.id
            self.subfield_display_name = self.subfield.display_name
        return self


    @staticmethod
    def from_sql(t: tuple) -> "Topic":
        """Create Topic from SQL."""
        args = dict(zip(Topic._sql_order.default, t))
        return Topic(**args)