"""Institutions Models."""
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
from openalex_types.sources import DehydratedSource, Source
from openalex_types.utils import check
from psycopg import Connection
from pydantic import AliasChoices, BaseModel, Field, model_validator, field_validator


class InstitutionAssociatedInstitution(BaseModel, SQLTable):
    """Associated Institutions."""
    institution_id: Optional[str] = None
    associated_institution_id: Optional[str] = Field(
        None, validation_alias=AliasChoices("id", "associated_institution_id"))
    relationship: Optional[str] = None
    country_code: Optional[CountryCode] = None
    display_name: Optional[str] = None
    ror: Optional[str] = None
    type: Optional[str] = None
    lineage: Optional[list[str]] = None
    _sql_table_name = "openalex.institutions_associated_institutions"
    _sql_order = ["institution_id", "associated_institution_id",
                  "relationship"]


class InstitutionCountByYear(BaseCountByYear, SQLTable):
    """Institution Count by Year."""
    institution_id: str
    _sql_table_name = "openalex.institutions_counts_by_year"
    _sql_order = ["institution_id", "year", "works_count",
                  "cited_by_count", "oa_works_count"]


class InstitutionGeo(BaseModel, SQLTable):
    """Institution Geo."""
    institution_id: str
    city: Optional[str] = None
    geonames_city_id: Optional[str] = None
    region: Optional[str] = None
    country_code: Optional[CountryCode] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    _sql_table_name = "openalex.institutions_geo"
    _sql_order = ["institution_id", "city", "geonames_city_id",
                  "region", "country_code", "country", "latitude", "longitude"]


class InstitutionIDs(BaseModel, SQLTable):
    """Institution ID."""
    institution_id: str
    openalex: Optional[str] = None
    ror: Optional[str] = None
    grid: Optional[str] = None
    wikidata: Optional[str] = None
    wikipedia: Optional[str] = None
    mag: Optional[int] = None
    _sql_table_name = "openalex.institutions_ids"
    _sql_order = ["institution_id", "openalex", "ror",
                  "grid", "wikipedia", "wikidata", "mag"]


class InstitutionInternationl(BaseModel):
    """Institution's display name in diff languages."""
    display_name: dict[str, str]


class DehydratedInstitution(OpenAlexObject):
    """OpenAlex Dehydrated Institutions."""
    country_code: Optional[CountryCode] = None
    display_name: Optional[str] = None
    ror: Optional[str] = None
    type: Optional[str] = None
    lineage: Optional[list[str]] = None

SQL_TABLES_TO_CLASSES = {
    "associated_institutions": InstitutionAssociatedInstitution,
    "counts_by_year": InstitutionCountByYear,
    "geo": InstitutionGeo,
    "ids": InstitutionIDs
}
# which tables have multiple values (list)?
MULTIVALUE = ["associated_institutions", "counts_by_year"]

class Institution(OpenAlexObject, SQLTable):
    """OpenAlex Institutions."""
    ror: Optional[str] = None
    lineage: Optional[list[str]] = None
    display_name: Optional[str] = None
    country_code: Optional[CountryCode] = None
    type: Optional[str] = None
    homepage_url: Optional[str] = None
    image_url: Optional[str] = None
    image_thumbnail_url: Optional[str] = None
    display_name_acronyms: Optional[list[str]] = None
    display_name_alternatives: Optional[list[str]] = None
    works_count: Optional[int] = None
    cited_by_count: Optional[int] = None
    works_api_url: Optional[str] = None
    updated_date: Optional[DateTimeNoTZ] = None
    geo: Optional[InstitutionGeo] = None
    counts_by_year: Optional[list[InstitutionCountByYear]] = None
    ids: Optional[InstitutionIDs] = None
    associated_institutions: Optional[list[InstitutionAssociatedInstitution]] = None
    created_date: Optional[Date8601] = None
    is_supersystem: Optional[bool] = None
    international: Optional[InstitutionInternationl] = None
    repositories: Optional[list[Source | DehydratedSource]] = None
    summary_stats: Optional[SummaryStats] = None
    roles: Optional[list[Role]] = None
    _sql_table_name = "openalex.institutions"
    _sql_order = ["id", "ror", "display_name", "country_code",
                  "type", "homepage_url", "image_url", "image_thumbnail_url",
                  "display_name_acronyms", "display_name_alternatives",
                  "works_count", "cited_by_count", "works_api_url",
                  "updated_date"]
    _sql_subtables = ["associated_institutions",
                      "counts_by_year", "geo", "ids"]

    @model_validator(mode="before")
    def _replicate_id(self):
        """Replicate institution_id in 'subtables'."""
        if check("geo", self):
            self["geo"]["institution_id"] = self["id"]
        if check("counts_by_year", self):
            for count_by_year in self["counts_by_year"]:
                count_by_year["institution_id"] = self["id"]
        # replicate in ids
        if check("ids", self):
            self["ids"]["institution_id"] = self["id"]
        if check("associated_institutions", self):
            for associated_institution in self["associated_institutions"]:
                associated_institution["institution_id"] = self["id"]
        return self

    @model_validator(mode="after")
    def _check_repositories(self):
        """Check host_org."""
        if self.repositories is not None:
            for repo in self.repositories:
                if repo.host_organization != self.id:
                    raise ValueError(
                        f"""
                        Repository with host id 
                        {repo.host_organization} doesn't match 
                        institution id {self.id}
                        """
                    )
        return self
    
    @field_validator("display_name_acronyms", "display_name_alternatives", "associated_institutions", "counts_by_year")
    @classmethod
    def _check_not_empty(cls, val: list) -> list | None:
        """Check if list is not empty."""
        if val is None or len(val) == 0:
            return None
        return val

    @staticmethod
    def from_sql(t: tuple, conn: Optional[Connection] = None,
                 subtables: Optional[dict] = None) -> "Institution":
        """Create Institution from SQL."""
        args = dict(zip(Institution._sql_order.default, t))  # type: ignore
        if conn is None:
            if subtables is None:  # only Institution object
                return Institution(**args)
            else:  # Institution object with subtables already queried
                for subtable in Institution._sql_subtables.default:  # type: ignore
                    if subtable in subtables:
                        if subtable in MULTIVALUE:
                            args[subtable] = [dict(zip(
                                SQL_TABLES_TO_CLASSES[subtable]._sql_order.default, t)  # type: ignore
                            )
                                for t in subtables[subtable]]
                        else:
                            args[subtable] = dict(zip(
                                SQL_TABLES_TO_CLASSES[subtable]._sql_order.default, subtables[subtable])  # type: ignore
                            )

            return Institution(**args)
        else:  # Query everything, connection is provided
            id_ = t[0]
            with conn.cursor() as cursor:
                for subtable in Institution._sql_subtables.default:  # type: ignore
                    subtable_cls = SQL_TABLES_TO_CLASSES[subtable]
                    if subtable in MULTIVALUE:
                        cursor.execute(
                            f"SELECT * FROM {subtable_cls._sql_table_name.default} WHERE institution_id = %s", (id_,))  # type: ignore
                        list_ = [dict(zip(subtable_cls._sql_order.default, t))  # type: ignore
                                 for t in cursor.fetchall()]
                        if len(list_) > 0:
                            args[subtable] = list_
                    else:
                        cursor.execute(
                            f"SELECT * FROM {subtable_cls._sql_table_name.default} WHERE institution_id = %s", (id_,))  # type: ignore
                        t = cursor.fetchone()
                        if t is not None:
                            args[subtable] = dict(
                                zip(subtable_cls._sql_order.default, t))  # type: ignore
            return Institution(**args)
