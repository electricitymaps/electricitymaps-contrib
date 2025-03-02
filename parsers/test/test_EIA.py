import json
import os
from datetime import datetime, timezone
from importlib import resources

import pytest
from requests_mock import ANY, GET

from electricitymap.contrib.lib.models.events import EventSourceType
from electricitymap.contrib.lib.types import ZoneKey
from parsers import EIA


@pytest.fixture(autouse=True)
def eia_key_env():
    os.environ["EIA_KEY"] = "token"


def _check_production_matches(
    actual: list[dict[str, str | dict]],
    expected: list[dict[str, str | dict]],
):
    assert actual is not None
    assert len(expected) == len(actual)
    for i, data in enumerate(actual):
        assert data["zoneKey"] == expected[i]["zoneKey"]
        assert data["source"] == expected[i]["source"]
        assert data["datetime"] is not None
        for key, value in data["production"].items():
            assert value == expected[i]["production"][key]
        assert data.get("storage") == expected[i].get("storage")
        for key, value in data.get("storage", {}).items():
            assert value == expected[i]["storage"][key]


def test_parse_hourly_interval():
    """
    We add a 'frequency=hourly' parameter to our EIA API requests; this
    requests results grouped by hourly intervals in UTC time.

    Each time window in the response indicates the _end_ of that hourly
    interval; ElectricityMaps stores intervals using start hour instead.
    """
    fixtures = [
        ("2022-02-28T23", datetime(2022, 2, 28, 22, 0, 0, tzinfo=timezone.utc)),
        ("2022-03-01T00", datetime(2022, 2, 28, 23, 0, 0, tzinfo=timezone.utc)),
        ("2022-03-01T01", datetime(2022, 3, 1, 0, 0, 0, tzinfo=timezone.utc)),
    ]

    for period, expected in fixtures:
        result = EIA._parse_hourly_interval(period)
        assert result == expected


def test_fetch_production_mix(adapter, session):
    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_NW_AVRN-wind.json")
            .read_text()
        ),
    )
    data_list = EIA.fetch_production_mix("US-NW-PGE", session)
    expected = [
        {
            "zoneKey": "US-NW-PGE",
            "source": "eia.gov",
            "production": {
                "gas": 1,
                "coal": 1,
                "wind": 1,
                "hydro": 1,
                "nuclear": 1,
                "oil": 1,
                "unknown": 1,
                "solar": 1,
                "geothermal": 1,
            },
            "storage": {},
        },
        {
            "zoneKey": "US-NW-PGE",
            "source": "eia.gov",
            "production": {
                "gas": 2,
                "coal": 2,
                "wind": 2,
                "hydro": 2,
                "nuclear": 2,
                "oil": 2,
                "unknown": 2,
                "solar": 2,
                "geothermal": 2,
            },
            "storage": {},
        },
    ]
    _check_production_matches(data_list, expected)


def test_US_NW_AVRN_rerouting(adapter, session):
    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_NW_AVRN-other.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("AVRN", "WND"),
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_NW_AVRN-wind.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("PACW", "NG"),
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_NW_PACW-gas.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("PACW", "WAT"),
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_SMTH-coal.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("PACW", "SUN"),
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_SMTH-coal.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("PACW", "WND"),
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_SMTH-coal.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("BPAT", "WND"),
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_NW_BPAT-wind.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("BPAT", "NG"),
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_SMTH-coal.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("BPAT", "WAT"),
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_SMTH-coal.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("BPAT", "NUC"),
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_SMTH-coal.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("BPAT", "SUN"),
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_SMTH-coal.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("AVRN", "NG"),
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_NW_AVRN-gas.json")
            .read_text()
        ),
    )

    data_list = EIA.fetch_production_mix(ZoneKey("US-NW-PACW"), session)
    expected = [
        {
            "zoneKey": "US-NW-PACW",
            "source": "eia.gov",
            "production": {"gas": 330, "hydro": 300, "solar": 300, "wind": 300},
            "storage": {},
        },
        {
            "zoneKey": "US-NW-PACW",
            "source": "eia.gov",
            "production": {"gas": 450, "hydro": 400, "solar": 400, "wind": 400},
            "storage": {},
        },
    ]
    _check_production_matches(data_list, expected)
    data_list = EIA.fetch_production_mix(ZoneKey("US-NW-BPAT"), session)
    expected = [
        {
            "zoneKey": "US-NW-BPAT",
            "source": "eia.gov",
            "production": {
                "wind": 21,
                "gas": 300,
                "hydro": 300,
                "nuclear": 300,
                "solar": 300,
            },
            "storage": {},
        },
        {
            "zoneKey": "US-NW-BPAT",
            "source": "eia.gov",
            "production": {
                "wind": 42,
                "gas": 400,
                "hydro": 400,
                "nuclear": 400,
                "solar": 400,
            },
            "storage": {},
        },
    ]
    _check_production_matches(data_list, expected)


