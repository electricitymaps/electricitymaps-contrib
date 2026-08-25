import logging
from importlib import resources

import pytest
from freezegun import freeze_time
from requests_mock import GET
from testfixtures import LogCapture

from electricitymap.contrib.parsers import SG


@pytest.fixture(autouse=True)
def mock_response(requests_mock):
    requests_mock.register_uri(
        GET,
        SG.SOLAR_URL,
        content=resources.files("electricitymap.contrib.parsers.tests.mocks")
        .joinpath("SG_ema_gov_sg_solar_map.png")
        .read_bytes(),
    )


@freeze_time("2021-12-23 03:21:00")
def test_works_when_nonzero(requests_mock, session):
    requests_mock.register_uri(
        GET,
        SG.SOLAR_URL,
        content=resources.files("electricitymap.contrib.parsers.tests.mocks")
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


def test_production_multi_source_has_no_space_after_comma():
    """Multi-source strings are split on "," without trim in the app (#8779).

    Tokens must not have leading spaces or the zone page builds
    ``https://%20…`` hrefs (same class of bug as GB Elexon / #8800).
    """
    import inspect

    src = inspect.getsource(SG.fetch_production)
    assert 'source="emcsg.com,ema.gov.sg"' in src
    assert 'source="emcsg.com, ema.gov.sg"' not in src
