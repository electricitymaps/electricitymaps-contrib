import json
import re
from datetime import datetime, time, timedelta
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

import pandas as pd
from bs4 import BeautifulSoup
from requests import Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.lib.models.event_lists import (
    PriceList,
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import ProductionMix, StorageMix
from parsers.lib.config import refetch_frequency, use_proxy
from parsers.lib.exceptions import ParserException

TIMEZONE = ZoneInfo("Asia/Seoul")
KR_CURRENCY = "KRW"
KR_SOURCE = "new.kpx.or.kr"
REAL_TIME_URL = "https://new.kpx.or.kr/powerinfoSubmain.es?mid=a10606030000"
PRICE_URL = "https://new.kpx.or.kr/smpInland.es?mid=a10606080100&device=pc"
HISTORICAL_PRODUCTION_URL = (
    "https://new.kpx.or.kr/powerSource.es?mid=a10606030000&device=chart"
)

#### Classification of New & Renewable Energy Sources ####
#
# Source: https://cms.khnp.co.kr/eng/content/563/main.do?mnCd=EN040101
# New energy: Hydrogen, Fuel Cell, Coal liquefied or gasified energy, and vacuum residue gasified energy, etc.
# Renewable: Solar, Wind power, Water power, ocean energy, Geothermal, Bio energy, etc.
#
PRODUCTION_MAPPING = {
    "coal": "coal",
    "localCoal": "coal",
    "gas": "gas",
    "oil": "oil",
    "nuclearPower": "nuclear",
    "waterPower": "hydro",
    "windPower": "wind",
    "sunlight": "solar",
    "newRenewable": "unknown",
}
STORAGE_MAPPING = {
    "raisingWater": "hydro",
}
IGNORE_LIST = [
    "ppa",
    "btm",
    "newRenewablePlusWindPower",
    "once",
    "regDate",
    "seq",
]


@use_proxy(country_code="KR")
def fetch_consumption(
    zone_key: ZoneKey = ZoneKey("KR"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    session = session or Session()
    if target_datetime:
        raise ParserException(
            "KPX.py",
            "This parser is not yet able to parse past dates",
            zone_key,
        )

    logger.debug(f"Fetching consumption data from {REAL_TIME_URL}")
    response = session.get(REAL_TIME_URL, verify=False)
    assert response.ok

    soup = BeautifulSoup(response.text, "html.parser")

    # value_text looks like: 64,918 MW
    value_text = soup.find("td", {"id": "load"}).text
    value = float(value_text.split()[0].replace(",", ""))

    # dt_text looks like: 2025.01.05(일) 23:10 새로고침
    dt_text = soup.find("p", {"class": "info_top"}).text
    dt_parts = dt_text.split(" ")[:2]
    dt_string = dt_parts[0].split("(")[0] + " " + dt_parts[1]
    dt = datetime.strptime(dt_string, "%Y.%m.%d %H:%M").replace(tzinfo=TIMEZONE)

    consumption_list = TotalConsumptionList(logger)
    consumption_list.append(
        zoneKey=zone_key,
        datetime=dt,
        source=KR_SOURCE,
        consumption=value,
    )

    return consumption_list.to_list()


@refetch_frequency(timedelta(hours=167))
@use_proxy(country_code="KR")
def fetch_price(
    zone_key: ZoneKey = ZoneKey("KR"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    session = session or Session()
    now = datetime.now(tz=TIMEZONE)
    target_datetime = (
        now if target_datetime is None else target_datetime.astimezone(TIMEZONE)
    )

    today = datetime.combine(now, time(), tzinfo=TIMEZONE)  # truncates to day
    first_available_api_date = today - timedelta(days=6) + timedelta(hours=1)
    if target_datetime < first_available_api_date:
        raise ParserException(
            "KPX.py",
            "This parser is not able to parse dates more than one week in the past.",
            zone_key,
        )

    logger.debug(f"Fetching price data from {PRICE_URL}")
    response = session.get(PRICE_URL, verify=False)
    assert response.ok

    price_list = PriceList(logger)

    table_prices = pd.read_html(response.text, header=0)[0]
    for col_idx in range(1, table_prices.shape[1]):
        for row_idx in range(24):
            day = col_idx
            hour = row_idx + 1

            if hour == 24:
                hour = 0
                day += 1

            dt = (now + timedelta(days=-1 * (7 - day))).replace(
                hour=hour, minute=0, second=0, microsecond=0
            )

            price_value = (
                table_prices.iloc[row_idx, col_idx] * 1000
            )  # Convert from Won/kWh to Won/MWh

            price_list.append(
                zoneKey=zone_key,
                datetime=dt,
                source=KR_SOURCE,
                price=price_value,
                currency=KR_CURRENCY,
            )

    return price_list.to_list()


def parse_chart_prod_data(
    raw_data: str,
    zone_key: ZoneKey = ZoneKey("KR"),
    logger: Logger = getLogger(__name__),
) -> ProductionBreakdownList:
    production_list = ProductionBreakdownList(logger)

    # Extract object with data
    json_string = re.search(r"var ictArr = (\[\{.+\}\]);", raw_data).group(1)
    json_obj = json.loads(json_string)

    for item in json_obj:
        if item["regDate"] == "0":
            break

        dt = datetime.strptime(item["regDate"], "%Y-%m-%d %H:%M").replace(
            tzinfo=TIMEZONE
        )

        production_mix = ProductionMix()
        storage_mix = StorageMix()
        for item_key, item_value in item.items():
            if item_key in IGNORE_LIST:
                continue
            elif item_key in PRODUCTION_MAPPING:
                production_mix.add_value(
                    PRODUCTION_MAPPING[item_key],
                    float(item_value),
                    correct_negative_with_zero=True,
                )
            elif item_key in STORAGE_MAPPING:
                storage_mix.add_value(STORAGE_MAPPING[item_key], -float(item_value))
            else:
                logger.warning(f"Unknown mode {item_key} with value {item_value}")

        production_list.append(
            zoneKey=zone_key,
            datetime=dt,
            source=KR_SOURCE,
            production=production_mix,
            storage=storage_mix,
        )

    return production_list


def get_real_time_prod_data(
    zone_key: ZoneKey = ZoneKey("KR"),
    session: Session | None = None,
    logger: Logger = getLogger(__name__),
) -> ProductionBreakdownList:
    session = session or Session()
    res = session.get(REAL_TIME_URL, verify=False)
    return parse_chart_prod_data(res.text, zone_key, logger)


def get_historical_prod_data(
    zone_key: ZoneKey = ZoneKey("KR"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> ProductionBreakdownList:
    session = session or Session()
    target_datetime_formatted_daily = target_datetime.strftime("%Y-%m-%d")

    # CSRF token is needed to access the production data
    logger.debug(
        f"Fetching CSRF token to access production data from {HISTORICAL_PRODUCTION_URL}"
    )
    session.get(HISTORICAL_PRODUCTION_URL, verify=False)
    cookies_dict = session.cookies.get_dict()

    payload = {
        "mid": "a10606030000",
        "device": "chart",
        "view_sdate": target_datetime_formatted_daily,
        "view_edate": target_datetime_formatted_daily,
        "_csrf": cookies_dict.get("XSRF-TOKEN", None),
    }

    logger.debug(f"Fetching production data from {HISTORICAL_PRODUCTION_URL}")
    res = session.post(HISTORICAL_PRODUCTION_URL, payload)
    assert res.ok

    return parse_chart_prod_data(res.text, zone_key, logger)


@refetch_frequency(timedelta(days=1))
@use_proxy(country_code="KR")
def fetch_production(
    zone_key: ZoneKey = ZoneKey("KR"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    session = session or Session()
    first_available_date = datetime(2021, 12, 22, 0, 0, 0, tzinfo=TIMEZONE)
    if target_datetime is not None and target_datetime < first_available_date:
        raise ParserException(
            "KPX.py",
            "This parser is not able to parse dates before 2021-12-22.",
            zone_key,
        )

    if target_datetime is None:
        production_list = get_real_time_prod_data(
            zone_key=zone_key, session=session, logger=logger
        )
    else:
        production_list = get_historical_prod_data(
            zone_key=zone_key,
            session=session,
            target_datetime=target_datetime,
            logger=logger,
        )
    return production_list.to_list()


if __name__ == "__main__":
    target_datetime = datetime(2022, 2, 7, 16, 35, 0, tzinfo=TIMEZONE)

    print("fetch_production() ->")
    print(fetch_production())
    print(fetch_production(target_datetime=target_datetime))

    print("fetch_price() -> ")
    print(fetch_price())

    print("fetch_consumption() -> ")
    print(fetch_consumption())
