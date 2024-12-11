"""Test authors module."""
import re

from hypothesis import given, provisional
from hypothesis import strategies as st
from openalex_types.authors import Author  # type: ignore

DATE_FMT = r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?\b"


@given(id_=st.text(),
       orcid=st.one_of(st.none(), st.text()),
       display_name=st.one_of(st.none(), st.text()),
       display_name_alternatives=st.one_of(
           st.none(), st.dictionaries(keys=st.text(), values=st.text())),
       works_count=st.one_of(st.none(), st.integers()),
       cited_by_count=st.integers(),
       last_known_institution=st.one_of(st.none(), st.text()),
       works_api_url=provisional.urls(),
       updated_date=st.datetimes(timezones=st.timezones())
       )
def test_author_obj(id_, orcid, display_name, display_name_alternatives,
                    works_count, cited_by_count, last_known_institution,
                    works_api_url, updated_date):
    """Test Author object."""
    author = Author(id=id_, orcid=orcid, display_name=display_name,
                    display_name_alternatives=display_name_alternatives,
                    works_count=works_count, cited_by_count=cited_by_count,
                    last_known_institution=last_known_institution,
                    works_api_url=works_api_url, updated_date=updated_date)

    assert author.id == id_
    assert re.match(DATE_FMT, author.updated_date)
