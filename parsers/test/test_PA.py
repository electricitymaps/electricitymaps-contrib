from importlib import resources

import pytest
from freezegun import freeze_time
from requests_mock import ANY, GET

from parsers.PA import fetch_production


@pytest.fixture(autouse=True)
def mock_response(adapter):
    adapter.register_uri(
        GET,
        ANY,
        text=resources.files("parsers.test.mocks")
        .joinpath("PA_nominal_generation.html")
        .read_text(),
        status_code=200,
    )


@freeze_time("2021-12-30 09:58:40", tz_offset=-5)
def test_fetch_production(session, snapshot):
    assert snapshot == fetch_production(session=session)
