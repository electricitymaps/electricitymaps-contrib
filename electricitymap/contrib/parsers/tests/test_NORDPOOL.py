import os
from datetime import datetime
from json import loads
from pathlib import Path

import pytest
from requests_mock import GET, POST

from electricitymap.contrib.parsers import NORDPOOL
from electricitymap.contrib.types import ZoneKey

base_path_to_mock = Path("electricitymap/contrib/parsers/tests/mocks/NORDPOOL")


@pytest.fixture(autouse=True)
def emaps_env():
    os.environ["EMAPS_NORDPOOL_USERNAME"] = "username"
    os.environ["EMAPS_NORDPOOL_PASSWORD"] = "password"


def test_price_parser_se(requests_mock, session, snapshot):
    mock_token = Path(base_path_to_mock, "token.json")
    mock_data_current_day = Path(base_path_to_mock, "se_current_day_price.json")
    mock_data_next_day = Path(base_path_to_mock, "se_next_day_price.json")

    requests_mock.register_uri(
        POST,
        "https://sts.nordpoolgroup.com/connect/token",
        json=loads(mock_token.read_text()),
    )
    requests_mock.register_uri(
        GET,
        "https://data-api.nordpoolgroup.com/api/v2/Auction/Prices/ByAreas?areas=SE4&currency=EUR&market=DayAhead&date=2024-07-08",
        json=loads(mock_data_current_day.read_text()),
    )
    requests_mock.register_uri(
        GET,
        "https://data-api.nordpoolgroup.com/api/v2/Auction/Prices/ByAreas?areas=SE4&currency=EUR&market=DayAhead&date=2024-07-09",
        json=loads(mock_data_next_day.read_text()),
    )

    assert snapshot == NORDPOOL.fetch_price(
        zone_key=ZoneKey("SE-SE4"),
        session=session,
        target_datetime=datetime.fromisoformat("2024-07-08"),
    )


def test_exchange_parser_fi_se1(requests_mock, session, snapshot):
    mock_token = Path(base_path_to_mock, "token.json")
    mock_data_current_day = Path(base_path_to_mock, "fi_se1_current_day_exchange.json")
    mock_data_previous_day = Path(
        base_path_to_mock, "fi_se1_previous_day_exchange.json"
    )

    requests_mock.register_uri(
        POST,
        "https://sts.nordpoolgroup.com/connect/token",
        json=loads(mock_token.read_text()),
    )
    requests_mock.register_uri(
        GET,
        "https://data-api.nordpoolgroup.com/api/v2/PowerSystem/Exchanges/ByAreas?areas=FI&date=2024-12-01",
        json=loads(mock_data_current_day.read_text()),
    )
    requests_mock.register_uri(
        GET,
        "https://data-api.nordpoolgroup.com/api/v2/PowerSystem/Exchanges/ByAreas?areas=FI&date=2024-11-30",
        json=loads(mock_data_previous_day.read_text()),
    )

    assert snapshot == NORDPOOL.fetch_exchange(
        zone_key1=ZoneKey("FI"),
        zone_key2=ZoneKey("SE-SE1"),
        session=session,
        target_datetime=datetime.fromisoformat("2024-12-01"),
    )


EXCHANGE_URL = "https://data-api.nordpoolgroup.com/api/v2/PowerSystem/Exchanges/ByAreas"


def _register_fi_exchange(requests_mock, current_day: list, previous_day: list):
    requests_mock.register_uri(
        POST,
        "https://sts.nordpoolgroup.com/connect/token",
        json=loads(Path(base_path_to_mock, "token.json").read_text()),
    )
    requests_mock.register_uri(
        GET, f"{EXCHANGE_URL}?areas=FI&date=2024-12-01", json=current_day
    )
    requests_mock.register_uri(
        GET, f"{EXCHANGE_URL}?areas=FI&date=2024-11-30", json=previous_day
    )


def _fetch_fi_se1(session) -> list:
    return NORDPOOL.fetch_exchange(
        zone_key1=ZoneKey("FI"),
        zone_key2=ZoneKey("SE-SE1"),
        session=session,
        target_datetime=datetime.fromisoformat("2024-12-01"),
    )


