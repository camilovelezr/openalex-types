"""Sources Models."""
# pylint: disable=too-few-public-methods

from typing import Optional

from openalex_types.common import (
    BaseCountByYear,
    CountryCode,
    DateTimeNoTZ,
    OpenAlexObject,
    SummaryStats,
    SQLTable,
)
from openalex_types.utils import check
from psycopg import Connection
from pydantic import BaseModel, model_validator


class SourceCountByYear(BaseCountByYear, SQLTable):
    """Source Count by Year."""
    source_id: str
    _sql_table_name = "openalex.sources_counts_by_year"
    _sql_order = ["source_id", "year", "works_count", "cited_by_count",
                  "oa_works_count"]


class SourceIDs(BaseModel, SQLTable):
    """Source ID."""
    source_id: str
    openalex: Optional[str] = None
    issn_l: Optional[str] = None
    issn: Optional[list[str]] = None
    mag: Optional[int] = None
    wikidata: Optional[str] = None
    fatcat: Optional[str] = None
    _sql_table_name = "openalex.sources_ids"
    _sql_order = ["source_id", "openalex", "issn_l",
                  "issn", "mag", "wikidata", "fatcat"]


class SourceAPC(BaseModel):
    """APC for Sources."""
    price: Optional[int] = None
    currency: Optional[str] = None


class DehydratedSource(OpenAlexObject):
    """Dehydrated Source."""
    issn_l: Optional[str] = None
    display_name: Optional[str] = None
    is_oa: Optional[bool] = None
    is_in_doaj: Optional[bool] = None
    issn: Optional[list[str]] = None
    host_organization: Optional[str] = None
    host_organization_lineage: Optional[list[str]] = None
    host_organization_name: Optional[str] = None
    is_core: Optional[bool] = None
    type: Optional[str] = None

SQL_TABLES_TO_CLASSES = {
    "counts_by_year": SourceCountByYear,
    "ids": SourceIDs,
}
# which tables have multiple values (list)?
MULTIVALUE = ["counts_by_year"]

class Source(OpenAlexObject, SQLTable):
    """OpenAlex Sources."""
    issn_l: Optional[str] = None
    # issn: Optional[dict] = None
    display_name: Optional[str] = None
    publisher: Optional[str] = None
    works_count: Optional[int] = None
    cited_by_count: Optional[int] = None
    is_oa: Optional[bool] = None
    is_in_doaj: Optional[bool] = None
    homepage_url: Optional[str] = None
    works_api_url: Optional[str] = None
    updated_date: Optional[DateTimeNoTZ] = None
    issn: Optional[list[str]] = None  # NOTE: SQL says JSON?
    abbreviated_title: Optional[str] = None
    alternate_titles: Optional[list[str]] = None
    apc_prices: Optional[list[SourceAPC]] = None
    apc_usd: Optional[int] = None
    country_code: Optional[CountryCode] = None
    counts_by_year: Optional[list[SourceCountByYear]] = None
    host_organization: Optional[str] = None
    host_organization_lineage: Optional[list[str]] = None
    host_organization_name: Optional[str] = None
    ids: Optional[SourceIDs] = None
    is_core: Optional[bool] = None
    summary_stats: Optional[SummaryStats] = None
    type: Optional[str] = None
    _sql_table_name = "openalex.sources"
    _sql_order = ["id", "issn_l", "issn", "display_name",
                  "publisher", "works_count", "cited_by_count",
                  "is_oa", "is_in_doaj", "homepage_url", "works_api_url", 
                  "updated_date"]
    _sql_subtables = ["counts_by_year", "ids"]

    @model_validator(mode="before")
    def _replicate_id(self):
        """Replicate Source ID."""
        if check("counts_by_year", self):
            for count in self["counts_by_year"]:
                count["source_id"] = self["id"]
        if check("ids", self):
            self["ids"]["source_id"] = self["id"]
        return self

    @staticmethod
    def from_sql(t: tuple, conn: Optional[Connection] = None,
                 subtables: Optional[dict] = None) -> "Source":
        """Create Source from SQL."""
        args = dict(zip(Source._sql_order.default, t))
        if conn is None:
            if subtables is None:  # only Source object
                return Source(**args)
            else:  # Source object with subtables already queried
                for subtable in Source._sql_subtables.default:  
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

            return Source(**args)
        else:  # Query everything, connection is provided
            id_ = t[0]
            with conn.cursor() as cursor:
                for subtable in Source._sql_subtables.default:
                    subtable_cls = SQL_TABLES_TO_CLASSES[subtable]
                    if subtable in MULTIVALUE:
                        cursor.execute(
                            f"SELECT * FROM {subtable_cls._sql_table_name.default} WHERE source_id = %s", (id_,))
                        list_ = [dict(zip(subtable_cls._sql_order.default, t))
                                 for t in cursor.fetchall()]
                        if len(list_) > 0:
                            args[subtable] = list_
                    else:
                        cursor.execute(
                            f"SELECT * FROM {subtable_cls._sql_table_name.default} WHERE source_id = %s", (id_,))
                        t = cursor.fetchone()
                        if t is not None:
                            args[subtable] = dict(
                                zip(subtable_cls._sql_order.default, t))
            return Source(**args)