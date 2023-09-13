#!/usr/bin/env python3

import json
import logging
import pprint
import re
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Dict, List, Optional, Union

import arrow
import pandas as pd
from bs4 import BeautifulSoup
from pytz import timezone
from requests import Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.lib.models.event_lists import (
    PriceList,
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import ProductionMix, StorageMix
from parsers.lib.config import refetch_frequency

TIMEZONE = timezone("Asia/Seoul")
KR_CURRENCY = "KRW"
KR_SOURCE = "new.kpx.or.kr"
REAL_TIME_URL = "https://new.kpx.or.kr/powerinfoSubmain.es?mid=a10606030000"
PRICE_URL = "https://new.kpx.or.kr/smpInland.es?mid=a10606080100&device=pc"
HISTORICAL_PRODUCTION_URL = (
    "https://new.kpx.or.kr/powerSource.es?mid=a10606030000&device=chart"
)

pp = pprint.PrettyPrinter(indent=4)

#### Classification of New & Renewable Energy Sources ####
# Source: https://cms.khnp.co.kr/eng/content/563/main.do?mnCd=EN040101
# New energy: Hydrogen, Fuel Cell, Coal liquefied or gasified energy, and vacuum residue gasified energy, etc.
# Renewable: Solar, Wind power, Water power, ocean energy, Geothermal, Bio energy, etc.


@refetch_frequency(timedelta(minutes=5))
def fetch_consumption(
    zone_key: ZoneKey = ZoneKey("KR"),
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> List[dict]:
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    logger.debug(f"Fetching consumption data from {REAL_TIME_URL}")

    response = session.get(REAL_TIME_URL, verify=False)
    assert response.status_code == 200

    soup = BeautifulSoup(response.text, "html.parser")
    consumption_title = soup.find("th", string=re.compile(r"\s*현재부하\s*"))
    consumption_val = float(
        consumption_title.find_next_sibling().text.split()[0].replace(",", "")
    )

    consumption_date_list = soup.find("p", {"class": "info_top"}).text.split(" ")[:2]
    consumption_date_list[0] = consumption_date_list[0].replace(".", "-").split("(")[0]
    consumption_date = TIMEZONE.localize(
        datetime.strptime(" ".join(consumption_date_list), "%Y-%m-%d %H:%M")
    )

    consumption_list = TotalConsumptionList(logger)
    consumption_list.append(
        zoneKey=zone_key,
        datetime=consumption_date,
        source=KR_SOURCE,
        consumption=consumption_val,
    )

    return consumption_list.to_list()


@refetch_frequency(timedelta(hours=1))
def fetch_price(
    zone_key: ZoneKey = ZoneKey("KR"),
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> List[dict]:
    first_available_date = (
        arrow.now(TIMEZONE).shift(days=-6).floor("day").shift(hours=1)
    )

    if target_datetime is not None and target_datetime < first_available_date:
        raise NotImplementedError(
            "This parser is not able to parse dates more than one week in the past."
        )

    if target_datetime is None:
        target_datetime = arrow.now(TIMEZONE).datetime

    logger.debug(f"Fetching price data from {PRICE_URL}")

    response = session.get(PRICE_URL, verify=False)
    assert response.status_code == 200

    price_list = PriceList(logger)

    table_prices = pd.read_html(response.text, header=0)[0]
    for col_idx in range(1, table_prices.shape[1]):
        for row_idx in range(24):
            day = col_idx
            hour = row_idx + 1

            if hour == 24:
                hour = 0
                day += 1

            arw_day = (
                arrow.now(TIMEZONE)
                .shift(days=-1 * (7 - day))
                .replace(hour=hour, minute=0, second=0, microsecond=0)
            )
            price_value = (
                table_prices.iloc[row_idx, col_idx] * 1000
            )  # Convert from Won/kWh to Won/MWh

            price_list.append(
                zoneKey=zone_key,
                datetime=arw_day.datetime,
                source=KR_SOURCE,
                price=price_value,
                currency=KR_CURRENCY,
            )

    return price_list.to_list()


def get_historical_prod_data(
    zone_key: ZoneKey = ZoneKey("KR"),
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> ProductionBreakdownList:
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

    assert res.status_code == 200

    production_list = ProductionBreakdownList(logger)
    soup = BeautifulSoup(res.text, "html.parser")
    table_rows = soup.find_all("tr")[1:]
    for row in table_rows:
        sanitized_date = [value[:-1] for value in row.find_all("td")[0].text.split(" ")]
        curr_prod_datetime_string = (
            "-".join(sanitized_date[:3]) + "T" + ":".join(sanitized_date[3:]) + ":00"
        )
        dt = arrow.get(
            curr_prod_datetime_string, "YYYY-MM-DDTHH:mm:ss", tzinfo=TIMEZONE
        ).datetime

        row_values = row.find_all("td")
        production_values = [
            int("".join(value.text.split(","))) for value in row_values[1:]
        ]

        # order of production_values
        # 0. other, 1. gas, 2. renewable, 3. coal, 4. nuclear
        # other can be negative as well as positive due to pumped hydro
        production_mix = ProductionMix()
        production_mix.add_value("unknown", production_values[0] + production_values[2])
        production_mix.add_value("gas", production_values[1])
        production_mix.add_value("coal", production_values[3])
        production_mix.add_value("nuclear", production_values[4])
        production_list.append(
            zoneKey=zone_key,
            datetime=dt,
            source=KR_SOURCE,
            production=production_mix,
        )
    return production_list


def get_real_time_prod_data(
    zone_key: ZoneKey = ZoneKey("KR"),
    session: Session = Session(),
    logger: Logger = getLogger(__name__),
) -> ProductionBreakdownList:
    res = session.get(REAL_TIME_URL, verify=False)

    production_list = ProductionBreakdownList(logger)

    # Extract object with data
    data_source = re.search(r"var ictArr = (\[\{.+\}\]);", res.text).group(1)
    # Un-quoted keys ({key:"value"}) are valid JavaScript but not valid JSON (which requires {"key":"value"}).
    # Will break if other keys than these are introduced. Alternatively, use a JSON5 library (JSON5 allows un-quoted keys)
    data_source = re.sub(
        r'"(localCoal|newRenewable|oil|once|gas|nuclearPower|coal|regDate|raisingWater|waterPower|seq)"',
        r'"\1"',
        data_source,
    )
    json_obj = json.loads(data_source)

    for item in json_obj:
        if item["regDate"] == "0":
            break

        dt = TIMEZONE.localize(datetime.strptime(item["regDate"], "%Y-%m-%d %H:%M"))

        production_mix = ProductionMix()
        production_mix.add_value(
            "coal",
            round(float(item["coal"]) + float(item["localCoal"]), 5),
        )
        production_mix.add_value(
            "gas",
            round(float(item["gas"]), 5),
        )
        production_mix.add_value(
            "hydro",
            round(float(item["waterPower"]), 5),
        )
        production_mix.add_value(
            "nuclear",
            round(float(item["nuclearPower"]), 5),
        )
        production_mix.add_value("oil", round(float(item["oil"]), 5))
        production_mix.add_value("unknown", round(float(item["newRenewable"]), 5))
        storage_mix = StorageMix()
        storage_mix.add_value("hydro", -round(float(item["raisingWater"]), 5))
        production_list.append(
            zoneKey=zone_key,
            datetime=dt,
            source=KR_SOURCE,
            production=production_mix,
            storage=storage_mix,
        )

    return production_list


@refetch_frequency(timedelta(minutes=5))
def fetch_production(
    zone_key: ZoneKey = ZoneKey("KR"),
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> List[dict]:
    first_available_date = arrow.get(2021, 12, 22, 0, 0, 0, tzinfo=TIMEZONE)
    if target_datetime is not None and target_datetime < first_available_date:
        raise NotImplementedError(
            "This parser is not able to parse dates before 2021-12-22."
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
    logger = getLogger(__name__)
    logging.basicConfig(level=logging.DEBUG)
    # Testing datetime on specific date
    target_datetime = arrow.get(2022, 2, 7, 16, 35, 0, tzinfo=TIMEZONE).datetime

    print("fetch_production() ->")
    # pp.pprint(fetch_production(target_datetime=target_datetime))
    pp.pprint(fetch_production())

    print("fetch_price() -> ")
    # pp.pprint(fetch_price(target_datetime=target_datetime))
    pp.pprint(fetch_price())

    print("fetch_consumption() -> ")
    pp.pprint(fetch_consumption())
