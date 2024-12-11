"""Test institutions module."""
# pylint: disable=R0913
import re

import pytest
from hypothesis import given, provisional
from hypothesis import strategies as st
from openalex_types.institutions import (  # type: ignore
    Institution,
    InstitutionAssociatedInstitution,
    InstitutionCountByYear,
    InstitutionGeo,
    InstitutionIDs,
)
from pydantic import AnyUrl, ValidationError

DATE_FMT = r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?\b"


@given(id_=st.text(),
       ror=st.one_of(st.none(), st.text()),
       country_code=st.sampled_from(["US", "CA", "MX"]),
       type_=st.one_of(st.none(), st.text()),
       homepage_url=st.one_of(st.none(), provisional.urls()),
       image_url=provisional.urls(),
       image_thumbnail_url=provisional.urls(),
       display_name_acronyms=st.lists(st.text()),
       display_name_alternatives=st.one_of(st.none(), st.lists(st.text())),
       works_count=st.integers(),
       cited_by_count=st.one_of(st.none(), st.integers()),
       works_api_url=provisional.urls(),
       updated_date=st.datetimes(timezones=st.timezones()),
       )
def test_inst_no_other_objs(
    id_,
    ror,
    country_code,
    type_,
    homepage_url,
    image_url,
    image_thumbnail_url,
    display_name_acronyms,
    display_name_alternatives,
    works_count,
    cited_by_count,
    works_api_url,
    updated_date,
):
    """Test Institution."""
    inst = Institution(
        id=id_,
        ror=ror,
        country_code=country_code,
        type=type_,
        homepage_url=homepage_url,
        image_url=image_url,
        image_thumbnail_url=image_thumbnail_url,
        display_name_acronyms=display_name_acronyms,
        display_name_alternatives=display_name_alternatives,
        works_count=works_count,
        cited_by_count=cited_by_count,
        works_api_url=works_api_url,
        updated_date=updated_date,
    )
    assert inst.id == id_
    assert inst.ror == ror
    assert inst.country_code == country_code
    assert inst.type == type_
    if homepage_url:
        assert isinstance(inst.homepage_url, AnyUrl)
    assert isinstance(inst.image_url, AnyUrl)
    assert isinstance(inst.image_thumbnail_url, AnyUrl)
    assert inst.display_name_acronyms == display_name_acronyms
    assert inst.display_name_alternatives == display_name_alternatives
    assert inst.works_count == works_count
    assert inst.cited_by_count == cited_by_count
    assert isinstance(inst.works_api_url, AnyUrl)
    assert re.match(DATE_FMT, inst.updated_date)
    assert isinstance(inst, Institution)


@given(id_=st.text(),
       openalex=st.one_of(st.none(), st.text()),
       ror=st.text(),
       wikidata=st.text(),
       wikipedia=st.text(),
       mag=st.one_of(st.none(), st.integers()),
       )
def test_inst_ids(id_, openalex, ror, wikidata, wikipedia, mag):
    """Test InstitutionIDs."""
    inst_ids = InstitutionIDs(
        institution_id=id_,
        openalex=openalex,
        ror=ror,
        wikidata=wikidata,
        wikipedia=wikipedia,
        mag=mag,
    )
    assert inst_ids.institution_id == id_
    assert inst_ids.openalex == openalex
    assert inst_ids.ror == ror
    assert inst_ids.wikidata == wikidata
    assert inst_ids.wikipedia == wikipedia
    assert inst_ids.mag == mag
    assert isinstance(inst_ids, InstitutionIDs)


@given(
    institution_id=st.text(),
    city=st.one_of(st.none(), st.text()),
    geonames_city_id=st.one_of(st.none(), st.text()),
    region=st.one_of(st.none(), st.text()),
    country_code=st.sampled_from(["US", "CA", "MX"]),
    country=st.one_of(st.none(), st.text()),
    latitude=st.one_of(st.none(), st.floats(allow_nan=False)),
    longitude=st.one_of(st.none(), st.floats(allow_nan=False)),
)
def test_inst_geo(institution_id,
                  city, geonames_city_id, region, country_code, country, latitude, longitude):
    """Test InstitutionGeo."""
    inst_geo = InstitutionGeo(
        institution_id=institution_id,
        city=city,
        geonames_city_id=geonames_city_id,
        region=region,
        country_code=country_code,
        country=country,
        latitude=latitude,
        longitude=longitude,
    )
    assert inst_geo.institution_id == institution_id
    assert inst_geo.city == city
    assert inst_geo.geonames_city_id == geonames_city_id
    assert inst_geo.region == region
    assert inst_geo.country_code == country_code
    assert inst_geo.country == country
    assert inst_geo.latitude == latitude
    assert inst_geo.longitude == longitude
    assert isinstance(inst_geo, InstitutionGeo)


@given(
    institution_id=st.text(),
    year=st.integers(),
    works_count=st.one_of(st.none(), st.integers()),
    cited_by_count=st.integers(),
)
def test_inst_count(institution_id, year, works_count, cited_by_count):
    """Test InstitutionCountByYear."""
    inst_count = InstitutionCountByYear(
        institution_id=institution_id,
        year=year,
        works_count=works_count,
        cited_by_count=cited_by_count,
    )
    assert inst_count.institution_id == institution_id
    assert inst_count.year == year
    assert inst_count.works_count == works_count
    assert inst_count.cited_by_count == cited_by_count
    assert isinstance(inst_count, InstitutionCountByYear)


def test_inst_count_no_year():
    """Test Institution Count No Year."""
    with pytest.raises(ValidationError):
        InstitutionCountByYear(institution_id="http://l:1")


