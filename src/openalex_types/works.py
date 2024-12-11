"""Works Models."""
# pylint: disable=too-few-public-methods, W1203, R1720, E1101, W0212, R1705

import logging
from typing import Literal, Optional

from openalex_types.authors import DehydratedAuthor
from openalex_types.common import Date8601, OpenAlexObject, SQLTable
from openalex_types.institutions import DehydratedInstitution
from openalex_types.sources import Source
from openalex_types.utils import check
from psycopg import Connection
from pydantic import (
    AliasChoices,
    BaseModel,
    Field,
    computed_field,
    field_validator,
    model_validator,
)

logger = logging.getLogger("openalex-types.works")


def _construct_abstract_from_index(index: dict) -> str:
    """Construct abstract from inverted index."""
    if index is None:
        return ""
    list_ = [int(y) for x in index.values() for y in x]
    if len(list_) == 0:
        return ""
    max_ = max(list_)
    abs_ = [""] * (max_ + 1)
    for word, positions in index.items():
        for position in positions:
            abs_[position] = word
    return " ".join(abs_)


def _construct_dict_from_id(work_id: str, other_id: str) -> dict:
    """Construct dict from ID."""
    return {"id": other_id, "work_id": work_id}


class BaseWorkLocation(BaseModel):
    """Work Location."""
    work_id: Optional[str] = None
    source_id: Optional[str] = None
    # landing_page_url: Optional[AnyUrl] = None
    # NOTE: pydantic does not like some urls,
    # like 'www.lingref.com/cpp/galana/2/paper1559.pdf'
    # so we use str instead of AnyUrl
    landing_page_url: Optional[str] = None
    pdf_url: Optional[str] = None
    is_oa: Optional[bool] = None
    version: Optional[Literal["publishedVersion",
                              "acceptedVersion", "submittedVersion"]] = None
    license: Optional[str] = None
    source: Optional[Source] = None
    is_accepted: Optional[bool] = None
    is_published: Optional[bool] = None
    _sql_order = ["work_id", "source_id", "landing_page_url",
                  "pdf_url", "is_oa", "version", "license"]

    @model_validator(mode="after")
    def _populate_source_id(self):
        """Populate source_id."""
        if self.source is not None:
            self.source_id = self.source.id
        return self


class WorkPrimaryLocation(BaseWorkLocation, SQLTable):
    """Primary Location, needed for SQL table operations."""
    _sql_table_name = "openalex.works_primary_locations"


class WorkLocation(BaseWorkLocation, SQLTable):
    """Work Location, needed for SQL table operations."""
    _sql_table_name = "openalex.works_locations"


class WorkBestOALocation(BaseWorkLocation, SQLTable):
    """Work Best OA Location, needed for SQL table operations."""
    _sql_table_name = "openalex.works_best_oa_locations"


class WorkAuthorship(BaseModel, SQLTable):
    """Work Authorship."""
    work_id: Optional[str] = None
    author_position: Optional[Literal["first", "last", "middle"]] = None
    author_id: Optional[str] = None
    institution_id: Optional[str] = None
    raw_affiliation_string: Optional[str] = None
    author: Optional[DehydratedAuthor] = None
    countries: Optional[list[str]] = None
    institutions: Optional[list[DehydratedInstitution]] = None
    is_corresponding: Optional[bool] = None
    raw_author_name: Optional[str] = None
    _sql_table_name = "openalex.works_authorships"
    _sql_order = ["work_id", "author_position", "author_id", "institution_id",
                  "raw_affiliation_string"]
    # NOTE: institution_id, docs have institutions [list]
    # NOTE: raw_affiliation_string, docs have raw_affiliation_strings [list]

    @model_validator(mode="before")
    def _replicate_id(self):
        """Replicate author_id."""
        if check("author", self):
            self["author_id"] = self["author"]["id"]
        return self

    @model_validator(mode="after")
    def _check_author_id(self):
        """Check author_id."""
        if self.author is not None:
            if self.author.id != self.author_id:
                raise ValueError("author_id must match author.id")
        return self


class WorkBiblio(BaseModel, SQLTable):
    """Work Bibliographic Information."""
    work_id: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    first_page: Optional[str] = None
    last_page: Optional[str] = None
    _sql_table_name = "openalex.works_biblio"
    _sql_order = ["work_id", "volume", "issue", "first_page", "last_page"]


