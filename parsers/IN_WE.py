#!/usr/bin/env python3


import json
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Any

import arrow
import pandas as pd
from requests import Response, Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

"""
This module is used to read the exchange values on a hourly basis for a day from India West to North, East, South. 
This module also calculates the total electricity consumption by India West.
The data is fetched from https://www.wrldc.in using APIs which provide data in JSON format
India West constitutes of Gujrat, Madhya Pradesh, Chattishgarh, Maharashtra, Goa, DD, DNH

These APIs return the data in 24 hour format from midnight 12:00am to current time at which the parser is run  
"""


IN_WE_PROXY = "https://in-proxy-jfnx5klx2a-el.a.run.app"
IN_TZ = "Asia/Kolkata"

""" 
Exchange data parser
source: https://www.wrldc.in/content/166_1_FlowsonInterRegionalLinks.aspx
API : https://www.wrldc.in/InterRegionalLinks_Data.aspx/Get_InterRegionalLinks_Data
"""
EXCHANGE_URL = f"{IN_WE_PROXY}/InterRegionalLinks_Data.aspx/Get_InterRegionalLinks_Data?host=https://www.wrldc.in"

"""
Consumption data parser
source: https://www.wrldc.in/content/164_1_StateScheduleVsActual.aspx
API: https://www.wrldc.in/OnlinestateTest1.aspx/GetRealTimeData
"""
CONSUMPTION_URL = (
    f"{IN_WE_PROXY}/OnlinestateTest1.aspx/GetRealTimeData?host=https://www.wrldc.in"
)

EXCHANGES_MAPPING = {
    "IN-SO->IN-WE": "WR-SR",
    "IN-EA->IN-WE": "WR-ER",
    "IN-NO->IN-WE": "WR-NR",
}


def fetch_data(url: str, session: Session, target_datetime: datetime) -> dict:
    """
    get data from wrldc.in
    """
    assert target_datetime is not None

    r = session or Session()
    payload = {"date": target_datetime.strftime("%Y-%m-%d"), "Flag": 24}

    resp: Response = r.post(url=url, json=payload)

    try:
        data = json.loads(resp.json().get("d", {}))
    except json.decoder.JSONDecodeError:
        raise ParserException(
            parser="IN_WE.py",
            message=f"{target_datetime}: {url} data is not available",
        )
    return data


def process_exchanges_data(
    data: dict, zone_key1: str, zone_key2: str, logger: Logger
) -> ExchangeList:
    """
    Processes exchanges data:
    - filter out the records that correspond to the zone_key
    - convert the datetime field to contain only date and hour(remove minute and secods)
    - set timezone to IST for datetime field
    - average all data points grouping by target_datetime hour
    - generate the Exchange list from the Current_Loading column
    """

    assert len(data) > 0

    datetime_column = "lastUpdate"
    value_column = "Current_Loading"
    zone_key = "->".join(sorted([zone_key1, zone_key2]))

    df = pd.DataFrame(data, columns=["Region_Name", datetime_column, value_column])
    df = df[df["Region_Name"] == EXCHANGES_MAPPING[zone_key]]
    df[datetime_column] = (
        pd.to_datetime(df[datetime_column], format="%Y-%m-%d %H:%M:%S")
        .dt.tz_localize(IN_TZ)
        .dt.floor("h")
    )
    df = df.groupby(["Region_Name", datetime_column]).mean().round(3)
    df[value_column] = -df[value_column]

    df = df.reset_index()
    exchange_list = ExchangeList(logger)
    for _, row in df.iterrows():
        exchange_list.append(
            zoneKey=ZoneKey(zone_key),
            datetime=row[datetime_column].to_pydatetime(),
            netFlow=row[value_column],
            source="wrldc.in",
        )
    return exchange_list


def process_consumption_data(
    data: dict, zone_key: ZoneKey, logger: Logger
) -> TotalConsumptionList:
    """
    Processes consumption data:
    - convert the datetime field to contain only date and hour(remove minute and secods)
    - set timezone to IST for datetime field
    - average all data points grouping by target_datetime hour and state
    - sum the datapoints from each state grouping by target_datetime hour
    - generate the Total Consumption list from the Demand column
    """

    assert len(data) > 0

    datetime_column = "current_datetime"
    value_column = "Demand"

    df = pd.DataFrame(data, columns=["StateName", datetime_column, value_column])
    df[datetime_column] = (
        pd.to_datetime(df[datetime_column], format="%Y-%m-%d %H:%M:%S")
        .dt.tz_localize(IN_TZ)
        .dt.floor("h")
    )
    df = (
        df.groupby([datetime_column, "StateName"])
        .mean()
        .groupby([datetime_column])
        .sum()
        .round(3)
    )

    df = df.reset_index()
    consumptionList = TotalConsumptionList(logger)
    for _, row in df.iterrows():
        consumptionList.append(
            zoneKey=zone_key,
            datetime=row[datetime_column].to_pydatetime(),
            consumption=row[value_column],
            source="wrldc.in",
        )
    return consumptionList


@refetch_frequency(timedelta(days=1))
def fetch_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """This method is called by IN-EA, IN-SO, IN-NO zone's parsers to get the exchange data with IN-WA zone."""

    if target_datetime is None:
        target_datetime = arrow.utcnow().datetime

    data = fetch_data(
        url=EXCHANGE_URL, session=session, target_datetime=target_datetime
    )
    exchange_list = process_exchanges_data(
        zone_key1=zone_key1, zone_key2=zone_key2, data=data, logger=logger
    )

    return exchange_list.to_list()


@refetch_frequency(timedelta(days=1))
def fetch_consumption(
    zone_key: ZoneKey = ZoneKey("IN-WE"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """This method is used to fetch the consumption data for IN-WA zone."""

    if target_datetime is None:
        target_datetime = arrow.utcnow().datetime
    data = fetch_data(
        url=CONSUMPTION_URL, session=session, target_datetime=target_datetime
    )
    consumption_list = process_consumption_data(data, zone_key, logger)
    return consumption_list.to_list()


if __name__ == "__main__":
    print(fetch_exchange(zone_key1="IN-WE", zone_key2="IN-NO"))
    print(fetch_consumption())