def test_US_CAR_SC_nuclear_split(adapter, session):
    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_NW_AVRN-other.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("SC", "COL"),
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_SMTH-coal.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("SC", "NG"),
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_SMTH-coal.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("SC", "WAT"),
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_SMTH-coal.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("SC", "OIL"),
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_SMTH-coal.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("SC", "SUN"),
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_SMTH-coal.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("SC", "NUC"),
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_CAR_SC-nuclear.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("SCEG", "NUC"),
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_CAR_SCEG-nuclear.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("SCEG", "COL"),
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_SMTH-coal.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("SCEG", "NG"),
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_SMTH-coal.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("SCEG", "WAT"),
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_SMTH-coal.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("SCEG", "OIL"),
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_SMTH-coal.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("SCEG", "SUN"),
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_SMTH-coal.json")
            .read_text()
        ),
    )

    data_list = EIA.fetch_production_mix(ZoneKey("US-CAR-SC"), session)
    expected = [
        {
            "zoneKey": "US-CAR-SC",
            "source": "eia.gov",
            "production": {
                "nuclear": 330.666634,
                "coal": 300,
                "gas": 300,
                "oil": 300,
                "solar": 300,
                "hydro": 300,
            },
            "storage": {},
        },
        {
            "zoneKey": "US-CAR-SC",
            "source": "eia.gov",
            "production": {
                "nuclear": 330.3333,
                "coal": 400,
                "gas": 400,
                "oil": 400,
                "solar": 400,
                "hydro": 400,
            },
            "storage": {},
        },
    ]
    _check_production_matches(data_list, expected)
    data_list = EIA.fetch_production_mix(ZoneKey("US-CAR-SCEG"), session)
    expected = [
        {
            "zoneKey": "US-CAR-SCEG",
            "source": "eia.gov",
            "production": {
                "nuclear": 661.333366,
                "coal": 300,
                "gas": 300,
                "oil": 300,
                "solar": 300,
                "hydro": 300,
            },
            "storage": {},
        },
        {
            "zoneKey": "US-CAR-SCEG",
            "source": "eia.gov",
            "production": {
                "nuclear": 660.6667,
                "coal": 400,
                "gas": 400,
                "oil": 400,
                "solar": 400,
                "hydro": 400,
            },
            "storage": {},
        },
    ]
    _check_production_matches(data_list, expected)


def test_check_transfer_mixes():
    for production in EIA.PRODUCTION_ZONES_TRANSFERS.values():
        all_production = production.get("all", {})
        for production_type, supplying_zones in production.items():
            if production_type == "all":
                continue
            for zone in supplying_zones:
                if zone in all_production:
                    raise Exception(
                        f"{zone} is both in the all production export\
                        and exporting its {production_type} production. \
                        This is not possible please fix this ambiguity."
                    )


