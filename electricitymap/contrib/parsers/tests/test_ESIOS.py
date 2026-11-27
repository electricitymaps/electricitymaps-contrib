import json
import os
from datetime import datetime, timedelta
from importlib import resources

import pytest
from requests_mock import ANY

from electricitymap.contrib.parsers import ESIOS
from electricitymap.contrib.types import ZoneKey


def test_fetch_exchange(requests_mock, session):
    requests_mock.register_uri(
        ANY,
        ANY,
        json=json.loads(
            resources.files("electricitymap.contrib.parsers.tests.mocks")
            .joinpath("ESIOS_ES_MA.json")
            .read_text()
        ),
    )
    os.environ["ESIOS_TOKEN"] = "token"
    data_list = ESIOS.fetch_exchange(ZoneKey("ES"), ZoneKey("MA"), session)
    assert data_list is not None
    for data in data_list:
        assert data["sortedZoneKeys"] == "ES->MA"
        assert data["source"] == "api.esios.ree.es"
        assert data["datetime"] is not None
        assert data["netFlow"] is not None


def test_exchange_with_snapshot(session, requests_mock, snapshot):
    requests_mock.register_uri(
        ANY,
        ANY,
        json=json.loads(
            resources.files("electricitymap.contrib.parsers.tests.mocks")
            .joinpath("ESIOS_ES_MA.json")
            .read_text()
        ),
    )
    os.environ["ESIOS_TOKEN"] = "token"
    assert snapshot == ESIOS.fetch_exchange(ZoneKey("ES"), ZoneKey("MA"), session)


@pytest.mark.parametrize(
    "zone_key,threshold",
    [
        (ZoneKey("ES->MA"), ESIOS.ES_MA_FACTOR_THRESHOLD),
        (ZoneKey("AD->ES"), ESIOS.AD_ES_FACTOR_THRESHOLD),
    ],
)
def test_exchange_multiplication_factor(zone_key, threshold):
    # Hourly values (MWh per hour == MW) before the switch to 15 min values.
    assert (
        ESIOS.get_exchange_multiplication_factor(
            zone_key, threshold - timedelta(seconds=1)
        )
        == 1
    )
    # 15 min values (MWh per quarter-hour) need scaling by 4 to get MW.
    assert ESIOS.get_exchange_multiplication_factor(zone_key, threshold) == 4


def test_ad_es_factor_threshold_is_madrid_midnight():
    assert datetime(2025, 10, 1, tzinfo=ESIOS.TIMEZONE) == ESIOS.AD_ES_FACTOR_THRESHOLD
