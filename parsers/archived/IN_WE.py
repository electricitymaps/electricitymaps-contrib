#!/usr/bin/env python3


import json
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Optional

import arrow
import pandas as pd
from requests import Response, Session

from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

IN_WE_PROXY = "https://in-proxy-jfnx5klx2a-el.a.run.app"
EXCHANGE_URL = f"{IN_WE_PROXY}/InterRegionalLinks_Data.aspx/Get_InterRegionalLinks_Region_Wise?host=https://www.wrldc.in"
CONSUMPTION_URL = f"{IN_WE_PROXY}/OnlinestateTest1.aspx/GetRealTimeData_state_Wise?host=https://www.wrldc.in"

EXCHANGES_MAPPING = {
    "WR-SR": "IN-SO->IN-WE",
    "WR-ER": "IN-EA->IN-WE",
    "WR-NR": "IN-NO->IN-WE",
}

KIND_MAPPING = {
    "exchange": {"url": EXCHANGE_URL, "datetime_column": "lastUpdate"},
    "consumption": {"url": CONSUMPTION_URL, "datetime_column": "current_datetime"},
}


def get_date_range(dt: datetime):
    return pd.date_range(
        arrow.get(dt).floor("day").datetime,
        arrow.get(dt).ceil("day").floor("hour").datetime,
        freq="H",
    ).to_pydatetime()


def fetch_data(
    zone_key: str = "IN-WE",
    kind: Optional[str] = None,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """- get production data from wrldc.in
    - filter all rows with same hour as target_datetime"""
    assert target_datetime is not None
    assert kind is not None

    r = session or Session()
    payload = {"date": target_datetime.strftime("%Y-%m-%d")}

    resp: Response = r.post(url=KIND_MAPPING[kind]["url"], json=payload)

    try:
        data = json.loads(resp.json().get("d", {}))
    except json.decoder.JSONDecodeError:
        raise ParserException(
            parser="IN_WE.py",
            message=f"{target_datetime}: {kind} data is not available",
        )

    datetime_col = KIND_MAPPING[kind]["datetime_column"]
    for item in data:
        item[datetime_col] = datetime.strptime(item[datetime_col], "%Y-%d-%m %H:%M:%S")
        dt = arrow.get(item[datetime_col])
        if dt.second >= 30:
            item[datetime_col] = dt.shift(minutes=1).floor("minute").datetime
        else:
            item[datetime_col] = dt.floor("minute").datetime
    return data


def format_raw_data(
    kind: str,
    data: dict,
    target_datetime: datetime,
) -> pd.DataFrame:
    assert len(data) > 0
    assert kind != ""

    dt_12_hour = arrow.get(target_datetime.strftime("%Y-%m-%d %I:%M")).datetime
    datetime_col = KIND_MAPPING[kind]["datetime_column"]
    filtered_data = pd.DataFrame(
        [item for item in data if item[datetime_col].hour == dt_12_hour.hour]
    )
    return filtered_data


def format_exchanges_data(
    data: dict, zone_key1: str, zone_key2: str, target_datetime: datetime
) -> dict:
    """format exchanges data:
    - filters out correct datetimes (source data is 12 hour format)
    - average all data points in the target_datetime hour"""
    assert target_datetime is not None
    assert len(data) > 0

    sortedZoneKeys = "->".join(sorted([zone_key1, zone_key2]))
    filtered_data = format_raw_data(
        kind="exchange", data=data, target_datetime=target_datetime
    )

    filtered_data["zone_key"] = filtered_data["Region_Name"].map(EXCHANGES_MAPPING)
    df_exchanges = filtered_data.loc[filtered_data["zone_key"] == sortedZoneKeys]
    exchanges = {}
    if target_datetime.hour >= 12:
        df_exchanges = df_exchanges.drop_duplicates(
            subset=["Region_Name", "lastUpdate"], keep="last"
        )
    else:
        df_exchanges = filtered_data.drop_duplicates(
            subset=["Region_Name", "lastUpdate"], keep="first"
        )
    df_exchanges.loc[:, "target_datetime"] = target_datetime
    df_exchanges = (
        df_exchanges.groupby(["Region_Name", "target_datetime"])
        .mean(numeric_only=True)
        .reset_index()
    )

    exchanges = {
        "netFlow": -round(df_exchanges.iloc[0]["Current_Loading"], 3),
        "sortedZoneKeys": sortedZoneKeys,
        "datetime": arrow.get(target_datetime).replace(tzinfo="Asia/Kolkata").datetime,
        "source": "wrldc.in",
    }
    return exchanges


def format_consumption_data(
    data: dict, zone_key: str, target_datetime: datetime
) -> dict:
    """format consumption data:
    - filters out correct datetimes (source data is 12 hour format)
    - average all data points in the target_datetime hour"""
    assert target_datetime is not None
    assert len(data) > 0

    filtered_data = format_raw_data(
        kind="consumption",
        data=data,
        target_datetime=target_datetime,
    )

    consumption = {
        "zoneKey": zone_key,
        "datetime": arrow.get(target_datetime).replace(tzinfo="Asia/Kolkata").datetime,
        "source": "wrldc.in",
    }

    if target_datetime.hour >= 12:
        df_consumption = filtered_data.drop_duplicates(
            subset=["StateName", "current_datetime"], keep="last"
        )
    else:
        df_consumption = filtered_data.drop_duplicates(
            subset=["StateName", "current_datetime"], keep="first"
        )
    df_consumption.loc[:, "target_datetime"] = target_datetime
    df_consumption = (
        df_consumption.groupby(["StateName", "target_datetime"])
        .mean(numeric_only=True)
        .reset_index()
    )

    consumption["consumption"] = round(
        df_consumption.groupby(["target_datetime"])["Act_Drawal"].sum().values[0], 3
    )
    return consumption


@refetch_frequency(timedelta(days=1))
def fetch_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    if target_datetime is None:
        target_datetime = arrow.utcnow().datetime
    data = fetch_data(
        zone_key=zone_key1,
        kind="exchange",
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )
    exchanges = [
        format_exchanges_data(
            zone_key1=zone_key1,
            zone_key2=zone_key2,
            data=data,
            target_datetime=dt,
        )
        for dt in get_date_range(target_datetime)
    ]
    return exchanges


@refetch_frequency(timedelta(days=1))
def fetch_consumption(
    zone_key: str = "IN-WE",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    if target_datetime is None:
        target_datetime = arrow.utcnow().datetime
    data = fetch_data(
        zone_key=zone_key,
        kind="consumption",
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )

    consumption = [
        format_consumption_data(
            zone_key=zone_key,
            data=data,
            target_datetime=dt,
        )
        for dt in get_date_range(target_datetime)
    ]

    return consumption


if __name__ == "__main__":
    print(fetch_consumption())
