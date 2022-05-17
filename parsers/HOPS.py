#!/usr/bin/env python3

"""Parser for power production in Croatia"""

import logging
from datetime import datetime

import arrow
import pandas as pd
import requests

URL = "https://www.hops.hr/Home/PowerExchange"


def fetch_solar_production(
    feed_date, session=None, logger=logging.getLogger(__name__)
) -> float:
    """
    Calls extra resource at https://files.hrote.hr/files/EKO_BG/FORECAST/SOLAR/FTP/TEST_DRIVE/<dd.m.yyyy>.json
    to get Solar power production in MW.
    :param feed_date: date_time string from the original HOPS feed
    """
    r = session or requests.session()

    dt = datetime.strptime(feed_date, "%Y-%m-%d %H:%M:%S")
    # Get all available files
    dates_url = (
        "https://files.hrote.hr/files/EKO_BG/FORECAST/SOLAR/FTP/TEST_DRIVE/dates.json"
    )
    response = r.get(dates_url)
    dates = response.json()
    # Use latest file to get more up to date estimation
    solar_url = (
        "https://files.hrote.hr/files/EKO_BG/FORECAST/SOLAR/FTP/TEST_DRIVE/{0}".format(
            dates[-1]["Filename"]
        )
    )
    response = r.get(solar_url)
    obj = response.json()

    df = pd.DataFrame.from_dict(obj["FullPower"]).set_index("Timestamp")
    df.index = pd.to_datetime(df.index)  # cast strings to datetimes
    solar_production_dt = pd.Timestamp(feed_date, tz="Europe/Zagreb").floor("1h")
    try:
        solar = df["Value"].loc[solar_production_dt]
        # Converting to MW
        solar *= 0.001
    except KeyError:
        logger.warning(
            "No value for Solar power production on {0}".format(solar_production_dt)
        )
        solar = None

    return solar


def fetch_production(
    zone_key="HR",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
):
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    r = session or requests.session()
    response = r.get(URL)
    obj = response.json()

    # We assume the timezone of the time returned is local time and convert to UTC
    date_time = arrow.get(obj["updateTime"]).replace(tzinfo="Europe/Belgrade").to("utc")

    # The json returned contains a list of values
    # 0 - 9 are individual exchanges with neighbouring countries
    # 10 - 13 are cumulative exchanges with neigbouring countries
    # 14 grid frequency
    # 15 total load of Croatia
    # 16 'Ukupna proizvodnja'  total generation
    # 17 'Proizvodnja VE'      wind generation
    df = pd.DataFrame.from_dict(obj["resources"]).set_index("sourceName")

    # Get the wind power generation
    # In some cases value may be negative. It looks like an issue at data source side.
    wind = abs(df["value"].loc["Proizvodnja VE"])

    solar = fetch_solar_production(obj["updateTime"], session)

    # Get the total power generation and substract wind and solar power
    unknown = df["value"].loc["Ukupna proizvodnja"] - wind
    if solar:
        unknown -= solar

    return [
        {
            "zoneKey": "HR",
            "datetime": date_time.datetime,
            "production": {"wind": wind, "solar": solar, "unknown": unknown},
            "source": "hops.hr",
        }
    ]


if __name__ == "__main__":
    print("fetch_production(HR)->")
    print(fetch_production("HR"))
