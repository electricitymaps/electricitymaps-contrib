import logging
from importlib import resources

import pytest
from freezegun import freeze_time
from requests_mock import GET
from testfixtures import LogCapture

from parsers import SG


@pytest.fixture(autouse=True)
def mock_response(adapter):
    adapter.register_uri(
        GET,
        SG.SOLAR_URL,
        content=resources.files("parsers.test.mocks")
        .joinpath("SG_ema_gov_sg_solar_map.png")
        .read_bytes(),
    )


@freeze_time("2021-12-23 03:21:00")
def test_works_when_nonzero(adapter, session):
    adapter.register_uri(
        GET,
        SG.SOLAR_URL,
        content=resources.files("parsers.test.mocks")
        .joinpath("SG_ema_gov_sg_solar_map_nonzero.png")
        .read_bytes(),
    )
    assert SG.get_solar(session, logger=logging.getLogger("test")) == 350.55


@freeze_time("2021-12-23 15:12:00")
def test_works_when_zero(session):
    assert SG.get_solar(session, logger=logging.getLogger("test")) == 0.0


@freeze_time("2024-08-06 15:12:00")
def test_ignore_data_older_than_one_hour(session):
    with LogCapture():
        assert SG.get_solar(session, logger=logging.getLogger("test")) is None


@freeze_time("2021-12-23 15:06:00")
def test_allow_remote_clock_to_be_slightly_ahead(session):
    assert SG.get_solar(session, logger=logging.getLogger("test")) == 0