class WorkTopic(BaseModel, SQLTable):
    """Work Topic."""
    work_id: Optional[str] = Field(
        None, validation_alias=AliasChoices("id", "work_id"))
    topic_id: Optional[str] = None
    score: Optional[float] = None
    subfield: Optional[dict] = None
    _sql_table_name = "openalex.works_topics"
    _sql_order = ["work_id", "topic_id", "score"]


class WorkConcept(BaseModel, SQLTable):
    """Work Concept."""
    work_id: Optional[str] = None
    concept_id: Optional[str] = None
    score: Optional[float] = None
    _sql_table_name = "openalex.works_concepts"
    _sql_order = ["work_id", "concept_id", "score"]


class WorkIDs(BaseModel, SQLTable):
    """Work ID."""
    work_id: str
    openalex: Optional[str] = None
    doi: Optional[str] = None
    mag: Optional[int] = None
    pmid: Optional[str] = None
    pmcid: Optional[str] = None
    _sql_table_name = "openalex.works_ids"
    _sql_order = ["work_id", "openalex", "doi", "mag", "pmid", "pmcid"]


class WorkMesh(BaseModel, SQLTable):
    """Work Mesh."""
    work_id: Optional[str] = None
    descriptor_ui: Optional[str] = None
    descriptor_name: Optional[str] = None
    qualifier_ui: Optional[str] = None
    qualifier_name: Optional[str] = None
    is_major_topic: Optional[bool] = None
    _sql_table_name = "openalex.works_mesh"
    _sql_order = ["work_id", "descriptor_ui", "descriptor_name",
                  "qualifier_ui", "qualifier_name", "is_major_topic"]


class NomicEmbedText768(BaseModel, SQLTable):
    """Embedding Nomic Embed Text Size 768."""
    work_id: Optional[str] = None
    # model_name: Optional[str] = None
    embedding: Optional[list[float]] = None
    _sql_table_name = "openalex.nomic_embed_text_768"
    _sql_order = ["work_id", "embedding"]


class WorkOpenAccess(BaseModel, SQLTable):
    """Work Open Access."""
    work_id: Optional[str] = None
    is_oa: Optional[bool] = None
    oa_status: Optional[str] = None
    oa_url: Optional[str] = None
    any_repository_has_fulltext: Optional[bool] = None
    _sql_table_name = "openalex.works_open_access"
    _sql_order = ["work_id", "is_oa", "oa_status", "oa_url",
                  "any_repository_has_fulltext"]


class WorkReferencedWork(BaseModel, SQLTable):
    """Work Referenced Work."""
    work_id: Optional[str] = None
    referenced_work_id: Optional[str] = Field(
        None, validation_alias=AliasChoices("id", "referenced_work_id"))
    _sql_table_name = "openalex.works_referenced_works"
    _sql_order = ["work_id", "referenced_work_id"]


class WorkRelatedWork(BaseModel, SQLTable):
    """Work Related Work."""
    work_id: Optional[str] = None
    related_work_id: Optional[str] = Field(
        None, validation_alias=AliasChoices("id", "related_work_id"))
    _sql_table_name = "openalex.works_related_works"
    _sql_order = ["work_id", "related_work_id"]


class WorkAPC(BaseModel):
    """Work APC (article processing charge)."""
    value: Optional[int] = None
    currency: Optional[str] = None
    provenance: Optional[str] = None
    value_usd: Optional[int] = None


class WorkCountByYear(BaseModel):
    """Work Count by Year."""
    year: int
    cited_by_count: int


class WorkGrant(BaseModel):
    """Grant for Work Object."""
    funder: Optional[str] = None
    funder_display_name: Optional[str] = None
    award_id: Optional[str] = None


class WorkKeyword(BaseModel):
    """Work Keyword."""
    id: Optional[str] = None
    display_name: Optional[str] = None
    score: Optional[float] = None
    # TODO: optional?


class WorkSDG(BaseModel):
    """Work Sustainable Development Goals."""
    id: Optional[str] = None
    display_name: Optional[str] = None
    score: Optional[float] = None


SQL_TABLES_TO_CLASSES = {
    "primary_location": WorkPrimaryLocation,
    "locations": WorkLocation,
    "best_oa_location": WorkBestOALocation,
    "authorships": WorkAuthorship,
    "biblio": WorkBiblio,
    "topics": WorkTopic,
    "concepts": WorkConcept,
    "ids": WorkIDs,
    "mesh": WorkMesh,
    "open_access": WorkOpenAccess,
    "referenced_works": WorkReferencedWork,
    "related_works": WorkRelatedWork
}
# which tables have multiple values (list)?
MULTIVALUE = ["locations", "authorships", "topics", "concepts", "mesh",
              "referenced_works", "related_works"]


