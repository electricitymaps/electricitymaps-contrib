"""Test for JP parsers"""

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from freezegun import freeze_time
from requests_mock import GET

from electricitymap.contrib.parsers.JP import (
    JEPX_SPOT_URL,
    fetch_consumption_forecast,
    fetch_generation_forecast,
    fetch_price_day_ahead,
)
from electricitymap.contrib.types import DayAheadAuction, ZoneKey

JEPX_MOCKS = Path("electricitymap/contrib/parsers/tests/mocks/JP")


@pytest.mark.parametrize(
    "zone_key",
    [
        "JP-CB",
        "JP-CG",
        "JP-HKD",
        "JP-HR",
        "JP-KN",
        "JP-KY",
        "JP-ON",
        "JP-SK",
        "JP-TH",
        "JP-TK",
    ],
)
@freeze_time("2025-04-16")  # because the mocks are all around this date
def test_snapshot_fetch_generation_forecast(requests_mock, session, snapshot, zone_key):
    datestamp_today = datetime.now().strftime("%Y%m%d")
    BASE_PATH_TO_MOCK = Path("electricitymap/contrib/parsers/tests/mocks/" + zone_key)

    forecast_url = {
        "JP-HKD": r"http://denkiyoho\.hepco\.co\.jp/area/data/\d{8}_hokkaido_yosoku\.csv",
        "JP-HR": r"https://www\.rikuden\.co\.jp/nw/denki-yoho/csv/yosoku_05_\d{8}\.csv",
        "JP-KN": r"https://www\.kansai-td\.co\.jp/interchange/denkiyoho/imbalance/\d{8}_yosoku\.csv",
        "JP-CG": r"https://www\.energia\.co\.jp/nw/jukyuu/sys/\d{6}_jyukyu2_chugoku\.zip",
        "JP-KY": r"https://www\.kyuden\.co\.jp/td_power_usages/csv/kouhyo/imbalance/21110_TSO9_0_\d{8}\.csv\?a=\d{8}%5Cd6",
        "JP-ON": r"http://www\.okiden\.co\.jp/denki2/dem_pg/csv/jukyu_yosoku_\d{8}\.csv",
    }

    # For zones with different URLs for today vs tomorrow
    if zone_key in ["JP-TH", "JP-TK", "JP-CB", "JP-SK"]:
        # Register today's URL
        today_url = None
        if zone_key == "JP-TH":
            today_url = f"https://setsuden.nw.tohoku-epco.co.jp/common/demand/area_tso_yosoku_{datestamp_today}.csv"
            data_path = Path(BASE_PATH_TO_MOCK, "area_tso_yosoku_20250416.csv")
        elif zone_key == "JP-TK":
            today_url = "https://www4.tepco.co.jp/forecast/html/images/AREA_YOSOKU.csv"
            data_path = Path(BASE_PATH_TO_MOCK, "AREA_YOSOKU.csv")
        elif zone_key == "JP-CB":
            today_url = "https://powergrid.chuden.co.jp/denki_yoho_content_data/keito_yosoku_cepco003.csv"
            data_path = Path(BASE_PATH_TO_MOCK, "keito_yosoku_cepco003.csv")
        elif zone_key == "JP-SK":
            today_url = "https://www.yonden.co.jp/nw/denkiyoho/supply_demand/csv/yosoku_today.csv"
            data_path = Path(BASE_PATH_TO_MOCK, "yosoku_today.csv")

        requests_mock.register_uri(GET, today_url, body=data_path.open("rb"))

        # Register tomorrow's URL (except for JP-CB which raises an exception)
        if zone_key != "JP-CB":
            tomorrow_url = None
            if zone_key == "JP-TH":
                tomorrow_url = "https://setsuden.nw.tohoku-epco.co.jp/common/demand/area_tso_yosoku_y.csv"
                data_path = Path(BASE_PATH_TO_MOCK, "area_tso_yosoku_y.csv")
            elif zone_key == "JP-TK":
                tomorrow_url = (
                    "https://www4.tepco.co.jp/forecast/html/images/AREA_ONCE_YOSOKU.csv"
                )
                data_path = Path(BASE_PATH_TO_MOCK, "AREA_ONCE_YOSOKU.csv")
            elif zone_key == "JP-SK":
                tomorrow_url = "https://www.yonden.co.jp/nw/denkiyoho/supply_demand/csv/yosoku_tomorrow.csv"
                data_path = Path(BASE_PATH_TO_MOCK, "yosoku_tomorrow.csv")

            requests_mock.register_uri(GET, tomorrow_url, body=data_path.open("rb"))

    if zone_key == "JP-HKD":
        data_path = Path(BASE_PATH_TO_MOCK, "20250415_hokkaido_yosoku.csv")
        requests_mock.register_uri(
            GET,
            re.compile(forecast_url[zone_key]),
            body=data_path.open("rb"),
        )

    elif zone_key == "JP-HR":
        data_path = Path(BASE_PATH_TO_MOCK, "yosoku_05_20250415.csv")
        requests_mock.register_uri(
            GET,
            re.compile(forecast_url[zone_key]),
            body=data_path.open("rb"),
        )

    elif zone_key == "JP-KN":
        data_path = Path(BASE_PATH_TO_MOCK, "20250416_yosoku.csv")
        requests_mock.register_uri(
            GET,
            re.compile(forecast_url[zone_key]),
            body=data_path.open("rb"),
        )

    elif zone_key == "JP-CG":
        data_zip_file = Path(BASE_PATH_TO_MOCK, "202504_jyukyu2_chugoku.zip")
        with open(data_zip_file, "rb") as zip_file:
            zip_content = zip_file.read()
        requests_mock.register_uri(
            GET,
            re.compile(forecast_url[zone_key]),
            content=zip_content,
        )

    elif zone_key == "JP-KY":
        data_path = Path(BASE_PATH_TO_MOCK, "21110_TSO9_0_20250407.csv")
        requests_mock.register_uri(
            GET,
            re.compile(forecast_url[zone_key]),
            body=data_path.open("rb"),
        )

    elif zone_key == "JP-ON":
        data_path = Path(BASE_PATH_TO_MOCK, "jukyu_yosoku_20250415.csv")
        requests_mock.register_uri(
            GET,
            re.compile(forecast_url[zone_key]),
            body=data_path.open("rb"),
        )

    # Run function under test
    assert snapshot == fetch_generation_forecast(
        zone_key=zone_key,
        session=session,
        target_datetime=datetime(
            2025, 4, 16, 12, 0
        ),  # the mock files were extracted this date
    )


