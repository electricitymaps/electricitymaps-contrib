#!/usr/bin/env python3

import datetime
import json
import logging
import pprint
import re

import arrow
import pandas as pd
import requests
from bs4 import BeautifulSoup

from parsers.lib.config import refetch_frequency

TIMEZONE = "Asia/Seoul"
REAL_TIME_URL = "https://new.kpx.or.kr/powerinfoSubmain.es?mid=a10606030000"
PRICE_URL = "https://new.kpx.or.kr/smpInland.es?mid=a10606080100&device=pc"
LONG_TERM_PRODUCTION_URL = (
    "https://new.kpx.or.kr/powerSource.es?mid=a10606030000&device=chart"
)

pp = pprint.PrettyPrinter(indent=4)

#### Classification of New & Renewable Energy Sources ####
# Source: https://cms.khnp.co.kr/eng/content/563/main.do?mnCd=EN040101
# New energy: Hydrogen, Fuel Cell, Coal liquefied or gasified energy, and vacuum residue gasified energy, etc.
# Renewable: Solar, Wind power, Water power, ocean energy, Geothermal, Bio energy, etc.

# src: https://stackoverflow.com/questions/3463930/how-to-round-the-minute-of-a-datetime-object
def time_floor(time, delta, epoch=None):
    if epoch is None:
        epoch = datetime.datetime(1970, 1, 1, tzinfo=time.tzinfo)
    mod = (time - epoch) % delta
    return time - mod


def extract_chart_data(html):
    """
    Extracts generation breakdown chart data from the source code of the page.
    """
    # Extract object with data
    data_source = re.search(r"var ictArr = (\[\{.+\}\]);", html).group(1)
    # Un-quoted keys ({key:"value"}) are valid JavaScript but not valid JSON (which requires {"key":"value"}).
    # Will break if other keys than these are introduced. Alternatively, use a JSON5 library (JSON5 allows un-quoted keys)
    data_source = re.sub(
        r'"(localCoal|newRenewable|oil|once|gas|nuclearPower|coal|regDate|raisingWater|waterPower|seq)"',
        r'"\1"',
        data_source,
    )
    json_obj = json.loads(data_source)

    timed_data = {}

    for item in json_obj:
        if item["regDate"] == "0":
            break

        date = datetime.datetime.strptime(item["regDate"], "%Y-%m-%d %H:%M")
        date = arrow.get(date, TIMEZONE).datetime

        timed_data[date] = {
            "coal": round(float(item["coal"]) + float(item["localCoal"]), 5),
            "gas": round(float(item["gas"]), 5),
            "hydro": round(float(item["waterPower"]), 5),
            "nuclear": round(float(item["nuclearPower"]), 5),
            "oil": round(float(item["oil"]), 5),
            "renewable": round(float(item["newRenewable"]), 5),
            "pumpedHydro": round(float(item["raisingWater"]), 5),
        }

    return timed_data


@refetch_frequency(datetime.timedelta(minutes=5))
def fetch_consumption(
    zone_key="KR",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
) -> dict:
    """
    Fetches consumption.
    """

    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    r = session or requests.session()
    url = REAL_TIME_URL

    response = r.get(url)
    assert response.status_code == 200

    soup = BeautifulSoup(response.text, "html.parser")
    consumption_title = soup.find("th", string=re.compile(r"\s*현재부하\s*"))
    consumption_val = float(
        consumption_title.find_next_sibling().text.split()[0].replace(",", "")
    )

    consumption_date_list = soup.find("p", {"class": "info_top"}).text.split(" ")[:2]
    consumption_date_list[0] = consumption_date_list[0].replace(".", "-").split("(")[0]
    consumption_date = datetime.datetime.strptime(
        " ".join(consumption_date_list), "%Y-%m-%d %H:%M"
    )
    consumption_date = arrow.get(consumption_date, TIMEZONE).datetime

    data = {
        "consumption": consumption_val,
        "datetime": consumption_date,
        "source": url,
        "zoneKey": zone_key,
    }

    return data


