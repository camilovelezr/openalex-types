"""Authors Models."""
# pylint: disable=too-few-public-methods

from typing import Optional

from openalex_types.common import (
    BaseCountByYear,
    Date8601,
    DateTimeNoTZ,
    OpenAlexObject,
    SummaryStats,
    SQLTable,
)
from openalex_types.institutions import DehydratedInstitution
from openalex_types.utils import check
from psycopg import Connection
from pydantic import BaseModel, model_validator, field_validator


class AuthorCountByYear(BaseCountByYear, SQLTable):
    """Author Count by Year."""
    author_id: str
    _sql_table_name = "openalex.authors_counts_by_year"
    _sql_order = ["author_id", "year", "works_count",
                  "cited_by_count", "oa_works_count"]


class AuthorIDs(BaseModel, SQLTable):
    """Author ID."""
    author_id: str
    openalex: Optional[str] = None
    orcid: Optional[str] = None
    scopus: Optional[str] = None
    twitter: Optional[str] = None
    wikipedia: Optional[str] = None
    mag: Optional[int] = None
    _sql_table_name = "openalex.authors_ids"
    _sql_order = ["author_id", "openalex", "orcid", "scopus",
                  "twitter", "wikipedia", "mag"]

    @property
    def sql_table_name(self) -> str:
        """SQL table name."""
        return "openalex.authors_ids"

class AuthorAffiliation(BaseModel):
    """Affiliation for Author."""
    institution: Optional[DehydratedInstitution] = None
    years: Optional[list[int]] = None


class DehydratedAuthor(OpenAlexObject):
    """Dehydrated Author."""
    display_name: Optional[str] = None
    orcid: Optional[str] = None

SQL_TABLES_TO_CLASSES = {
    "counts_by_year": AuthorCountByYear,
    "ids": AuthorIDs
}
# which tables have multiple values (list)?
MULTIVALUE = ["counts_by_year"]

class Author(OpenAlexObject, SQLTable):
    """OpenAlex Authors."""
    orcid: Optional[str] = None
    display_name: Optional[str] = None
    display_name_alternatives: Optional[list[str]] = None
    works_count: Optional[int] = None
    cited_by_count: Optional[int] = None
    last_known_institution: Optional[str] = None  # NOTE: deprecated!
    works_api_url: Optional[str] = None
    updated_date: Optional[DateTimeNoTZ] = None
    ids: Optional[AuthorIDs] = None
    counts_by_year: Optional[list[AuthorCountByYear]] = None
    affiliations: Optional[list[AuthorAffiliation]] = None
    created_date: Optional[Date8601] = None
    last_known_institutions: Optional[list[DehydratedInstitution]] = None
    summary_stats: Optional[SummaryStats] = None
    _sql_table_name = "openalex.authors"
    _sql_order = ["id", "orcid", "display_name", "display_name_alternatives", "works_count", "cited_by_count",
                  "last_known_institution", "works_api_url", "updated_date"]
    _sql_subtables = ["counts_by_year", "ids"]
    # x_concepts will be removed soon so not included here

    @model_validator(mode="before")
    def _replicate_id(self):
        """Replicate author_id in 'subtables'."""
        if check("counts_by_year", self):
            for count_by_year in self["counts_by_year"]:
                count_by_year["author_id"] = self["id"]
        # replicate in ids
        if check("ids", self):
            self["ids"]["author_id"] = self["id"]
        return self
    
    @field_validator("display_name_alternatives", mode="after")
    @classmethod
    def _remove_quotation_marks(cls, v):
        """Remove quotation marks from display_name_alternatives."""
        if v is None:
            return None
        return [x.replace('"', "") for x in v]

    @field_validator("counts_by_year", "display_name_alternatives")
    @classmethod
    def _check_not_empty(cls, val: list) -> list | None:
        """Check if list is not empty."""
        if val is None or len(val) == 0:
            return None
        return val

    @staticmethod
    def from_sql(t: tuple, conn: Optional[Connection] = None,
                 subtables: Optional[dict] = None) -> "Author":
        """Create Author from SQL."""
        args = dict(zip(Author._sql_order.default, t))  # type: ignore
        if conn is None:
            if subtables is None:  # only Author object
                return Author(**args)
            else:  # Author object with subtables already queried
                for subtable in Author._sql_subtables.default:  # type: ignore
                    if subtable in subtables:
                        if subtable in MULTIVALUE:
                            args[subtable] = [dict(zip(
                                SQL_TABLES_TO_CLASSES[subtable]._sql_order.default, t)  # type: ignore
                            )
                                for t in subtables[subtable]]
                        else:
                            args[subtable] = dict(
                                zip(SQL_TABLES_TO_CLASSES[subtable]._sql_order.default, subtables[subtable])  # type: ignore
                            )
            return Author(**args)
        else:  # Query everything, connection is provided
            id_ = t[0]
            with conn.cursor() as cursor:
                for subtable in Author._sql_subtables.default:  # type: ignore
                    subtable_cls = SQL_TABLES_TO_CLASSES[subtable]
                    if subtable in MULTIVALUE:
                        cursor.execute(
                            f"SELECT * FROM {subtable_cls._sql_table_name.default} WHERE author_id = %s", (id_,))  # type: ignore
                        list_ = [dict(zip(subtable_cls._sql_order.default, t))  # type: ignore
                                 for t in cursor.fetchall()]
                        if len(list_) > 0:
                            args[subtable] = list_
                    else:
                        cursor.execute(
                            f"SELECT * FROM {subtable_cls._sql_table_name.default} WHERE author_id = %s", (id_,))  # type: ignore
                        t = cursor.fetchone()
                        if t is not None:
                            args[subtable] = dict(
                                zip(subtable_cls._sql_order.default, t))  # type: ignore
            return Author(**args)
