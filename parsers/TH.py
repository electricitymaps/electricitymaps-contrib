import datetime as dt
import json
from logging import Logger, getLogger
from typing import List, Optional

import arrow
import pytz
import requests
from bs4 import BeautifulSoup

from parsers.lib.exceptions import ParserException

EGAT_GENERATION_URL = "https://www.sothailand.com/sysgen/ws/sysgen"
EGAT_URL = "www.egat.co.th"
MEA_PRICE_URL = "https://www.mea.or.th/en/profile/109/111"
MEA_URL = "www.mea.or.th"
TZ = "Asia/Bangkok"


def fetch_production(
    zone_key: str = "TH",
    session: Optional[requests.Session] = None,
    target_datetime: Optional[dt.datetime] = None,
    logger: Logger = getLogger(__name__),
) -> List[dict]:
    """Request the last known production mix (in MW) of a given country."""
    data = _fetch_data(_as_localtime(target_datetime), "actual")

    production = []
    for item in data:
        production.append(
            {
                "zoneKey": zone_key,
                "datetime": item["datetime"],
                # All mapped to 'unknown' because there is no available breakdown.
                "production": {"unknown": item["generation"]},
                "source": EGAT_URL,
            }
        )
    return production


def fetch_consumption(
    zone_key: str = "TH",
    session: Optional[requests.Session] = None,
    target_datetime: Optional[dt.datetime] = None,
    logger: Logger = getLogger(__name__),
) -> List[dict]:
    """
    Gets consumption for a specified zone.

    We use the same value as the production for now.
    But it would be better to include exchanged electricity data if available.
    """
    production = fetch_production(target_datetime=_as_localtime(target_datetime))
    consumption = []
    for item in production:
        item["consumption"] = item["production"]["unknown"]
        del item["production"]
        consumption.append(item)
    return consumption


def fetch_generation_forecast(
    zone_key: str = "TH",
    session: Optional[requests.Session] = None,
    target_datetime: Optional[dt.datetime] = None,
    logger: Logger = getLogger(__name__),
) -> List[dict]:
    """Gets generation forecast for specified zone."""
    data = _fetch_data(_as_localtime(target_datetime), "plan")

    production = []
    for item in data:
        production.append(
            {
                "zoneKey": zone_key,
                "datetime": item["datetime"],
                # All mapped to unknown as there is no available breakdown
                "production": {"unknown": item["generation"]},
                "source": EGAT_URL,
            }
        )
    return production


def _as_localtime(datetime):
    """
    If there is no datetime is given, returns the current datetime with timezone.
    Otherwise, it interprets the datetime as the representation of local time
    since the API server supposes the local timezone instead of UTC.
    """
    tzinfo = pytz.timezone(TZ)
    if datetime is None:
        return dt.datetime.now(tz=tzinfo)
    return datetime.astimezone(tzinfo)


def _fetch_data(target_datetime: dt.datetime, data_type: str) -> List[dict]:
    """Fetch actual or planning generation data from the EGAT API endpoint."""
    url = f"{EGAT_GENERATION_URL}/{data_type}"
    if target_datetime is None:
        target_datetime = arrow.now(TZ).datetime

    if data_type == "actual":
        params = {"name": "SYSTEM_GEN(MW)", "day": target_datetime.strftime("%d-%m-%Y")}
    elif data_type == "plan":
        params = {"day": target_datetime.strftime("%d-%m-%Y")}
    else:
        raise ParserException("TH.py", f"unexpected data_type: {data_type}", "TZ")

    # This API returns a list of 2-elements list
    # Example: [[0, 12345], [60, 12345.6], ...]
    # - The first integer is the seconds number since 00:00 am (i.e. 900 == 00:15 am)
    # - The second integer is the total generation (MW)
    raw_text = requests.post(url, data=params).text

    # Fix programming error of the returned value.
    # This API server returns a invalid string if the list is empty.
    # e.g. {"id":"","name":"","day":"","timeStart":0,list:[],"count":0}
    raw_text = raw_text.replace(",list:", ',"list":')

    raw_data = json.loads(raw_text)["list"]

    data = []
    for item in raw_data:
        # The data structure of `item` is inconsistent.
        # If there is temperature data is available, `item` is 3-tuple.
        # Otherwise, it returns 2-tuple. So we cannot simply iterate `raw_data`.
        seconds_in_day = item[0]
        generation = item[1]

        datetime = _seconds_to_time(target_datetime, seconds_in_day)
        data.append(
            {
                "datetime": datetime,
                "generation": generation,
            }
        )

    return data


def _seconds_to_time(target_datetime: dt.datetime, seconds_in_day: int) -> dt.datetime:
    """Convert a given seconds integer to a datetime value."""
    today = target_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
    datetime = today + dt.timedelta(seconds=seconds_in_day)
    return datetime


def fetch_price(
    zone_key: str = "TH",
    session: Optional[requests.Session] = None,
    target_datetime: Optional[dt.datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """Fetch the price data from the MEA."""
    if target_datetime is not None:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    # Fetch price from MEA table.
    with requests.get(MEA_PRICE_URL) as response:
        soup = BeautifulSoup(response.content, "lxml")

    # 'Over 400 kWh (up from 401st)' from Table 1.1
    unit_price_table = soup.find_all("table")[1]
    price = unit_price_table.find_all("td")[19]

    return {
        "zoneKey": zone_key,
        "currency": "THB",
        "datetime": arrow.now(TZ).datetime,
        "price": float(price.text) * 1000,
        "source": MEA_URL,
    }


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""
    print("fetch_production() ->")
    print(fetch_production())

    print("fetch_consumption() ->")
    print(fetch_consumption())

    print("fetch_generation_forecast() ->")
    print(fetch_generation_forecast())

    print("fetch_price() ->")
    print(fetch_price())