@refetch_frequency(datetime.timedelta(hours=1))
def fetch_price(
    zone_key="KR",
    session=None,
    target_datetime: datetime.datetime = None,
    logger=logging.getLogger(__name__),
):

    first_available_date = time_floor(
        arrow.now(TIMEZONE).shift(days=-6), datetime.timedelta(days=1)
    ).shift(hours=1)

    if target_datetime is not None and target_datetime < first_available_date:
        raise NotImplementedError(
            "This parser is not able to parse dates more than one week in the past."
        )

    if target_datetime is None:
        target_datetime = arrow.now(TIMEZONE).datetime

    r = session or requests.session()
    url = PRICE_URL

    response = r.get(url)
    assert response.status_code == 200

    all_data = []
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
            price_value = table_prices.iloc[row_idx, col_idx]

            data = {
                "zoneKey": zone_key,
                "datetime": arw_day.datetime,
                "currency": "KRW",
                "price": price_value,
                "source": "new.kpx.or.kr",
            }

            all_data.append(data)

    return all_data


def get_long_term_prod_data(
    session=None, target_datetime: datetime.datetime = None
) -> dict:
    target_datetime_formatted_daily = target_datetime.strftime("%Y-%m-%d")

    r = session or requests.session()

    # CSRF token is needed to access the production data
    r.get(LONG_TERM_PRODUCTION_URL)
    cookies_dict = r.cookies.get_dict()

    payload = {
        "mid": "a10606030000",
        "device": "chart",
        "view_sdate": target_datetime_formatted_daily,
        "view_edate": target_datetime_formatted_daily,
        "_csrf": cookies_dict["XSRF-TOKEN"],
    }

    res = r.post(LONG_TERM_PRODUCTION_URL, payload)

    assert res.status_code == 200

    all_data = []

    soup = BeautifulSoup(res.text, "html.parser")
    table_rows = soup.find_all("tr")[1:]

    for row in table_rows:

        sanitized_date = [value[:-1] for value in row.find_all("td")[0].text.split(" ")]
        curr_prod_datetime_string = (
            "-".join(sanitized_date[:3]) + "T" + ":".join(sanitized_date[3:]) + ":00"
        )
        arw_datetime = arrow.get(
            curr_prod_datetime_string, "YYYY-MM-DDTHH:mm:ss", tzinfo=TIMEZONE
        ).datetime

        data = {
            "zoneKey": "KR",
            "datetime": arw_datetime,
            "capacity": {},
            "production": {},
            "storage": {},
            "source": "https://new.kpx.or.kr",
        }

        row_values = row.find_all("td")
        production_values = [
            int("".join(value.text.split(","))) for value in row_values[1:]
        ]

        # order of production_values
        # 0. other, 1. gas, 2. renewable, 3. coal, 4. nuclear
        # other can be negative as well as positive due to pumped hydro

        data["datetime"] = arw_datetime
        data["production"]["unknown"] = production_values[0] + production_values[2]
        data["production"]["gas"] = production_values[1]
        data["production"]["coal"] = production_values[3]
        data["production"]["nuclear"] = production_values[4]

        all_data.append(data)

    return all_data


def get_granular_real_time_prod_data(session=None) -> dict:
    r0 = session or requests.session()
    res_0 = r0.get(REAL_TIME_URL)
    chart_data = extract_chart_data(res_0.text)

    return chart_data


@refetch_frequency(datetime.timedelta(minutes=5))
def fetch_production(
    zone_key="KR",
    session=None,
    target_datetime: datetime.datetime = None,
    logger: logging.Logger = logging.getLogger(__name__),
) -> dict:

    if target_datetime is not None and target_datetime < arrow.get(
        2021, 12, 22, 0, 0, 0, tzinfo=TIMEZONE
    ):
        raise NotImplementedError(
            "This parser is not able to parse dates before 2021-12-22."
        )

    if target_datetime is None:
        target_datetime = arrow.now(TIMEZONE).datetime

    all_data = []

    if target_datetime.date() == arrow.now(TIMEZONE).date():
        chart_data = get_granular_real_time_prod_data(session=session)

        for datetime_key, chart_data_values in chart_data.items():
            data = {
                "zoneKey": "KR",
                "datetime": datetime_key,
                "capacity": {},
                "production": {},
                "storage": {},
                "source": "https://new.kpx.or.kr",
            }

            data["storage"]["hydro"] = chart_data_values["pumpedHydro"]

            data["production"]["coal"] = chart_data_values["coal"]
            data["production"]["gas"] = chart_data_values["gas"]
            data["production"]["nuclear"] = chart_data_values["nuclear"]
            data["production"]["oil"] = chart_data_values["oil"]
            data["production"]["hydro"] = chart_data_values["hydro"]
            data["production"]["unknown"] = chart_data_values["renewable"]

            all_data.append(data)

    else:
        all_data = get_long_term_prod_data(
            session=session, target_datetime=target_datetime
        )

    return all_data


if __name__ == "__main__":
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
