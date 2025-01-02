from importlib import resources

import pytest
from requests_mock import ANY

from parsers.archived import IN_AP


@pytest.fixture(autouse=True)
def mock_response(adapter):
    adapter.register_uri(
        ANY,
        ANY,
        text=resources.files("parsers.test.mocks").joinpath("IN_AP.html").read_text(),
    )


def test_fetch_production(session):
    data = IN_AP.fetch_production("IN-AP", session)
    assert data
    assert data["zoneKey"] == "IN-AP"
    assert data["source"] == "core.ap.gov.in"
    assert data["datetime"]
    assert data["production"]
    assert data["storage"]


def test_fetch_consumption(session):
    data = IN_AP.fetch_consumption("IN-AP", session)
    assert data
    assert data["zoneKey"] == "IN-AP"
    assert data["source"] == "core.ap.gov.in"
    assert data["datetime"]
    assert data["consumption"]
