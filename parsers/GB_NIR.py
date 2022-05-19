#!/usr/bin/env python3

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from io import StringIO
from operator import itemgetter

import pandas as pd
import requests
from bs4 import BeautifulSoup
from dateutil import parser, tz

from parsers.lib.config import refetch_frequency

from .lib.validation import validate

production_url = "http://ws.soni.ltd.uk/DownloadCentre/aspx/FuelMix.aspx"
exchange_url = "http://ws.soni.ltd.uk/DownloadCentre/aspx/SystemOutput.aspx"
# Positive values in the .csv represent imports to Northern Ireland from GB / IR.
# Negative values in the .csv represent exports from Northern Ireland to GB / IR.

## exchange_url = 'http://ws.soni.ltd.uk/DownloadCentre/aspx/MoyleTie.aspx' ## see comment below
## Old exchange_url was used for exchanges, but it provided incomplete data.
## "Total_Moyle_Load_MW" was showing "0" when exporting to GB. Tie-line data was missing for the two 110kV Lines "Enniskillen(NIR)-Corraclassy(IR)" and "Strabane(NIR)-Letterkenny(IR)"
## Exchanges are now based on data with better quality provided in "SystemOutput.csv" under the new exchange_url = 'http://ws.soni.ltd.uk/DownloadCentre/aspx/SystemOutput.aspx'


def get_data(url, target_datetime, session=None):
    """
    Requests data from a specified url in CSV format.
    Returns a response.text object.
    """

    s = session or requests.Session()

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:55.0) Gecko/20100101 Firefox/55.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    pagereq = requests.get(url, headers=headers)
    soup = BeautifulSoup(pagereq.text, "html.parser")

    # Find and define parameters needed to send a POST request for the actual data.
    viewstategenerator = soup.find("input", attrs={"id": "__VIEWSTATEGENERATOR"})[
        "value"
    ]
    viewstate = soup.find("input", attrs={"id": "__VIEWSTATE"})["value"]
    eventvalidation = soup.find("input", attrs={"id": "__EVENTVALIDATION"})["value"]

    # Set date for post request.
    if target_datetime:
        target_date = target_datetime.date()
    else:
        # get the latest data
        target_date = datetime.now().date()

    month = target_date.month
    day = target_date.day
    year = target_date.year

    FromDatePicker_clientState = (
        '|0|01%s-%s-%s-0-0-0-0||[[[[]],[],[]],[{%s},[]],"01%s-%s-%s-0-0-0-0"]'
        % (year, month, day, "", year, month, day)
    )
    ToDatePicker_clientState = (
        '|0|01%s-%s-%s-0-0-0-0||[[[[]],[],[]],[{%s},[]],"01%s-%s-%s-0-0-0-0"]'
        % (year, month, day, "", year, month, day)
    )
    btnDownloadCSV = "Download+CSV"
    ig_def_dp_cal_clientState = (
        '|0|15,2017,09,2017,%s,%s||[[null,[],null],[{%s},[]],"11,2017,09,2017,%s,%s"]'
        % (month, day, "", month, day)
    )
    IG_CSS_LINKS_ = "ig_res/default/ig_monthcalendar.css|ig_res/default/ig_texteditor.css|ig_res/default/ig_shared.css"

    postdata = {
        "__VIEWSTATE": viewstate,
        "__VIEWSTATEGENERATOR": viewstategenerator,
        "__EVENTVALIDATION": eventvalidation,
        "FromDatePicker_clientState": FromDatePicker_clientState,
        "ToDatePicker_clientState": ToDatePicker_clientState,
        "btnDownloadCSV": btnDownloadCSV,
        "_ig_def_dp_cal_clientState": ig_def_dp_cal_clientState,
        "_IG_CSS_LINKS_": IG_CSS_LINKS_,
    }

    postheaders = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:55.0) Gecko/20100101 Firefox/55.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    datareq = s.post(url, headers=postheaders, data=postdata)

    return datareq.text


def add_default_tz(timestamp):
    """Adds Northern Ireland timezone to datetime object if tz = None."""

    NIR = tz.gettz("Europe/Belfast")
    modified_timestamp = timestamp.replace(tzinfo=timestamp.tzinfo or NIR)

    return modified_timestamp