@pytest.mark.parametrize(
    "zone_key",
    [
        "JP-CB",
        "JP-CG",
        "JP-HKD",
        "JP-HR",
        "JP-KN",
        "JP-KY",
        "JP-ON",
        "JP-SK",
        "JP-TH",
        "JP-TK",
    ],
)
@freeze_time("2025-04-16")  # because the mocks are all around this date
def test_snapshot_fetch_consumption_forecast(
    requests_mock, session, snapshot, zone_key
):
    datestamp_today = datetime.now().strftime("%Y%m%d")
    BASE_PATH_TO_MOCK = Path("electricitymap/contrib/parsers/tests/mocks/" + zone_key)

    forecast_url = {
        "JP-HKD": r"http://denkiyoho\.hepco\.co\.jp/area/data/\d{8}_hokkaido_yosoku\.csv",
        "JP-HR": r"https://www\.rikuden\.co\.jp/nw/denki-yoho/csv/yosoku_05_\d{8}\.csv",
        "JP-KN": r"https://www\.kansai-td\.co\.jp/interchange/denkiyoho/imbalance/\d{8}_yosoku\.csv",
        "JP-CG": r"https://www\.energia\.co\.jp/nw/jukyuu/sys/\d{6}_jyukyu2_chugoku\.zip",
        "JP-KY": r"https://www\.kyuden\.co\.jp/td_power_usages/csv/kouhyo/imbalance/21110_TSO9_0_\d{8}\.csv\?a=\d{8}%5Cd6",
        "JP-ON": r"http://www\.okiden\.co\.jp/denki2/dem_pg/csv/jukyu_yosoku_\d{8}\.csv",
    }

    # For zones with different URLs for today vs tomorrow
    if zone_key in ["JP-TH", "JP-TK", "JP-CB", "JP-SK"]:
        # Register today's URL
        today_url = None
        if zone_key == "JP-TH":
            today_url = f"https://setsuden.nw.tohoku-epco.co.jp/common/demand/area_tso_yosoku_{datestamp_today}.csv"
            data_path = Path(BASE_PATH_TO_MOCK, "area_tso_yosoku_20250416.csv")
        elif zone_key == "JP-TK":
            today_url = "https://www4.tepco.co.jp/forecast/html/images/AREA_YOSOKU.csv"
            data_path = Path(BASE_PATH_TO_MOCK, "AREA_YOSOKU.csv")
        elif zone_key == "JP-CB":
            today_url = "https://powergrid.chuden.co.jp/denki_yoho_content_data/keito_yosoku_cepco003.csv"
            data_path = Path(BASE_PATH_TO_MOCK, "keito_yosoku_cepco003.csv")
        elif zone_key == "JP-SK":
            today_url = "https://www.yonden.co.jp/nw/denkiyoho/supply_demand/csv/yosoku_today.csv"
            data_path = Path(BASE_PATH_TO_MOCK, "yosoku_today.csv")

        requests_mock.register_uri(GET, today_url, body=data_path.open("rb"))

        # Register tomorrow's URL (except for JP-CB which raises an exception)
        if zone_key != "JP-CB":
            tomorrow_url = None
            if zone_key == "JP-TH":
                tomorrow_url = "https://setsuden.nw.tohoku-epco.co.jp/common/demand/area_tso_yosoku_y.csv"
                data_path = Path(BASE_PATH_TO_MOCK, "area_tso_yosoku_y.csv")
            elif zone_key == "JP-TK":
                tomorrow_url = (
                    "https://www4.tepco.co.jp/forecast/html/images/AREA_ONCE_YOSOKU.csv"
                )
                data_path = Path(BASE_PATH_TO_MOCK, "AREA_ONCE_YOSOKU.csv")
            elif zone_key == "JP-SK":
                tomorrow_url = "https://www.yonden.co.jp/nw/denkiyoho/supply_demand/csv/yosoku_tomorrow.csv"
                data_path = Path(BASE_PATH_TO_MOCK, "yosoku_tomorrow.csv")

            requests_mock.register_uri(GET, tomorrow_url, body=data_path.open("rb"))

    if zone_key == "JP-HKD":
        data_path = Path(BASE_PATH_TO_MOCK, "20250415_hokkaido_yosoku.csv")
        requests_mock.register_uri(
            GET,
            re.compile(forecast_url[zone_key]),
            body=data_path.open("rb"),
        )

    elif zone_key == "JP-HR":
        data_path = Path(BASE_PATH_TO_MOCK, "yosoku_05_20250415.csv")
        requests_mock.register_uri(
            GET,
            re.compile(forecast_url[zone_key]),
            body=data_path.open("rb"),
        )

    elif zone_key == "JP-KN":
        data_path = Path(BASE_PATH_TO_MOCK, "20250416_yosoku.csv")
        requests_mock.register_uri(
            GET,
            re.compile(forecast_url[zone_key]),
            body=data_path.open("rb"),
        )

    elif zone_key == "JP-CG":
        data_zip_file = Path(BASE_PATH_TO_MOCK, "202504_jyukyu2_chugoku.zip")
        with open(data_zip_file, "rb") as zip_file:
            zip_content = zip_file.read()
        requests_mock.register_uri(
            GET,
            re.compile(forecast_url[zone_key]),
            content=zip_content,
        )

    elif zone_key == "JP-KY":
        data_path = Path(BASE_PATH_TO_MOCK, "21110_TSO9_0_20250407.csv")
        requests_mock.register_uri(
            GET,
            re.compile(forecast_url[zone_key]),
            body=data_path.open("rb"),
        )

    elif zone_key == "JP-ON":
        data_path = Path(BASE_PATH_TO_MOCK, "jukyu_yosoku_20250415.csv")
        requests_mock.register_uri(
            GET,
            re.compile(forecast_url[zone_key]),
            body=data_path.open("rb"),
        )

    # Run function under test
    assert snapshot == fetch_consumption_forecast(
        zone_key=zone_key,
        session=session,
        target_datetime=datetime(
            2025, 4, 16, 12, 0
        ),  # the mock files were extracted this date
    )


