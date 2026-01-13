import json
from importlib import resources

import pytest
from requests_mock import ANY, GET

from electricitymap.contrib.parsers.CAMMESA import (
    CAMMESA_DEMANDA_ENDPOINT,
    CAMMESA_RENEWABLES_ENDPOINT,
    fetch_exchange,
    fetch_production,
)
from electricitymap.types import ZoneKey


@pytest.fixture(autouse=True)
def mock_response(adapter):
    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("electricitymap.contrib.parsers.tests.mocks.Cammesa")
            .joinpath("exchanges.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        CAMMESA_DEMANDA_ENDPOINT,
        json=json.loads(
            resources.files("electricitymap.contrib.parsers.tests.mocks.Cammesa")
            .joinpath("conventional_production.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        CAMMESA_RENEWABLES_ENDPOINT,
        json=json.loads(
            resources.files("electricitymap.contrib.parsers.tests.mocks.Cammesa")
            .joinpath("renewable_production.json")
            .read_text()
        ),
    )


def test_exchanges_AR_CL_SEN(session, snapshot):
    assert snapshot == fetch_exchange(
        ZoneKey("AR"),
        ZoneKey("CL-SEN"),
        session=session,
    )


def test_exchanges_AR_BAS_AR_COM(session, snapshot):
    assert snapshot == fetch_exchange(
        ZoneKey("AR-BAS"),
        ZoneKey("AR-COM"),
        session=session,
    )


def test_fetch_production(session, snapshot):
    assert snapshot == fetch_production(ZoneKey("AR"), session=session)
