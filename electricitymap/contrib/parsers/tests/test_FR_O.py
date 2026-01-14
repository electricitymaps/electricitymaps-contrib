import json
from datetime import datetime
from importlib import resources

from requests_mock import ANY

from electricitymap.contrib.parsers import FR_O
from electricitymap.contrib.types import ZoneKey


def test_fetch_exchange(adapter, session):
    adapter.register_uri(
        ANY,
        ANY,
        json=json.loads(
            resources.files("electricitymap.contrib.parsers.tests.mocks.FR_O")
            .joinpath("FR_GP.json")
            .read_text()
        ),
    )
    data_list = FR_O.fetch_production("GP", session)
    assert data_list is not None
    expected_data = [
        {
            "zoneKey": "GP",
            "production": {
                "gas": 1,
                "coal": 2,
                "oil": 3,
                "hydro": 4,
                "geothermal": 5,
                "wind": 6,
                "solar": 7,
                "biomass": 8,
            },
            "storage": {},
        },
        {
            "zoneKey": "GP",
            "production": {
                "gas": 10,
                "coal": 11,
                "oil": 12,
                "hydro": 13,
                "geothermal": 14,
                "wind": 15,
                "solar": 16,
                "biomass": 17,
            },
            "storage": {},
        },
    ]
    assert len(data_list) == len(expected_data)
    for index, actual in enumerate(data_list):
        assert actual["zoneKey"] == "GP"
        assert actual["source"] == "opendata-guadeloupe.edf.fr"
        for production_type, production in actual["production"].items():
            assert production, expected_data[index]["production"][production_type]


def test_fetch_price(adapter, session):
    adapter.register_uri(
        ANY,
        ANY,
        json=json.loads(
            resources.files("electricitymap.contrib.parsers.tests.mocks.FR_O")
            .joinpath("FR_RE.json")
            .read_text()
        ),
    )
    data_list = FR_O.fetch_price(ZoneKey("RE"), session, datetime(2018, 1, 1))
    assert data_list is not None
    expected_data = [
        {
            "zoneKey": "RE",
            "currency": "EUR",
            "datetime": datetime.fromisoformat("2018-01-01T00:00:00+00:00"),
            "source": "opendata.edf.fr",
            "price": 193.7,
        },
        {
            "zoneKey": "RE",
            "currency": "EUR",
            "datetime": datetime.fromisoformat("2018-01-01T01:00:00+00:00"),
            "source": "opendata.edf.fr",
            "price": 195.8,
        },
    ]
    assert len(data_list) == len(expected_data)
    for index, actual in enumerate(data_list):
        assert actual["zoneKey"] == expected_data[index]["zoneKey"]
        assert actual["currency"] == expected_data[index]["currency"]
        assert actual["datetime"] == expected_data[index]["datetime"]
        assert actual["source"] == expected_data[index]["source"]
        assert actual["price"] == expected_data[index]["price"]


def test_fetch_production(adapter, session):
    adapter.register_uri(
        ANY,
        ANY,
        json=json.loads(
            resources.files("electricitymap.contrib.parsers.tests.mocks.FR_O")
            .joinpath("FR_COR.json")
            .read_text(encoding="utf-8")
        ),
    )
    data_list = FR_O.fetch_production(ZoneKey("FR-COR"), session)
    assert data_list is not None
    expected_production_data = [
        {
            "correctedModes": [],
            "datetime": datetime.fromisoformat("2024-12-15T10:45:00+00:00"),
            "production": {
                "biomass": 2.0,
                "gas": 0.0,
                "hydro": 26.7,
                "oil": 105.2,
                "solar": 103.8,
                "wind": 0.0,
            },
            "source": "opendata-corse.edf.fr",
            "sourceType": "estimated",
            "storage": {"battery": -0.0},
            "zoneKey": "FR-COR",
        },
        {
            "correctedModes": [],
            "datetime": datetime.fromisoformat("2024-12-15T11:00:00+00:00"),
            "zoneKey": "FR-COR",
            "production": {
                "biomass": 2.0,
                "gas": 0.0,
                "hydro": 25.8,
                "oil": 105.3,
                "solar": 104.1,
                "wind": 0.0,
            },
            "storage": {"battery": -0.0},
            "source": "opendata-corse.edf.fr",
            "sourceType": "estimated",
        },
    ]
    assert len(data_list) == len(expected_production_data)
    for index, actual in enumerate(data_list):
        assert actual["zoneKey"] == expected_production_data[index]["zoneKey"]
        assert actual["source"] == expected_production_data[index]["source"]
        assert actual["sourceType"] == expected_production_data[index]["sourceType"]
        assert actual["datetime"] == expected_production_data[index]["datetime"]
        assert actual["production"] == expected_production_data[index]["production"]
        assert actual["storage"] == expected_production_data[index]["storage"]
        assert (
            actual["correctedModes"]
            == expected_production_data[index]["correctedModes"]
        )
