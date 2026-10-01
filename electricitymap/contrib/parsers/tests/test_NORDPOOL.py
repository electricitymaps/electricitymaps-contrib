import os
import time
from datetime import datetime, timedelta, timezone
from json import loads
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
from freezegun import freeze_time
from requests_mock import ANY, GET, POST

from electricitymap.contrib.parsers import NORDPOOL
from electricitymap.contrib.types import DayAheadAuction, ZoneKey

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


def _register_token(requests_mock):
    requests_mock.register_uri(
        POST,
        "https://sts.nordpoolgroup.com/connect/token",
        json=loads(Path(base_path_to_mock, "token.json").read_text()),
    )


def _assert_utc(rows):
    for row in rows:
        for key in ("datetime", "end_datetime", "publishedAt"):
            assert row[key].utcoffset() == timedelta(0)


def test_price_day_ahead_se(requests_mock, session, snapshot):
    _register_token(requests_mock)
    requests_mock.register_uri(
        GET,
        "https://data-api.nordpoolgroup.com/api/v2/Auction/Prices/ByAreas?areas=SE4&currency=EUR&market=DayAhead&date=2024-07-08",
        json=loads(Path(base_path_to_mock, "se_current_day_price.json").read_text()),
    )
    requests_mock.register_uri(
        GET,
        "https://data-api.nordpoolgroup.com/api/v2/Auction/Prices/ByAreas?areas=SE4&currency=EUR&market=DayAhead&date=2024-07-09",
        json=loads(Path(base_path_to_mock, "se_next_day_price.json").read_text()),
    )

    rows = NORDPOOL.fetch_price_day_ahead(
        zone_key=ZoneKey("SE-SE4"),
        session=session,
        target_datetime=datetime.fromisoformat("2024-07-08"),
    )

    assert snapshot == rows
    assert len(rows) == 48
    assert {row["auction"] for row in rows} == {DayAheadAuction.SDAC}
    # The next day's `updatedAt` has 7 fractional digits.
    assert rows[-1]["publishedAt"] == datetime(
        2024, 7, 8, 11, 12, 16, 85662, tzinfo=timezone.utc
    )
    _assert_utc(rows)


def test_price_day_ahead_gb(requests_mock, session, snapshot):
    _register_token(requests_mock)
    requests_mock.register_uri(
        GET,
        "https://data-api.nordpoolgroup.com/api/v2/Auction/Prices/ByAreas?areas=UK&currency=GBP&market=N2EX_DayAhead&date=2026-10-01",
        json=loads(Path(base_path_to_mock, "gb_n2ex_day_ahead_price.json").read_text()),
    )
    requests_mock.register_uri(
        GET,
        "https://data-api.nordpoolgroup.com/api/v2/Auction/Prices/ByAreas?areas=UK&currency=GBP&market=N2EX_DayAhead&date=2026-10-02",
        json=loads(Path(base_path_to_mock, "gb_n2ex_next_day_price.json").read_text()),
    )

    rows = NORDPOOL.fetch_price_day_ahead(
        zone_key=ZoneKey("GB"),
        session=session,
        target_datetime=datetime(2026, 10, 1, 12, tzinfo=timezone.utc),
    )

    assert snapshot == rows
    assert len(rows) == 48
    assert all(
        row["end_datetime"] - row["datetime"] == timedelta(hours=1) for row in rows
    )
    assert {row["auction"] for row in rows} == {DayAheadAuction.NORDPOOL_N2EX_DA}
    assert {row["currency"] for row in rows} == {"GBP"}
    # Each delivery day carries its own `updatedAt`.
    assert rows[0]["publishedAt"] == datetime(
        2026, 9, 30, 8, 59, 40, 955084, tzinfo=timezone.utc
    )
    assert rows[-1]["publishedAt"] == datetime(
        2026, 10, 1, 8, 59, 10, 8320, tzinfo=timezone.utc
    )
    _assert_utc(rows)


def _requested_dates(requests_mock) -> list[str]:
    return [
        parse_qs(urlparse(request.url).query)["date"][0]
        for request in requests_mock.request_history
        if request.method == GET
    ]


def _register_gb_any(requests_mock):
    _register_token(requests_mock)
    requests_mock.register_uri(
        GET,
        ANY,
        json=loads(Path(base_path_to_mock, "gb_n2ex_day_ahead_price.json").read_text()),
    )


@pytest.mark.parametrize(
    "target_datetime",
    [
        datetime(2026, 9, 30, 22, 30, tzinfo=timezone.utc),
        # Naive targets are UTC, not host-local time.
        datetime(2026, 9, 30, 22, 30),
    ],
)
def test_price_day_ahead_utc_target(requests_mock, session, target_datetime):
    """22:30 UTC is already the next CET delivery day."""
    _register_gb_any(requests_mock)
    NORDPOOL.fetch_price_day_ahead(
        ZoneKey("GB"), session, target_datetime=target_datetime
    )
    assert _requested_dates(requests_mock) == ["2026-10-01", "2026-10-02"]


@freeze_time("2026-09-30 22:30:00")
def test_price_day_ahead_live_uses_cet_delivery_date(requests_mock, session):
    _register_gb_any(requests_mock)
    NORDPOOL.fetch_price_day_ahead(ZoneKey("GB"), session)
    assert _requested_dates(requests_mock) == ["2026-10-01", "2026-10-02"]


def test_price_day_ahead_does_not_depend_on_host_timezone(
    requests_mock, session, monkeypatch
):
    _register_gb_any(requests_mock)
    try:
        with monkeypatch.context() as patched:
            patched.setenv("TZ", "America/New_York")
            time.tzset()
            NORDPOOL.fetch_price_day_ahead(
                ZoneKey("GB"), session, target_datetime=datetime(2026, 9, 30, 22, 30)
            )
    finally:
        time.tzset()
    assert _requested_dates(requests_mock) == ["2026-10-01", "2026-10-02"]


def test_price_day_ahead_unknown_zone_raises(session):
    with pytest.raises(NotImplementedError):
        NORDPOOL.fetch_price_day_ahead(ZoneKey("RU-1"), session)