@given(institution_id=st.text(),
       associated_institution_id=st.text(min_size=2),
       relationship=st.text(),
       )
def test_inst_associated_inst_no_alias(institution_id, associated_institution_id, relationship):
    """Test InstitutionAssociatedInstitution no alias.
      (i.e `associated_institution` instead of `id`)."""
    inst_assoc_inst = InstitutionAssociatedInstitution(
        institution_id=institution_id,
        associated_institution_id=associated_institution_id,
        relationship=relationship,
    )
    assert inst_assoc_inst.institution_id == institution_id
    assert inst_assoc_inst.associated_institution_id == associated_institution_id
    assert inst_assoc_inst.relationship == relationship
    assert isinstance(inst_assoc_inst, InstitutionAssociatedInstitution)


@given(institution_id=st.text(),
       associated_institution_id=st.text(),
       relationship=st.text(),
       )
def test_inst_associated_inst(institution_id, associated_institution_id, relationship):
    """Test InstitutionAssociatedInstitution."""
    inst_assoc_inst = InstitutionAssociatedInstitution(
        institution_id=institution_id,
        id=associated_institution_id,
        relationship=relationship,
    )
    assert inst_assoc_inst.institution_id == institution_id
    assert inst_assoc_inst.associated_institution_id == associated_institution_id
    assert inst_assoc_inst.relationship == relationship
    assert isinstance(inst_assoc_inst, InstitutionAssociatedInstitution)


@given(id_=st.text(),
       ror=st.one_of(st.none(), st.text()),
       country_code=st.sampled_from(["US", "CA", "MX"]),
       type_=st.one_of(st.none(), st.text()),
       homepage_url=st.one_of(st.none(), provisional.urls()),
       image_url=provisional.urls(),
       image_thumbnail_url=provisional.urls(),
       display_name_acronyms=st.lists(st.text()),
       display_name_alternatives=st.one_of(st.none(), st.lists(st.text())),
       works_count=st.integers(),
       cited_by_count=st.one_of(st.none(), st.integers()),
       works_api_url=provisional.urls(),
       updated_date=st.datetimes(timezones=st.timezones()),
       city=st.one_of(st.none(), st.text()),
       geonames_city_id=st.one_of(st.none(), st.text()),
       region=st.one_of(st.none(), st.text()),
       country_code=st.sampled_from(["US", "CA", "MX"]),
       country=st.one_of(st.none(), st.text()),
       latitude=st.one_of(st.none(), st.floats(allow_nan=False)),
       longitude=st.one_of(st.none(), st.floats(allow_nan=False)),
       openalex=st.one_of(st.none(), st.text()),
       wikidata=st.text(),
       wikipedia=st.text(),
       mag=st.one_of(st.none(), st.integers()),
       counts_by_year=st.lists(st.builds(
           dict,
           year=st.integers(),
           works_count=st.integers(),
           cited_by_count=st.one_of(st.none(), st.integers()))),
       associated_institutions=st.lists(st.builds(
           dict,
           associated_institution_id=st.text(),
           relationship=st.text(),
       ))
       )
def test_inst_complete(
    id_,
    ror,
    country_code,
    type_,
    homepage_url,
    image_url,
    image_thumbnail_url,
    display_name_acronyms,
    display_name_alternatives,
    works_count,
    cited_by_count,
    works_api_url,
    updated_date,
    city,
    geonames_city_id,
    region,
    country_codes,
    country,
    latitude,
    longitude,
    openalex,
    wikidata,
    wikipedia,
    mag,
    counts_by_year,
    associated_institutions,
):
    """Test Institution."""
    inst = Institution(
        **{"id": id_,
           "ror": ror,
           "country_code": country_code,
           "type": type_,
           "homepage_url": homepage_url,
           "image_url": image_url,
           "image_thumbnail_url": image_thumbnail_url,
           "display_name_acronyms": display_name_acronyms,
           "display_name_alternatives": display_name_alternatives,
           "works_count": works_count,
           "cited_by_count": cited_by_count,
           "works_api_url": works_api_url,
           "updated_date": updated_date,
           "geo": {
               "city": city,
               "geonames_city_id": geonames_city_id,
               "region": region,
               "country_code": country_codes,
               "country": country,
               "latitude": latitude,
               "longitude": longitude,
           },
           "ids": {
               "openalex": openalex,
               "wikidata": wikidata,
               "wikipedia": wikipedia,
               "mag": mag,
           },
           "counts_by_year": counts_by_year,
           "associated_institutions": associated_institutions,
           }
    )
    assert inst.id == id_
    assert inst.ror == ror
    assert inst.country_code == country_code
    assert inst.type == type_
    if homepage_url:
        assert isinstance(inst.homepage_url, AnyUrl)
    assert isinstance(inst.image_url, AnyUrl)
    assert isinstance(inst.image_thumbnail_url, AnyUrl)
    assert inst.display_name_acronyms == display_name_acronyms
    assert inst.display_name_alternatives == display_name_alternatives
    assert inst.works_count == works_count
    assert inst.cited_by_count == cited_by_count
    assert isinstance(inst.works_api_url, AnyUrl)
    assert re.match(DATE_FMT, inst.updated_date)
    for count_by_year in inst.counts_by_year:  # pylint: disable=not-an-iterable
        assert isinstance(count_by_year, InstitutionCountByYear)
        assert count_by_year.institution_id == id_
    for as_inst in inst.associated_institutions:  # pylint: disable=not-an-iterable
        assert isinstance(as_inst, InstitutionAssociatedInstitution)
        assert as_inst.institution_id == id_
        assert isinstance(as_inst.associated_institution_id, str)
    assert inst.ids.institution_id == id_
    assert inst.geo.institution_id == id_
