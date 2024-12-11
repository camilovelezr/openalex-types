"""Test works module."""
# pylint: disable=R0913, E1133, R0914
import re

import pytest
from hypothesis import given, provisional, settings
from hypothesis import strategies as st
from openalex_types.works import (  # type: ignore
    Work,
    _construct_abstract_from_index,
    _construct_dict_from_id,
)
from pydantic import AnyUrl, ValidationError

DATE_FMT = r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?\b"

TEXT_EXAMPLE = "Accelerate discovery and advance organizational success through emerging technologies and renowned research talent. Working with Axle, our clients can deploy cutting-edge solutions and services that push the pace of progress and expand the limits of possibility. Advance. Accelerate. Achieve."

words = re.findall(r"\b[\w-]+\b[,\.]?", TEXT_EXAMPLE)

REVERSED_INDEX_EXAMPLE: dict[str, list[int]] = {}

for i, word in enumerate(words):
    if word not in REVERSED_INDEX_EXAMPLE:
        REVERSED_INDEX_EXAMPLE[word] = []
    REVERSED_INDEX_EXAMPLE[word].append(i)


def test_construct_abstract_from_index():
    """Test construct abstract from index."""
    assert _construct_abstract_from_index(
        REVERSED_INDEX_EXAMPLE) == TEXT_EXAMPLE


def test_construct_dict_from_id():
    """Test construct dict from ID."""
    assert _construct_dict_from_id("work_id", "other_id") == {
        "id": "other_id", "work_id": "work_id"}


@given(
    id_=st.text(min_size=1),
    doi=st.text(min_size=1),
    title=st.one_of(st.none(), st.text(min_size=1)),
    display_name=st.one_of(st.none(), st.text(min_size=1)),
    publication_year=st.one_of(st.none(), st.integers()),
    publication_date=st.dates(),
    type_=st.text(min_size=1),
    cited_by_count=st.one_of(st.none(), st.integers()),
    is_retracted=st.one_of(st.none(), st.booleans()),
    is_paratext=st.booleans(),
    cited_by_api_url=st.one_of(st.none(), provisional.urls()),
    abstract_inverted_index=st.builds(dict, st.lists(
        st.tuples(st.text(min_size=1), st.lists(st.integers())))),
    language=st.one_of(
        st.none(), st.text(min_size=1)),
    ids=st.builds(dict, openalex=st.text(min_size=1),
                  doi=st.text(min_size=1), mag=st.integers()),
    authorships=st.lists(st.builds(dict, author_id=st.text(min_size=1),
                                   author_position=st.text(), raw_affiliation_string=st.text(min_size=8))),
    biblio=st.builds(dict, volume=st.text(),
                     first_page=st.text(), last_page=st.text()),
    topics=st.lists(st.builds(dict, topic_id=st.text(
        min_size=1), score=st.floats())),
    concepts=st.lists(
        st.builds(dict, concept_id=st.text(min_size=1), score=st.floats())),
    mesh=st.lists(st.builds(dict, descriptor_ui=st.text(
        min_size=1), descriptor_name=st.text(min_size=1), is_major_topic=st.booleans(), qualifier_ui=st.text())),
    locations=st.lists(st.builds(dict, source_id=st.text(
        min_size=1), pdf_url=provisional.urls(), version=st.text(min_size=1))),
    open_access=st.builds(dict, is_oa=st.booleans(),
                          oa_status=st.text(min_size=1)),
    referenced_works=st.lists(st.text(min_size=5)),
    related_works=st.lists(st.text(min_size=5)),
)
def test_work(
    id_: str,
    doi: str,
    title: str,
    display_name: str,
    publication_year: int,
    publication_date: str,
    type_: str,
    cited_by_count: int,
    is_retracted: bool,
    is_paratext: bool,
    cited_by_api_url: AnyUrl,
    language: str,
    ids: list,
    authorships: list,
    biblio: dict,
    topics: list,
    concepts: list,
    mesh: list,
    abstract_inverted_index: dict,
    locations: list,
    related_works: list,
    referenced_works: list,
    open_access: dict,
):
    """Test Works."""
    w = Work(
        id=id_,
        doi=doi,
        title=title,
        display_name=display_name,
        publication_year=publication_year,
        publication_date=publication_date,
        type=type_,
        cited_by_count=cited_by_count,
        is_retracted=is_retracted,
        is_paratext=is_paratext,
        cited_by_api_url=cited_by_api_url,
        abstract_inverted_index=abstract_inverted_index,
        language=language,
        locations=locations,
        authorships=authorships,
        biblio=biblio,
        topics=topics,
        concepts=concepts,
        mesh=mesh,
        ids=ids,
        open_access=open_access,
        referenced_works=referenced_works,
        related_works=related_works,
    )
    assert w.id == id_
    assert w.ids.work_id == id_
    for concept in w.concepts:
        assert concept.work_id == id_
    for topic in w.topics:
        assert topic.work_id == id_
    for authorship in w.authorships:
        assert authorship.work_id == id_
    for location in w.locations:
        assert location.work_id == id_
    for m in w.mesh:
        assert m.work_id == id_
    assert w.biblio.work_id == id_
    for related_work in w.related_works:
        assert related_work.work_id == id_
        assert isinstance(related_work.related_work_id, str)
    for referenced_work in w.referenced_works:
        assert referenced_work.work_id == id_
        assert isinstance(referenced_work.referenced_work_id, str)
    assert w.open_access.work_id == id_