def _register_jepx(requests_mock):
    for fiscal_year in (2025, 2026):
        requests_mock.register_uri(
            GET,
            JEPX_SPOT_URL.format(fiscal_year=fiscal_year),
            content=(JEPX_MOCKS / f"spot_{fiscal_year}.csv").read_bytes(),
        )


def test_fetch_price_day_ahead(requests_mock, session, snapshot):
    _register_jepx(requests_mock)

    rows = fetch_price_day_ahead(
        ZoneKey("JP-TK"),
        session,
        target_datetime=datetime(2026, 10, 1, tzinfo=timezone.utc),
    )

    assert snapshot == rows
    # 2026-10-01T00:00Z is 09:00 JST, so the window is JST 2026-09-30 and 2026-10-01.
    assert len(rows) == 96
    # JST 2026-10-01 Period 1 starts at 00:00 JST.
    first_of_target_day = rows[48]
    assert first_of_target_day["datetime"] == datetime(
        2026, 9, 30, 15, tzinfo=timezone.utc
    )
    assert first_of_target_day["price"] == 24010  # 24.01 JPY/kWh.
    assert rows[0]["datetime"] == datetime(2026, 9, 29, 15, tzinfo=timezone.utc)
    assert rows[-1]["end_datetime"] == datetime(2026, 10, 1, 15, tzinfo=timezone.utc)
    for row in rows:
        assert row["end_datetime"] - row["datetime"] == timedelta(minutes=30)
        assert row["datetime"].utcoffset() == timedelta(0)
        assert row["end_datetime"].utcoffset() == timedelta(0)
        assert row["auction"] == DayAheadAuction.JEPX_DA
        assert row["currency"] == "JPY"
        assert row["publishedAt"] is None


