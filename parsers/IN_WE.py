#!/usr/bin/env python3


import json
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
from requests import Response, Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

IN_WE_PROXY = "https://in-proxy-jfnx5klx2a-el.a.run.app"
EXCHANGE_URL = f"{IN_WE_PROXY}/InterRegionalLinks_Data.aspx/Get_InterRegionalLinks_Region_Wise?host=https://www.wrldc.in"
CONSUMPTION_URL = f"{IN_WE_PROXY}/OnlinestateTest1.aspx/GetRealTimeData_state_Wise?host=https://www.wrldc.in"
ZONE_INFO = ZoneInfo("Asia/Kolkata")

EXCHANGES_MAPPING = {
    "WR-SR": "IN-SO->IN-WE",
    "WR-ER": "IN-EA->IN-WE",
    "WR-NR": "IN-NO->IN-WE",
}

KIND_MAPPING = {
    "exchange": {
        "url": EXCHANGE_URL,
        "datetime_col": "lastUpdate",
        "region_col": "Region_Name",
    },
    "consumption": {
        "url": CONSUMPTION_URL,
        "datetime_col": "current_datetime",
        "region_col": "StateName",
    },
}


def is_expected_downtime() -> bool:
    """
    Details about this expected downtime is currently being clarified via
    https://github.com/electricitymaps/electricitymaps-contrib/pull/6184#issuecomment-2564302911.
    """
    expected_outage_days = [5, 6, 0]  # Saturday, Sunday and Monday
    if datetime.now(ZONE_INFO).weekday() in expected_outage_days:
        return True
    return False


def get_date_range(dt: datetime):
    """Returns 24 datetime objects for a given datetime's date, one for each hour."""
    now_date_as_dt = datetime.combine(
        datetime.now(ZONE_INFO).date(), datetime.min.time()
    ).replace(tzinfo=ZONE_INFO)
    return pd.date_range(
        now_date_as_dt,
        now_date_as_dt + timedelta(hours=23),
        freq="H",
    ).to_pydatetime()


def fetch_data(
    kind: str,
    session: Session,
    target_datetime: datetime,
) -> dict:
    """
    Fetches 24 hours of either exchange or production data from wrldc.in.
    """
    url = KIND_MAPPING[kind]["url"]
    datetime_col = KIND_MAPPING[kind]["datetime_col"]

    payload = {"date": target_datetime.strftime("%Y-%m-%d")}
    resp: Response = session.post(url, json=payload)

    try:
        data = json.loads(resp.json().get("d", {}))
    except Exception as e:
        if is_expected_downtime(target_datetime):
            raise ValueError(
                "IN_WE Parser cannot get latest data during the expected downtime (Saturday to Monday)."
            ) from e
        else:
            raise ParserException(
                parser="IN_WE.py",
                message=f"{target_datetime}: {kind} data is not available",
            ) from e

    for item in data:
        # replace datetime string with datetime object
        dt = datetime.strptime(item[datetime_col], "%Y-%d-%m %H:%M:%S").replace(
            tzinfo=ZONE_INFO
        )
        item[datetime_col] = dt

        # round the seconds to 0 as a non-robust strategy to later distinguish
        # AM from PM
        if dt.second >= 30:
            item[datetime_col] = dt + timedelta(seconds=60 - dt.second)
        else:
            item[datetime_col] = dt - timedelta(seconds=dt.second)
    return data


def filter_raw_data(
    kind: str,
    data: dict,
    target_datetime: datetime,
) -> pd.DataFrame:
    """
    From 24 hours of data, filter out a specific hour of interest.

    The source data is a 12 hour format without mentioning if its AM/PM, so
    11:15 could mean 11:15 or 23:15.
    """
    datetime_col = KIND_MAPPING[kind]["datetime_col"]
    region_col = KIND_MAPPING[kind]["region_col"]

    # 00:mm is never reported, only 12:mm, so we need to filter based on an hour
    # value from one to twelve instead of zero to eleven
    one_to_twelve = (target_datetime.hour % 12) or 12
    two_hours_df = pd.DataFrame(
        [item for item in data if item[datetime_col].hour == one_to_twelve]
    )

    # We rely on the data being ordered, and drop first/last duplicates
    # depending on the hour of interest.
    one_hour_df = two_hours_df.drop_duplicates(
        subset=[region_col, datetime_col],
        keep="first" if target_datetime.hour < 12 else "last",
    )
    return one_hour_df


