#!/usr/bin/env python3

"""Parse the Alberta Electric System Operator's (AESO's) Energy Trading System
(ETS) website.
"""

# Standard library imports
import csv
import logging
import re
import urllib.parse

# Third-party library imports
import arrow
import requests

# Local library imports
from parsers.lib import validation

DEFAULT_ZONE_KEY = "CA-AB"
MINIMUM_PRODUCTION_THRESHOLD = 10  # MW
TIMEZONE = "Canada/Mountain"
URL = urllib.parse.urlsplit("http://ets.aeso.ca/ets_web/ip/Market/Reports")
URL_STRING = urllib.parse.urlunsplit(URL)


def fetch_exchange(
    zone_key1=DEFAULT_ZONE_KEY,
    zone_key2="CA-BC",
    session=None,
    target_datetime=None,
    logger=None,
) -> dict:
    """Request the last known power exchange (in MW) between two countries."""
    if target_datetime:
        raise NotImplementedError("Currently unable to scrape historical data")
    session = session or requests.Session()
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
    sorted_zone_keys = "->".join(sorted((zone_key1, zone_key2)))
    if sorted_zone_keys not in flows:
        raise NotImplementedError(f"Pair '{sorted_zone_keys}' not implemented")
    return {
        "datetime": get_csd_report_timestamp(response.text),
        "sortedZoneKeys": sorted_zone_keys,
        "netFlow": float(flows[sorted_zone_keys]),
        "source": URL.netloc,
    }


def fetch_price(
    zone_key=DEFAULT_ZONE_KEY, session=None, target_datetime=None, logger=None
) -> list:
    """Request the last known power price of a given country."""
    if target_datetime:
        raise NotImplementedError("Currently unable to scrape historical data")
    session = session or requests.Session()
    response = session.get(
        f"{URL_STRING}/SMPriceReportServlet", params={"contentType": "csv"}
    )
    return [
        {
            "currency": "CAD",
            "datetime": arrow.get(row[0], "MM/DD/YYYY HH", tzinfo=TIMEZONE).datetime,
            "price": float(row[1]),
            "source": URL.netloc,
            "zoneKey": zone_key,
        }
        for row in csv.reader(response.text.split("\r\n\r\n")[2].splitlines()[1:])
        if row[1] != "-"
    ]


def fetch_production(
    zone_key=DEFAULT_ZONE_KEY,
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
) -> dict:
    """Request the last known production mix (in MW) of a given country."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")
    session = session or requests.Session()
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
    return arrow.get(
        re.search(r'"Last Update : (.*)"', report).group(1),
        "MMM DD, YYYY HH:mm",
        tzinfo=TIMEZONE,
    ).datetime


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