@freeze_time("2026-09-30 16:00:00")  # 2026-10-01T01:00 JST.
def test_fetch_price_day_ahead_live_includes_tomorrow(requests_mock, session):
    _register_jepx(requests_mock)

    rows = fetch_price_day_ahead(ZoneKey("JP-KY"), session)

    # Today and tomorrow in JST.
    assert rows[0]["datetime"] == datetime(2026, 9, 30, 15, tzinfo=timezone.utc)
    assert rows[-1]["end_datetime"] == datetime(2026, 10, 2, 15, tzinfo=timezone.utc)
    assert len(rows) == 96


def test_fetch_price_day_ahead_spans_fiscal_years(requests_mock, session):
    _register_jepx(requests_mock)

    rows = fetch_price_day_ahead(
        ZoneKey("JP-HKD"),
        session,
        target_datetime=datetime(2026, 4, 1, tzinfo=timezone.utc),
    )

    assert [request.url for request in requests_mock.request_history] == [
        JEPX_SPOT_URL.format(fiscal_year=2025),
        JEPX_SPOT_URL.format(fiscal_year=2026),
    ]
    # JST 2026-03-31 from FY2025 and 2026-04-01 from FY2026.
    assert len(rows) == 96
    assert rows[0]["datetime"] == datetime(2026, 3, 30, 15, tzinfo=timezone.utc)
    assert rows[-1]["end_datetime"] == datetime(2026, 4, 1, 15, tzinfo=timezone.utc)


def test_fetch_price_day_ahead_jp_on_raises(session):
    with pytest.raises(NotImplementedError):
        fetch_price_day_ahead(ZoneKey("JP-ON"), session)