def create_production_df(text_data):
    """
    Turns thermal csv data into a usable dataframe.
    """

    cols_to_use = [0, 1, 2, 3, 4, 5]
    df_production = pd.read_csv(StringIO(text_data), usecols=cols_to_use)
    df_production.fillna(0.0, inplace=True)

    return df_production


def create_exchange_df(text_data):
    """
    Turns exchange csv data into a usable dataframe.
    """

    df_exchange = pd.read_csv(StringIO(text_data))
    df_exchange.fillna(0.0, inplace=True)

    return df_exchange


def production_processor(df) -> list:
    """Creates quarter hour datapoints for thermal production."""

    datapoints = []
    for index, row in df.iterrows():
        snapshot = {}
        snapshot["datetime"] = add_default_tz(
            parser.parse(row["TimeStamp"], dayfirst=True)
        )
        snapshot["gas"] = row["Gas_MW"]
        snapshot["coal"] = row["Coal_MW"]
        snapshot["oil"] = row["Distillate_MW"] + row["Diesel_MW"]
        snapshot["wind"] = row["Wind_MW"]
        if snapshot["wind"] > -20:
            snapshot["wind"] = max(snapshot["wind"], 0)
        datapoints.append(snapshot)

    return datapoints


def moyle_processor(df) -> list:
    """Creates quarter hour datapoints for GB exchange."""

    datapoints = []
    for index, row in df.iterrows():
        snapshot = {}
        snapshot["datetime"] = add_default_tz(
            parser.parse(row["TimeStamp"], dayfirst=True)
        )
        snapshot["netFlow"] = row["Total_Moyle_Load_MW"]
        snapshot["source"] = "soni.ltd.uk"
        snapshot["sortedZoneKeys"] = "GB->GB-NIR"
        datapoints.append(snapshot)

    return datapoints


def IE_processor(df) -> list:
    """Creates quarter hour datapoints for IE exchange."""

    datapoints = []
    for index, row in df.iterrows():
        snapshot = {}
        snapshot["datetime"] = add_default_tz(
            parser.parse(row["TimeStamp"], dayfirst=True)
        )
        netFlow = -1 * row["Tie_Lines_MW"]
        snapshot["netFlow"] = netFlow
        snapshot["source"] = "soni.ltd.uk"
        snapshot["sortedZoneKeys"] = "GB-NIR->IE"
        datapoints.append(snapshot)

    return datapoints


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key="GB-NIR",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
) -> dict:
    """Requests the last known production mix (in MW) of a given country."""

    production_data = get_data(production_url, target_datetime)
    production_df = create_production_df(production_data)
    production = production_processor(production_df)

    production_mix_by_quarter_hour = []

    for datapoint in production:
        production_mix = {
            "zoneKey": zone_key,
            "datetime": datapoint.get("datetime", 0.0),
            "production": {
                "coal": datapoint.get("coal", 0.0),
                "gas": datapoint.get("gas", 0.0),
                "oil": datapoint.get("oil", 0.0),
                "solar": None,
                "wind": datapoint.get("wind", 0.0),
            },
            "source": "soni.ltd.uk",
        }
        production_mix_by_quarter_hour.append(
            validate(production_mix, logger=logger, required=["gas", "coal"], floor=1.0)
        )

    return production_mix_by_quarter_hour


def fetch_exchange(
    zone_key1, zone_key2, session=None, target_datetime=None, logger=None
) -> dict:
    """Requests the last known power exchange (in MW) between two countries."""

    exchange_data = get_data(exchange_url, target_datetime)
    exchange_dataframe = create_exchange_df(exchange_data)
    if "->".join(sorted([zone_key1, zone_key2])) == "GB->GB-NIR":
        moyle = moyle_processor(exchange_dataframe)
        return moyle
    elif "->".join(sorted([zone_key1, zone_key2])) == "GB-NIR->IE":
        IE = IE_processor(exchange_dataframe)
        return IE
    else:
        raise NotImplementedError("This exchange pair is not implemented")


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""
    print("fetch_production() ->")
    print(fetch_production())
    print("fetch_exchange(GB-NIR, GB) ->")
    print(fetch_exchange("GB-NIR", "GB"))
    print("fetch_exchange(GB-NIR, IE) ->")
    print(fetch_exchange("GB-NIR", "IE"))
