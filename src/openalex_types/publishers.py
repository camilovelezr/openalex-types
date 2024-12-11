"""Publishers Models."""
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
    SQLTable,
)
from openalex_types.utils import check
from psycopg import Connection
from pydantic import BaseModel, model_validator


class PublisherCountByYear(BaseCountByYear, SQLTable):
    """Publisher Count by Year."""
    publisher_id: str
    _sql_table_name = "openalex.publishers_counts_by_year"
    _sql_order = ["publisher_id", "year", "works_count",
                  "cited_by_count", "oa_works_count"]


class PublisherIDs(BaseModel, SQLTable):
    """Publisher ID."""
    publisher_id: Optional[str] = None
    openalex: Optional[str] = None
    ror: Optional[str] = None
    wikidata: Optional[str] = None
    _sql_table_name = "openalex.publishers_ids"
    _sql_order = ["publisher_id", "openalex", "ror", "wikidata"]


class ParentPublisher(BaseModel):
    """Parent Publisher."""
    id: Optional[str] = None
    display_name: Optional[str] = None

SQL_TABLES_TO_CLASSES = {
    "counts_by_year": PublisherCountByYear,
    "ids": PublisherIDs,
}
# which tables have multiple values (list)?
MULTIVALUE = ["counts_by_year"]

class Publisher(OpenAlexObject, SQLTable):
    """OpenAlex Publishers."""
    display_name: Optional[str] = None
    alternate_titles: Optional[list[str]] = None  # NOTE: SQL json?
    country_codes: Optional[list[CountryCode]] = None  # NOTE: SQL json?
    hierarchy_level: Optional[int] = None
    # NOTE: docs say parent_publisher: str,
    # but API response is dict {"id":__, "display_name":__}
    # parent_publisher: Optional[str] = None
    parent_publisher: Optional[ParentPublisher] = None
    works_count: Optional[int] = None
    cited_by_count: Optional[int] = None
    sources_api_url: Optional[str] = None
    updated_date: Optional[DateTimeNoTZ] = None
    counts_by_year: Optional[list[PublisherCountByYear]] = None
    created_date: Optional[Date8601] = None
    ids: Optional[PublisherIDs] = None
    image_thumbnail_url: Optional[str] = None
    image_url: Optional[str] = None
    lineage: Optional[list[str]] = None
    roles: Optional[list[Role]] = None
    summary_stats: Optional[SummaryStats] = None
    _sql_table_name = "openalex.publishers"
    _sql_order = ["id", "display_name", "alternate_titles",
                  "country_codes", "hierarchy_level", "parent_publisher",
                  "works_count", "cited_by_count", "sources_api_url",
                  "updated_date"]
    _sql_subtables = ["counts_by_year", "ids"]

    @model_validator(mode="before")
    def _replicate_id(self):
        """Replicate ID."""
        if check("counts_by_year", self):
            for count in self["counts_by_year"]:
                count["publisher_id"] = self["id"]
        if check("ids", self):
            self["ids"]["publisher_id"] = self["id"]

        return self

    @staticmethod
    def from_sql(t: tuple, conn: Optional[Connection] = None,
                 subtables: Optional[dict] = None) -> "Publisher":
        """Create Publisher from SQL."""
        args = dict(zip(Publisher._sql_order.default, t))
        if conn is None:
            if subtables is None:  # only Publisher object
                return Publisher(**args)
            else:  # Publisher object with subtables already queried
                for subtable in Publisher._sql_subtables.default:  
                    if subtable in subtables:
                        if subtable in MULTIVALUE:
                            args[subtable] = [dict(zip(
                                SQL_TABLES_TO_CLASSES[subtable]._sql_order.default, t)
                            )
                                for t in subtables[subtable]]
                        else:
                            args[subtable] = dict(zip(
                                SQL_TABLES_TO_CLASSES[subtable]._sql_order.default, subtables[subtable])
                            )

            return Publisher(**args)
        else:  # Query everything, connection is provided
            id_ = t[0]
            with conn.cursor() as cursor:
                for subtable in Publisher._sql_subtables.default:
                    subtable_cls = SQL_TABLES_TO_CLASSES[subtable]
                    if subtable in MULTIVALUE:
                        cursor.execute(
                            f"SELECT * FROM {subtable_cls._sql_table_name.default} WHERE publisher_id = %s", (id_,))
                        list_ = [dict(zip(subtable_cls._sql_order.default, t))
                                 for t in cursor.fetchall()]
                        if len(list_) > 0:
                            args[subtable] = list_
                    else:
                        cursor.execute(
                            f"SELECT * FROM {subtable_cls._sql_table_name.default} WHERE publisher_id = %s", (id_,))
                        t = cursor.fetchone()
                        if t is not None:
                            args[subtable] = dict(
                                zip(subtable_cls._sql_order.default, t))
            return Publisher(**args)