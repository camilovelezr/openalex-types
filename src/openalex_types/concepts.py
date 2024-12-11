"""Concepts Models."""
# NOTE: These have been deprecated in favor of Topics.
# pylint: disable=too-few-public-methods

from typing import Optional

from openalex_types.common import BaseCountByYear, DateTimeNoTZ, OpenAlexObject, SQLTable
from openalex_types.utils import check
from psycopg import Connection
from pydantic import AliasChoices, BaseModel, Field, model_validator, field_validator


class ConceptAncestor(BaseModel, SQLTable):
    """OpenAlex Concept Ancestors."""
    concept_id: Optional[str] = None
    ancestor_id: Optional[str] = None
    ancestor_id: Optional[str] = Field(
        None, validation_alias=AliasChoices("id", "ancestor_id"))
    _sql_table_name = "openalex.concepts_ancestors"
    _sql_order = ["concept_id", "ancestor_id"]


class ConceptCountByYear(BaseCountByYear, SQLTable):
    """Concept Count by Year."""
    concept_id: str
    _sql_table_name = "openalex.concepts_counts_by_year"
    _sql_order = ["concept_id", "year", "works_count",
                  "cited_by_count", "oa_works_count"]


class ConceptIDs(BaseModel, SQLTable):
    """Concept ID."""
    concept_id: str
    openalex: Optional[str] = None
    wikidata: Optional[str] = None
    wikipedia: Optional[str] = None
    umls_aui: Optional[list[str]] = None
    umls_cui: Optional[list[str]] = None
    mag: Optional[int] = None
    _sql_table_name = "openalex.concepts_ids"
    _sql_order = ["concept_id", "openalex", "wikidata", "wikipedia",
                    "umls_aui", "umls_cui", "mag"]


class ConceptRelatedConcept(BaseModel, SQLTable):
    """Related Concepts."""
    concept_id: Optional[str] = None
    related_concept_id: Optional[str] = Field(
        None, validation_alias=AliasChoices("id", "related_concept_id"))
    score: Optional[float] = None
    _sql_table_name = "openalex.concepts_related_concepts"
    _sql_order = ["concept_id", "related_concept_id", "score"]

SQL_TABLES_TO_CLASSES = {
    "ancestors": ConceptAncestor,
    "related_concepts": ConceptRelatedConcept,
    "counts_by_year": ConceptCountByYear,
    "ids": ConceptIDs
}
# which tables have multiple values (list)?
MULTIVALUE = ["ancestors", "related_concepts", "counts_by_year"]

class Concept(OpenAlexObject, SQLTable):
    """OpenAlex Concepts."""
    wikidata: Optional[str] = None
    display_name: Optional[str] = None
    level: Optional[int] = None
    description: Optional[str] = None
    works_count: Optional[int] = None
    cited_by_count: Optional[int] = None
    image_url: Optional[str] = None
    image_thumbnail_url: Optional[str] = None
    works_api_url: Optional[str] = None
    updated_date: Optional[DateTimeNoTZ] = None
    ancestors: Optional[list[ConceptAncestor]] = None
    related_concepts: Optional[list[ConceptRelatedConcept]] = None
    counts_by_year: Optional[list[ConceptCountByYear]] = None
    ids: Optional[ConceptIDs] = None
    _sql_table_name = "openalex.concepts"
    _sql_order = ["id", "wikidata", "display_name", "level", "description",
                  "works_count", "cited_by_count", "image_url", "image_thumbnail_url",
                  "works_api_url", "updated_date"]
    _sql_subtables = ["ancestors", "related_concepts", "counts_by_year", "ids"]

    @model_validator(mode="before")
    def _replicate_id(self):
        """Replicate self.id."""
        if check("ids", self):
            self["ids"]["concept_id"] = self["id"]
        if check("counts_by_year", self):
            for count in self["counts_by_year"]:
                count["concept_id"] = self["id"]
        if check("ancestors", self):
            for ancestor in self["ancestors"]:
                ancestor["concept_id"] = self["id"]
        if check("related_concepts", self):
            for related in self["related_concepts"]:
                related["concept_id"] = self["id"]
        return self

    @field_validator("ancestors", "related_concepts", "counts_by_year")
    @classmethod
    def _check_not_empty(cls, val: list) -> list | None:
        """Check if list is not empty."""
        if val is None or len(val) == 0:
            return None
        return val

    @staticmethod
    def from_sql(t: tuple, conn: Optional[Connection] = None,
                 subtables: Optional[dict] = None) -> "Concept":
        """Create Concept from SQL."""
        args = dict(zip(Concept._sql_order.default, t))  # type: ignore
        if conn is None:
            if subtables is None:  # only Concept object
                return Concept(**args)
            else:  # Concept object with subtables already queried
                for subtable in Concept._sql_subtables.default:  # type: ignore
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
            return Concept(**args)
        else:  # Query everything, connection is provided
            id_ = t[0]
            with conn.cursor() as cursor:
                for subtable in Concept._sql_subtables.default:  # type: ignore
                    subtable_cls = SQL_TABLES_TO_CLASSES[subtable]
                    if subtable in MULTIVALUE:
                        cursor.execute(
                            f"SELECT * FROM {subtable_cls._sql_table_name.default} WHERE concept_id = %s", (id_,))  # type: ignore
                        list_ = [dict(zip(subtable_cls._sql_order.default, t))  # type: ignore
                                 for t in cursor.fetchall()]
                        if len(list_) > 0:
                            args[subtable] = list_
                    else:
                        cursor.execute(
                            f"SELECT * FROM {subtable_cls._sql_table_name.default} WHERE concept_id = %s", (id_,))  # type: ignore
                        t = cursor.fetchone()
                        if t is not None:
                            args[subtable] = dict(
                                zip(subtable_cls._sql_order.default, t))  # type: ignore
            return Concept(**args)    
