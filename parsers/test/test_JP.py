"""Test for JP parsers"""

import re
from pathlib import Path

import pytest
from requests_mock import GET

from parsers.JP import fetch_generation_forecast


@pytest.mark.parametrize(
    "zone_key",
    [
        "JP-CB",
        "JP-CG",
        "JP-HKD",
        "JP-HR",
        "JP-KN",
        # "JP-KY",
        "JP-ON",
        "JP-SK",
        "JP-TH",
        "JP-TK",
    ],
)
def test_snapshot_fetch_generation_forecast(adapter, session, snapshot, zone_key):
    test_datestamp_today = "20250416"
    # test_datestamp_tomorrow = "20250417"
    BASE_PATH_TO_MOCK = Path("parsers/test/mocks/" + zone_key)

    forecast_url = {
        "JP-HKD": r"http://denkiyoho\.hepco\.co\.jp/area/data/\d{8}_hokkaido_yosoku\.csv",
        "JP-HR": r"https://www\.rikuden\.co\.jp/nw/denki-yoho/csv/yosoku_05_\d{8}\.csv",
        "JP-KN": r"https://www\.kansai-td\.co\.jp/interchange/denkiyoho/imbalance/\d{8}_yosoku\.csv",
        "JP-CG": r"https://www\.energia\.co\.jp/nw/jukyuu/sys/\d{6}_jyukyu2_chugoku\.zip",
        # "JP-KY": r"https://www\.kyuden\.co\.jp/td_power_usages/csv/kouhyo/imbalance/21110_TSO9_0_\d{8}\.csv\?a=\d{14}",  # TODO why this
        "JP-ON": r"http://www\.okiden\.co\.jp/denki2/dem_pg/csv/jukyu_yosoku_\d{8}\.csv",
    }

    # For zones with different URLs for today vs tomorrow
    if zone_key in ["JP-TH", "JP-TK", "JP-CB", "JP-SK"]:
        # Register today's URL
        today_url = None
        if zone_key == "JP-TH":
            today_url = f"https://setsuden.nw.tohoku-epco.co.jp/common/demand/area_tso_yosoku_{test_datestamp_today}.csv"
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

        adapter.register_uri(GET, today_url, body=data_path.open("rb"))

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

            adapter.register_uri(GET, tomorrow_url, body=data_path.open("rb"))

    if zone_key == "JP-HKD":
        data_path = Path(BASE_PATH_TO_MOCK, "20250415_hokkaido_yosoku.csv")
        adapter.register_uri(
            GET,
            re.compile(forecast_url[zone_key]),
            body=data_path.open("rb"),
        )

    elif zone_key == "JP-HR":
        data_path = Path(BASE_PATH_TO_MOCK, "yosoku_05_20250415.csv")
        adapter.register_uri(
            GET,
            re.compile(forecast_url[zone_key]),
            body=data_path.open("rb"),
        )

    elif zone_key == "JP-KN":
        data_path = Path(BASE_PATH_TO_MOCK, "20250416_yosoku.csv")
        adapter.register_uri(
            GET,
            re.compile(forecast_url[zone_key]),
            body=data_path.open("rb"),
        )

    elif zone_key == "JP-CG":
        data_zip_file = Path(BASE_PATH_TO_MOCK, "202504_jyukyu2_chugoku.zip")
        with open(data_zip_file, "rb") as zip_file:
            zip_content = zip_file.read()
        adapter.register_uri(
            GET,
            re.compile(forecast_url[zone_key]),
            content=zip_content,
        )

    elif zone_key == "JP-KY":
        data_path = Path(BASE_PATH_TO_MOCK, "21110_TSO9_0_20250407.csv")
        adapter.register_uri(
            GET,
            re.compile(forecast_url[zone_key]),
            body=data_path.open("rb"),
        )

    elif zone_key == "JP-ON":
        data_path = Path(BASE_PATH_TO_MOCK, "jukyu_yosoku_20250415.csv")
        adapter.register_uri(
            GET,
            re.compile(forecast_url[zone_key]),
            body=data_path.open("rb"),
        )

    # Run function under test
    assert snapshot == fetch_generation_forecast(
        zone_key=zone_key,
        session=session,
    )
