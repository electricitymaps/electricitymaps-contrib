#!/usr/bin/env python3

"""Parse the Alberta Electric System Operator's (AESO's) Energy Trading System
(ETS) website.
"""

# Standard library imports
import csv
import re
import urllib.parse
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

# Third-party library imports
from requests import Session

from electricitymap.contrib.lib.models.event_lists import ExchangeList, PriceList
from electricitymap.contrib.lib.types import ZoneKey

# Local library imports
from parsers.lib import validation

DEFAULT_ZONE_KEY = ZoneKey("CA-AB")
MINIMUM_PRODUCTION_THRESHOLD = 10  # MW
TIMEZONE = ZoneInfo("Canada/Mountain")
URL = urllib.parse.urlsplit("http://ets.aeso.ca/ets_web/ip/Market/Reports")
URL_STRING = urllib.parse.urlunsplit(URL)


def fetch_exchange(
    zone_key1: str = DEFAULT_ZONE_KEY,
    zone_key2: str = "CA-BC",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Request the last known power exchange (in MW) between two countries."""
    if target_datetime:
        raise NotImplementedError("Currently unable to scrape historical data")
    session = session or Session()
    response = session.get(
        f"{URL_STRING}/CSDReportServlet", params={"contentType": "csv"}
    )
    interchange = dict(csv.reader(response.text.split("\r\n\r\n")[4].splitlines()))
    flows = {
        f"{DEFAULT_ZONE_KEY}->CA-BC": interchange["British Columbia"],
        f"{DEFAULT_ZONE_KEY}->CA-SK": interchange["Saskatchewan"],
        f"{DEFAULT_ZONE_KEY}->US-MT": interchange["Montana"],
        f"{DEFAULT_ZONE_KEY}->US-NW-NWMT": interchange["Montana"],
    }
    sorted_zone_keys = ZoneKey("->".join(sorted((zone_key1, zone_key2))))
    if sorted_zone_keys not in flows:
        raise NotImplementedError(f"Pair '{sorted_zone_keys}' not implemented")
    exchanges = ExchangeList(logger)
    exchanges.append(
        zoneKey=sorted_zone_keys,
        datetime=get_csd_report_timestamp(response.text),
        netFlow=float(flows[sorted_zone_keys]),
        source=URL.netloc,
    )
    return exchanges.to_list()


def fetch_price(
    zone_key: ZoneKey = DEFAULT_ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Request the last known power price of a given country."""
    if target_datetime:
        raise NotImplementedError("Currently unable to scrape historical data")
    session = session or Session()
    response = session.get(
        f"{URL_STRING}/SMPriceReportServlet", params={"contentType": "csv"}
    )
    prices = PriceList(logger)
    for row in csv.reader(response.text.split("\r\n\r\n")[2].splitlines()[1:]):
        if row[1] != "-":
            date, hour = row[0].split()
            prices.append(
                zoneKey=zone_key,
                datetime=datetime.strptime(
                    f"{date} {int(hour) - 1}", "%m/%d/%Y %H"
                ).replace(tzinfo=TIMEZONE)
                + timedelta(hours=1),
                price=float(row[1]),
                source=URL.netloc,
                currency="CAD",
            )
    return prices.to_list()


def fetch_production(
    zone_key: str = DEFAULT_ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> dict[str, Any] | None:
    """Request the last known production mix (in MW) of a given country."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")
    session = session or Session()
    response = session.get(
        f"{URL_STRING}/CSDReportServlet", params={"contentType": "csv"}
    )
    generation = {
        row[0]: {
            "MC": float(row[1]),  # maximum capability
            "TNG": float(row[2]),  # total net generation
        }
        for row in csv.reader(response.text.split("\r\n\r\n")[3].splitlines())
    }
    return validation.validate(
        {
            "capacity": {
                "gas": generation["GAS"]["MC"],
                "hydro": generation["HYDRO"]["MC"],
                "battery storage": generation["ENERGY STORAGE"]["MC"],
                "solar": generation["SOLAR"]["MC"],
                "wind": generation["WIND"]["MC"],
                "biomass": generation["OTHER"]["MC"],
                "unknown": generation["DUAL FUEL"]["MC"],
                "coal": generation["COAL"]["MC"],
            },
            "datetime": get_csd_report_timestamp(response.text),
            "production": {
                "gas": generation["GAS"]["TNG"],
                "hydro": generation["HYDRO"]["TNG"],
                "solar": generation["SOLAR"]["TNG"],
                "wind": generation["WIND"]["TNG"],
                "biomass": generation["OTHER"]["TNG"],
                "unknown": generation["DUAL FUEL"]["TNG"],
                "coal": generation["COAL"]["TNG"],
            },
            "source": URL.netloc,
            "storage": {
                "battery": generation["ENERGY STORAGE"]["TNG"],
            },
            "zoneKey": zone_key,
        },
        logger,
        floor=MINIMUM_PRODUCTION_THRESHOLD,
        remove_negative=True,
    )


def get_csd_report_timestamp(report):
    """Get the timestamp from a current supply/demand (CSD) report."""
    return datetime.strptime(
        re.search(r'"Last Update : (.*)"', report).group(1), "%b %d, %Y %H:%M"
    ).replace(tzinfo=TIMEZONE)


if __name__ == "__main__":
    # Never used by the electricityMap backend, but handy for testing.
    print("fetch_production() ->")
    print(fetch_production())
    print("fetch_price() ->")
    print(fetch_price())
    print(f"fetch_exchange({DEFAULT_ZONE_KEY}, CA-BC) ->")
    print(fetch_exchange(DEFAULT_ZONE_KEY, "CA-BC"))
    print(f"fetch_exchange({DEFAULT_ZONE_KEY}, CA-SK) ->")
    print(fetch_exchange(DEFAULT_ZONE_KEY, "CA-SK"))
    print(f"fetch_exchange({DEFAULT_ZONE_KEY}, US-MT) ->")
    print(fetch_exchange(DEFAULT_ZONE_KEY, "US-MT"))
    print(f"fetch_exchange({DEFAULT_ZONE_KEY}, US-NW-NWMT) ->")
    print(fetch_exchange(DEFAULT_ZONE_KEY, "US-NW-NWMT"))