def test_hydro_transfer_mix(adapter, session):
    """
    Make sure that with zones that integrate production only zones
    the hydro production events are properly handled and the storage
    is accounted for on a zone by zone basis.
    """
    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_NW_AVRN-other.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("SRP", "COL"),
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_SMTH-coal.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("SRP", "NG"),
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_SMTH-coal.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("SRP", "NUC"),
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_SMTH-coal.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("SRP", "SUN"),
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_SMTH-coal.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("SRP", "WND"),
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_SMTH-coal.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("DEAA", "WAT"),
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_SW_DEAA-hydro.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("HGMA", "WAT"),
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_SW_HGMA-hydro.json")
            .read_text()
        ),
    )
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("SRP", "WAT"),
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_SW_SRP-hydro.json")
            .read_text()
        ),
    )

    data = EIA.fetch_production_mix(ZoneKey("US-SW-SRP"), session)
    expected = [
        {
            "zoneKey": "US-SW-SRP",
            "source": "eia.gov",
            "production": {
                "hydro": 7.0,
                "coal": 300,
                "gas": 300,
                "nuclear": 300,
                "solar": 300,
                "wind": 300,
            },  # hydro 4 from HGMA, 3 from DEAA
            "storage": {"hydro": 5.0},  # 5 from SRP
        },
        {
            "zoneKey": "US-SW-SRP",
            "source": "eia.gov",
            "production": {
                "hydro": 800.0,
                "coal": 400,
                "gas": 400,
                "nuclear": 400,
                "solar": 400,
                "wind": 400,
            },  # hydro 400 from SRP, 400 from HGMA
            "storage": {"hydro": 900.0},  # 900 from DEAA
        },
    ]
    _check_production_matches(data, expected)


def test_exchange_transfer(adapter, session):
    exchange_key = "US-FLA-FPC->US-FLA-FPL"
    remapped_exchange_key = "US-FLA-FPC->US-FLA-NSB"
    # target_datetime = (
    #     "2020-01-07T05:00:00+00:00"  # Last datapoint before decommissioning of NSB
    # )
    # 1. Get data directly from EIA for both
    fpl_exchange_data = json.loads(
        resources.files("parsers.test.mocks.EIA")
        .joinpath("US-FLA-FPC_US-FLA-FPL_exchange.json")
        .read_text()
    )
    adapter.register_uri(
        GET,
        # For example:
        # https://api.eia.gov/v2/electricity/rto/interchange-data/data/?data[]=value&facets[fromba][]=FPC&facets[toba][]=FPL&frequency=hourly&api_key=token&sort[0][column]=period&sort[0][direction]=desc&length=24
        EIA.EXCHANGE.format(EIA.EXCHANGES[exchange_key]),
        json=fpl_exchange_data,
    )
    nsb_exchange_data = json.loads(
        resources.files("parsers.test.mocks.EIA")
        .joinpath("US-FLA-FPC_US-FLA-NSB_exchange.json")
        .read_text()
    )
    adapter.register_uri(
        GET,
        # For example:
        # https://api.eia.gov/v2/electricity/rto/interchange-data/data/?data[]=value&facets[fromba][]=FPC&facets[toba][]=NSB&frequency=hourly&api_key=token&sort[0][column]=period&sort[0][direction]=desc&length=24
        EIA.EXCHANGE.format(EIA.EXCHANGES[remapped_exchange_key]),
        json=nsb_exchange_data,
    )

    # 2. Get data from the EIA parser fetch_exchange for
    # US-FLA-FPC->US-FLA-FPL
    z_k_1, z_k_2 = exchange_key.split("->")
    data_list = EIA.fetch_exchange(ZoneKey(z_k_1), ZoneKey(z_k_2), session)

    # Verify that the sum of the data directly fetched matches the data
    # from the parser.
    for fpl, nsb, parser in zip(
        fpl_exchange_data["response"]["data"],
        nsb_exchange_data["response"]["data"],
        data_list,
        strict=True,
    ):
        assert fpl["value"] + nsb["value"] == parser["netFlow"]


def test_fetch_production_mix_discards_null(adapter, session):
    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US-NW-PGE-with-nulls.json")
            .read_text()
        ),
    )
    data_list = EIA.fetch_production_mix(ZoneKey("US-NW-PGE"), session)
    expected = [
        {
            "zoneKey": "US-NW-PGE",
            "source": "eia.gov",
            "production": {
                "gas": 400,
                "coal": 400,
                "wind": 400,
                "hydro": 400,
                "nuclear": 400,
                "oil": 400,
                "unknown": 400,
                "solar": 400,
                "geothermal": 400,
            },
            "storage": {},
        },
    ]
    assert (
        datetime(2022, 10, 31, 11, 0, tzinfo=timezone.utc) == data_list[0]["datetime"]
    )
    _check_production_matches(data_list, expected)


