#!/usr/bin/env python3
# coding=utf-8
"""
This parser returns Kuwait's electricity system load (assumed to be equal to electricity production)
Source: Ministry of Electricity and Water / State of Kuwait
URL: https://www.mew.gov.kw/en/
Scroll down to see the system load gauge
Shares of Electricity production in 2017: 65.6% oil, 34.4% gas (source: IEA; https://www.iea.org/statistics/?country=KUWAIT&indicator=ElecGenByFuel)
"""

import re

import arrow
import requests


def fetch_production(zone_key="KW", session=None, target_datetime=None, logger=None):
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    # Kuwait very rarely imports power, so we assume that production is equal to consumption
    # "Kuwait imports power in an emergency and only for a few hours at a time"
    # See https://github.com/tmrowco/electricitymap-contrib/pull/2457#pullrequestreview-408781556
    consumption_dict = fetch_consumption(
        zone_key=zone_key, session=session, logger=logger
    )
    consumption = consumption_dict["consumption"]

    datapoint = {
        "zoneKey": zone_key,
        "datetime": arrow.now("Asia/Kuwait").datetime,
        "production": {"unknown": consumption},
        "source": "mew.gov.kw",
    }

    return datapoint


def fetch_consumption(zone_key="KW", session=None, target_datetime=None, logger=None):
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    r = session or requests.session()
    url = "https://www.mew.gov.kw/en"
    response = r.get(url)
    load = re.findall(r"\((\d{4,5})\)", response.text)
    load = int(load[0])
    consumption = load

    datapoint = {
        "zoneKey": zone_key,
        "datetime": arrow.now("Asia/Kuwait").datetime,
        "consumption": consumption,
        "source": "mew.gov.kw",
    }

    return datapoint


if __name__ == "__main__":
    """Main method, never used by the electricityMap backend, but handy for testing."""

    print("fetch_consumption() ->")
    print(fetch_consumption())
    print("fetch_production() ->")
    print(fetch_production())
