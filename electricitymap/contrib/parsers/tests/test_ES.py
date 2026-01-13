from datetime import datetime

import pytest
from requests_mock import GET

from electricitymap.contrib.parsers import ES
from electricitymap.types import ZoneKey


@pytest.fixture(autouse=True)
def mock_response(adapter):
    # these json files are not in valid json format
    with open(
        "electricitymap/contrib/parsers/tests/mocks/ES/demandaGeneracionPeninsula.json",
        "rb",
    ) as data:
        adapter.register_uri(
            GET,
            ES.get_url(ZoneKey("ES"), "2024-10-26"),
            content=data.read(),
        )
    with open(
        "electricitymap/contrib/parsers/tests/mocks/ES/demandaGeneracionBaleares.json",
        "rb",
    ) as data:
        adapter.register_uri(
            GET,
            ES.get_url(ZoneKey("ES-IB-MA"), "2024-10-26"),
            content=data.read(),
        )
    with open(
        "electricitymap/contrib/parsers/tests/mocks/ES/demandaGeneracionCanarias.json",
        "rb",
    ) as data:
        adapter.register_uri(
            GET,
            ES.get_url(ZoneKey("ES-CN-TE"), "2024-10-26"),
            content=data.read(),
        )


### Iberian Peninsula (ES) Consumption
def test_es_consumption(adapter, session, snapshot):
    assert snapshot == ES.fetch_consumption(
        ZoneKey("ES"), session, datetime.fromisoformat("2024-10-26")
    )


### Iberian Peninsula (ES) Production with DST Tests
def test_es_production(adapter, session, snapshot):
    assert snapshot == ES.fetch_production(
        ZoneKey("ES"), session, datetime.fromisoformat("2024-10-26")
    )


### ES->PT exchange
def test_es_pt_exchange(adapter, session, snapshot):
    assert snapshot == ES.fetch_exchange(
        ZoneKey("ES"),
        ZoneKey("PT"),
        session,
        datetime.fromisoformat("2024-10-26"),
    )


### Mallorca Consumption
def test_es_ib_ma_consumption(adapter, session, snapshot):
    assert snapshot == ES.fetch_consumption(
        ZoneKey("ES-IB-MA"), session, datetime.fromisoformat("2024-10-26")
    )


### Mallorca Production with DST Tests
def test_es_ib_ma_production(adapter, session, snapshot):
    assert snapshot == ES.fetch_production(
        ZoneKey("ES-IB-MA"), session, datetime.fromisoformat("2024-10-26")
    )


### Ibiza->Mallorca exchange
def test_es_ib_ma_exchange(adapter, session, snapshot):
    assert snapshot == ES.fetch_exchange(
        ZoneKey("ES-IB-IZ"),
        ZoneKey("ES-IB-MA"),
        session,
        datetime.fromisoformat("2024-10-26"),
    )


### Tenerife Consumption
def test_es_cn_te_consumption(adapter, session, snapshot):
    assert snapshot == ES.fetch_consumption(
        ZoneKey("ES-CN-TE"), session, datetime.fromisoformat("2024-10-26")
    )


### Tenerife Production with DST Tests
def test_es_cn_te_production(adapter, session, snapshot):
    assert snapshot == ES.fetch_production(
        ZoneKey("ES-CN-TE"), session, datetime.fromisoformat("2024-10-26")
    )
