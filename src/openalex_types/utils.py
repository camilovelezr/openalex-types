"""Utilities for OpenAlex types."""


def check(arg_name: str, obj: dict) -> bool:
    """Check if arg_name in obj and is not None."""
    if arg_name not in obj or obj[arg_name] is None:
        return False
    return True


# For easy cleanup of SQL tables, for testing
SQL_TABLE_NAMES = {
    "works": [
        "openalex.nomic_embed_text_768",
        "openalex.works",
        "openalex.works_primary_locations",
        "openalex.works_locations",
        "openalex.works_authorships",
        "openalex.works_biblio",
        "openalex.works_topics",
        "openalex.works_concepts",
        "openalex.works_ids",
        "openalex.works_mesh",
        "openalex.works_open_access",
        "openalex.works_referenced_works",
        "openalex.works_related_works",
    ],
    "authors": [
        "openalex.authors",
        "openalex.authors_counts_by_year",
        "openalex.authors_ids",
    ],
    "topics": [
        "openalex.topics",
    ],
    "concepts": [
        "openalex.concepts",
        "openalex.concepts_ancestors",
        "openalex.concepts_counts_by_year",
        "openalex.concepts_ids",
        "openalex.concepts_related_concepts",
    ],
    "institutions": [
        "openalex.institutions",
        "openalex.institutions_associated_institutions",
        "openalex.institutions_counts_by_year",
        "openalex.institutions_geo",
        "openalex.institutions_ids",
    ],
    "publishers": [
        "openalex.publishers",
        "openalex.publishers_counts_by_year",
        "openalex.publishers_ids",
    ],
    "sources": [
        "openalex.sources",
        "openalex.sources_counts_by_year",
        "openalex.sources_ids",
    ]
}