def test_exchange_directions_match_connection_export_and_import(requests_mock, session):
    current_day = loads(
        Path(base_path_to_mock, "fi_se1_current_day_exchange.json").read_text()
    )
    previous_day = loads(
        Path(base_path_to_mock, "fi_se1_previous_day_exchange.json").read_text()
    )
    _register_fi_exchange(requests_mock, current_day, previous_day)
    se1_by_start = {
        datetime.fromisoformat(exchange["deliveryStart"].replace("Z", "+00:00")): conn
        for payload in (current_day, previous_day)
        for exchange in payload[0]["exchanges"]
        for conn in exchange["byConnections"]
        if conn["area"] == "SE1"
    }

    events = _fetch_fi_se1(session)

    assert len(events) == len(se1_by_start) == 128
    assert any(event["exports"] > 0 for event in events)
    assert any(event["imports"] > 0 for event in events)
    for event in events:
        connection = se1_by_start[event["datetime"]]
        assert event["sortedZoneKeys"] == "FI->SE-SE1"
        assert event["exports"] == connection["export"]
        assert event["imports"] == connection["import"]
        assert event["netFlow"] == -connection["netPosition"]
        assert event["netFlow"] == event["exports"] - event["imports"]


def test_exchange_keeps_both_directions_within_one_period(requests_mock, session):
    def payload(start: str, end: str, export: float, import_: float) -> list:
        return [
            {
                "deliveryArea": "FI",
                "exchanges": [
                    {
                        "byConnections": [
                            {
                                "area": "SE1",
                                "export": export,
                                "import": import_,
                                "netPosition": import_ - export,
                            },
                            {
                                "area": "EE",
                                "export": 999.0,
                                "import": 0.0,
                                "netPosition": -999.0,
                            },
                        ],
                        "deliveryStart": start,
                        "deliveryEnd": end,
                    }
                ],
            }
        ]

    _register_fi_exchange(
        requests_mock,
        current_day=payload("2024-12-01T00:00:00Z", "2024-12-01T00:15:00Z", 300, 120),
        previous_day=payload("2024-11-30T00:00:00Z", "2024-11-30T00:15:00Z", 50, 80),
    )

    events = sorted(_fetch_fi_se1(session), key=lambda e: e["datetime"])

    assert [(e["exports"], e["imports"], e["netFlow"]) for e in events] == [
        (50, 80, -30),
        (300, 120, 180),
    ]
    assert all(e["sortedZoneKeys"] == "FI->SE-SE1" for e in events)


def test_atc_parser_de_no_no2(requests_mock, session, snapshot):
    """DE↔NO-NO2 is the NordLink cable. The parser queries from zone1's side
    (DE → Nordpool code `GER`) and filters byConnection on the counterpart
    (`NO2_NK`). From GER's perspective `exportsByConnection` is GER→NO2 =
    capacityExport (DE→NO-NO2) and `importsByConnection` is NO2→GER =
    capacityImport (NO-NO2→DE) — no direction flip needed.
    """
    mock_token = Path(base_path_to_mock, "token.json")
    mock_target_day = Path(base_path_to_mock, "ger_target_day_capacity.json")
    mock_next_day = Path(base_path_to_mock, "ger_next_day_capacity.json")

    requests_mock.register_uri(
        POST,
        "https://sts.nordpoolgroup.com/connect/token",
        json=loads(mock_token.read_text()),
    )
    requests_mock.register_uri(
        GET,
        "https://data-api.nordpoolgroup.com/api/v2/Auction/Capacities/ByAreas?areas=GER&market=DayAhead&date=2025-05-10",
        json=loads(mock_target_day.read_text()),
    )
    requests_mock.register_uri(
        GET,
        "https://data-api.nordpoolgroup.com/api/v2/Auction/Capacities/ByAreas?areas=GER&market=DayAhead&date=2025-05-11",
        json=loads(mock_next_day.read_text()),
    )

    assert snapshot == NORDPOOL.fetch_exchange_available_transfer_capacity(
        zone_key1=ZoneKey("DE"),
        zone_key2=ZoneKey("NO-NO2"),
        session=session,
        target_datetime=datetime.fromisoformat("2025-05-10"),
    )