class Work(OpenAlexObject, SQLTable, validate_assignment=True):
    """OpenAlex Works."""
    doi: Optional[str] = None
    title: Optional[str] = None
    display_name: Optional[str] = None
    publication_year: Optional[int] = None
    publication_date: Optional[Date8601] = None
    type: Optional[str] = None
    cited_by_count: Optional[int] = None
    is_retracted: Optional[bool] = None
    is_paratext: Optional[bool] = None
    cited_by_api_url: Optional[str] = None
    abstract_inverted_index: Optional[dict] = None
    language: Optional[str] = None
    ids: Optional[WorkIDs] = None
    locations: Optional[list[WorkLocation]] = None
    authorships: Optional[list[WorkAuthorship]] = None
    biblio: Optional[WorkBiblio] = None
    topics: Optional[list[WorkTopic]] = None
    concepts: Optional[list[WorkConcept]] = None
    mesh: Optional[list[WorkMesh]] = None
    open_access: Optional[WorkOpenAccess] = None
    referenced_works: Optional[list[WorkReferencedWork]] = None
    related_works: Optional[list[WorkRelatedWork]] = None
    apc_list: Optional[WorkAPC] = None
    apc_paid: Optional[WorkAPC] = None
    best_oa_location: Optional[WorkBestOALocation] = None
    corresponding_author_ids: Optional[list[str]] = None
    corresponding_institution_ids: Optional[list[str]] = None
    countries_distinct_count: Optional[int] = None
    created_date: Optional[Date8601] = None
    counts_by_year: Optional[list[WorkCountByYear]] = None
    fulltext_origin: Optional[Literal["pdf", "ngrams"]] = None
    fwci: Optional[float] = None
    grants: Optional[list[WorkGrant]] = None
    has_fulltext: Optional[bool] = None
    # indexed_in: Optional[list[Literal["arxiv", "crossref", "pubmed", "doaj"]]] = None
    # NOTE: docs say possible values are arxiv, crossref, pubmed, doaj, but
    # objects have more values, like 'datacite'
    indexed_in: Optional[list[str]] = None
    institutions_distinct_count: Optional[int] = None
    keywords: Optional[list[WorkKeyword]] = None
    license: Optional[str] = None
    locations_count: Optional[int] = None
    primary_location: Optional[WorkPrimaryLocation] = None
    primary_topic: Optional[WorkTopic] = None
    sustainable_development_goals: Optional[list[WorkSDG]] = None
    type_crossref: Optional[str] = None
    updated_date: Optional[Date8601] = None
    abstract_embedding_nomic_embed_text: Optional[NomicEmbedText768] = None
    _sql_table_name = "openalex.works"
    _sql_order = ["id", "doi", "title", "display_name", "publication_year",
                  "publication_date", "type",
                  "cited_by_count", "is_retracted", "is_paratext",
                  "cited_by_api_url", "abstract_inverted_index",
                  "language"
                  ]
    _sql_subtables = ["primary_location", "locations", "best_oa_location",
                      "authorships", "biblio", "topics", "concepts", "ids",
                      "mesh", "open_access", "referenced_works", "related_works"]
    #   "abstract_embedding_nomic_embed_text"]

    @computed_field  # type: ignore[misc]
    @property
    def abstract(self) -> str | None:
        """Abstract as plain-text."""
        if self.abstract_inverted_index is None:
            return None
        return _construct_abstract_from_index(self.abstract_inverted_index)

    @model_validator(mode="before")
    def _replicate_id_1(self):
        """Replicate work_id in 'subtables'."""
        if check("counts_by_year", self):
            for count_by_year in self["counts_by_year"]:
                count_by_year["author_id"] = self["id"]
        # replicate in ids
        if check("ids", self):
            self["ids"]["work_id"] = self["id"]
        if check("locations", self):
            for location in self["locations"]:
                location["work_id"] = self["id"]
        if check("authorships", self):
            for authorship in self["authorships"]:
                authorship["work_id"] = self["id"]
        if check("biblio", self):
            self["biblio"]["work_id"] = self["id"]
        return self

    @model_validator(mode="before")
    def _replicate_id_2(self):
        """Replicate IDs in 'subtables'."""
        if check("topics", self):
            for topic in self["topics"]:
                topic["work_id"] = self["id"]
        if check("concepts", self):
            for concept in self["concepts"]:
                concept["work_id"] = self["id"]
        if check("mesh", self):
            for mesh in self["mesh"]:
                mesh["work_id"] = self["id"]
        if check("open_access", self):
            self["open_access"]["work_id"] = self["id"]
        return self

    @model_validator(mode="before")
    def _replicate_id_3(self):
        """Replicate IDs in 'subtables'."""
        if check("best_oa_location", self):
            self["best_oa_location"]["work_id"] = self["id"]
        if check("primary_location", self):
            self["primary_location"]["work_id"] = self["id"]
        if check("locations", self):
            for location in self["locations"]:
                location["work_id"] = self["id"]
        return self

    @model_validator(mode="before")
    def _work_id_ref_related(self):
        """Appropriately format reference and related works as dict."""
        if check("related_works", self):
            for n, related_work in enumerate(self["related_works"]):
                self["related_works"][n] = _construct_dict_from_id(
                    self["id"], related_work)
        if check("referenced_works", self):
            for n, referenced_work in enumerate(self["referenced_works"]):
                self["referenced_works"][n] = _construct_dict_from_id(
                    self["id"], referenced_work)
        return self

    @model_validator(mode="before")
    def _flatten_authorships(self):
        """Flatten authorships, they can have multiple institutions."""
        # NOTE: this will create multiple
        # authorships for author X that has multiple institutions
        if check("authorships", self):
            authorships = []
            for authorship in self["authorships"]:
                if not check("institutions", authorship):
                    authorships.append(authorship)
                    continue
                if authorship["institutions"] is None or len(authorship["institutions"]) == 0:
                    authorships.append(authorship)
                    continue
                for institution in authorship["institutions"]:
                    authorship_ = authorship.copy()
                    authorship_["institution_id"] = institution["id"]
                    authorship_["institutions"] = [institution]
                    authorships.append(authorship_)
            self["authorships"] = authorships
        return self

    @field_validator("best_oa_location")
    @classmethod
    def _validate_best_oa_location(cls, value):
        """Validate best_oa_location."""
        if value is None:
            return value
        if not value.is_oa:
            raise ValueError("best_oa_location must be OA.")
        return value

    @field_validator("abstract_inverted_index")
    @classmethod
    def _validate_abstract_inverted_index(cls, value):
        """Validate abstract_inverted_index."""
        if value is None:
            return value
        if len(value) == 0:
            return None
        return value

    @staticmethod
    def from_sql(t: tuple, conn: Optional[Connection] = None,
                 subtables: Optional[dict] = None) -> "Work":
        """Create Work from SQL."""
        args = dict(zip(Work._sql_order.default, t))  # type: ignore
        if conn is None:
            if subtables is None:  # only Work object
                return Work(**args)
            else:  # Work object with subtables already queried
                for subtable in Work._sql_subtables.default:  # type: ignore
                    if subtable in subtables:
                        if subtable in ["referenced_works", "related_works"]:
                            args[subtable] = [t[1]
                                              for t in subtables[subtable]]
                        elif subtable in MULTIVALUE:
                            args[subtable] = [dict(zip(
                                SQL_TABLES_TO_CLASSES[subtable]._sql_order.default, t)  # type: ignore
                            )
                                for t in subtables[subtable]]
                        else:
                            args[subtable] = dict(zip(
                                SQL_TABLES_TO_CLASSES[subtable]._sql_order.default, subtables[subtable])  # type: ignore
                            )
            return Work(**args)
        else:  # Query everything, connection is provided
            id_ = t[0]
            with conn.cursor() as cursor:
                for subtable in Work._sql_subtables.default:  # type: ignore
                    subtable_cls = SQL_TABLES_TO_CLASSES[subtable]
                    if subtable in MULTIVALUE:
                        cursor.execute(
                            f"SELECT * FROM {subtable_cls._sql_table_name.default} WHERE work_id = %s", (id_,))  # type: ignore
                        if subtable in ["referenced_works", "related_works"]:
                            list_ = [t[1] for t in cursor.fetchall()]
                        else:
                            list_ = [dict(zip(subtable_cls._sql_order.default, t))  # type: ignore
                                     for t in cursor.fetchall()]
                        if len(list_) > 0:
                            args[subtable] = list_
                    else:
                        cursor.execute(
                            f"SELECT * FROM {subtable_cls._sql_table_name.default} WHERE work_id = %s", (id_,))  # type: ignore
                        t = cursor.fetchone()  # type: ignore
                        if t is not None:
                            args[subtable] = dict(
                                zip(subtable_cls._sql_order.default, t))  # type: ignore
            return Work(**args)