def format_exchanges_data(
    data: dict,
    zone_key1: str,
    zone_key2: str,
    target_datetime: datetime,
) -> float:
    """format exchanges data:
    - average all data points in the target_datetime hour"""
    region_col = KIND_MAPPING["exchange"]["region_col"]

    sortedZoneKeys = "->".join(sorted([zone_key1, zone_key2]))
    filtered_data = filter_raw_data(
        kind="exchange",
        data=data,
        target_datetime=target_datetime,
    )

    filtered_data["zone_key"] = filtered_data[region_col].map(EXCHANGES_MAPPING)
    df_exchanges = filtered_data.loc[filtered_data["zone_key"] == sortedZoneKeys]

    df_exchanges.loc[:, "target_datetime"] = target_datetime
    df_exchanges = (
        df_exchanges.groupby([region_col, "target_datetime"])
        .mean(numeric_only=True)
        .reset_index()
    )
    net_flow = -round(df_exchanges.iloc[0].get("Current_Loading", 0), 3)

    return net_flow


def format_consumption_data(
    data: dict,
    zone_key: str,
    target_datetime: datetime,
) -> float:
    """format consumption data:
    - average all data points in the target_datetime hour"""
    region_col = KIND_MAPPING["consumption"]["region_col"]

    filtered_data = filter_raw_data(
        kind="consumption",
        data=data,
        target_datetime=target_datetime,
    )
    filtered_data.loc[:, "target_datetime"] = target_datetime
    filtered_data = (
        filtered_data.groupby([region_col, "target_datetime"])
        .mean(numeric_only=True)
        .reset_index()
    )

    consumption_value = round(
        filtered_data.groupby(["target_datetime"])["Demand"].sum().values[0], 3
    )
    return consumption_value


@refetch_frequency(timedelta(days=1))
def fetch_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    if session is None:
        session = Session()
    if target_datetime is None:
        target_datetime = datetime.now(ZONE_INFO)
    else:
        target_datetime = target_datetime.astimezone(ZONE_INFO)

    sortedZoneKeys = "->".join(sorted([zone_key1, zone_key2]))
    data = fetch_data(
        kind="exchange",
        session=session,
        target_datetime=target_datetime,
    )
    exchange_list = ExchangeList(logger)
    for dt in get_date_range(target_datetime):
        net_flow = format_exchanges_data(
            zone_key1=zone_key1,
            zone_key2=zone_key2,
            data=data,
            target_datetime=dt,
        )
        exchange_list.append(
            zoneKey=ZoneKey(sortedZoneKeys),
            datetime=dt,
            netFlow=net_flow,
            source="wrldc.in",
        )

    return exchange_list.to_list()


@refetch_frequency(timedelta(days=1))
def fetch_consumption(
    zone_key: ZoneKey = ZoneKey("IN-WE"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    if session is None:
        session = Session()
    if target_datetime is None:
        target_datetime = datetime.now(ZONE_INFO)
    else:
        target_datetime = target_datetime.astimezone(ZONE_INFO)

    data = fetch_data(
        kind="consumption",
        session=session,
        target_datetime=target_datetime,
    )

    consumption_list = TotalConsumptionList(logger)
    for dt in get_date_range(target_datetime):
        consumption_data_point = format_consumption_data(
            zone_key=zone_key, data=data, target_datetime=dt
        )
        consumption_list.append(
            zoneKey=zone_key,
            datetime=dt,
            consumption=consumption_data_point,
            source="wrldc.in",
        )
    return consumption_list.to_list()


if __name__ == "__main__":
    print(fetch_exchange(zone_key1="IN-WE", zone_key2="IN-NO"))
    print(fetch_consumption())