def test_fetch_exchange(adapter, session):
    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US-NW-BPAT-US-NW-NWMT-exchange.json")
            .read_text()
        ),
    )
    data_list = EIA.fetch_exchange(
        ZoneKey("US-NW-BPAT"), ZoneKey("US-NW-NWMT"), session
    )
    expected = [
        {
            "source": "eia.gov",
            "datetime": datetime(2022, 2, 28, 22, 0, tzinfo=timezone.utc),
            "sortedZoneKeys": "US-NW-BPAT->US-NW-NWMT",
            "netFlow": -12,
        },
        {
            "source": "eia.gov",
            "datetime": datetime(2022, 2, 28, 23, 0, tzinfo=timezone.utc),
            "sortedZoneKeys": "US-NW-BPAT->US-NW-NWMT",
            "netFlow": -11,
        },
        {
            "source": "eia.gov",
            "datetime": datetime(2022, 3, 1, 0, 0, tzinfo=timezone.utc),
            "sortedZoneKeys": "US-NW-BPAT->US-NW-NWMT",
            "netFlow": -2,
        },
    ]
    assert len(data_list) == len(expected)
    for i, data in enumerate(data_list):
        assert data["source"] == expected[i]["source"]
        assert data["datetime"] == expected[i]["datetime"]
        assert data["sortedZoneKeys"] == expected[i]["sortedZoneKeys"]
        assert data["netFlow"] == expected[i]["netFlow"]


def test_fetch_consumption(adapter, session):
    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_NW_BPAT-consumption.json")
            .read_text()
        ),
    )
    data_list = EIA.fetch_consumption(ZoneKey("US-NW-BPAT"), session)
    expected = [
        {
            "source": "eia.gov",
            "datetime": datetime(2023, 5, 1, 9, 0, tzinfo=timezone.utc),
            "consumption": 4792,
        },
        {
            "source": "eia.gov",
            "datetime": datetime(2023, 5, 1, 10, 0, tzinfo=timezone.utc),
            "consumption": 6215,
        },
    ]
    assert len(data_list) == len(expected)
    for i, data in enumerate(data_list):
        assert data["source"] == expected[i]["source"]
        assert data["datetime"] == expected[i]["datetime"]
        assert data["consumption"] == expected[i]["consumption"]


def test_fetch_forecasted_consumption(adapter, session):
    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_NW_BPAT-consumption.json")
            .read_text()
        ),
    )
    data_list = EIA.fetch_consumption_forecast(ZoneKey("US-NW-BPAT"), session)
    expected = [
        {
            "source": "eia.gov",
            "datetime": datetime(2023, 5, 1, 9, 0, tzinfo=timezone.utc),
            "consumption": 4792,
        },
        {
            "source": "eia.gov",
            "datetime": datetime(2023, 5, 1, 10, 0, tzinfo=timezone.utc),
            "consumption": 6215,
        },
    ]
    assert len(data_list) == len(expected)
    for i, data in enumerate(data_list):
        assert data["source"] == expected[i]["source"]
        assert data["datetime"] == expected[i]["datetime"]
        assert data["consumption"] == expected[i]["consumption"]
        assert data["sourceType"] == EventSourceType.forecasted


def test_texas_loses_one_mode(adapter, session):
    """A temporary test to make sure that if texas loses one of its modes we discard the datapoint."""
    # All modes are loaded with some data
    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_SMTH-coal.json")
            .read_text()
        ),
    )
    # Nuclear is missing data
    adapter.register_uri(
        GET,
        EIA.PRODUCTION_MIX.format("ERCO", "NUC"),
        json=json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US_NW_AVRN-other.json")
            .read_text()
        ),
    )
    data = EIA.fetch_production_mix(ZoneKey("US-TEX-ERCO"), session)
    assert len(data) == 0
