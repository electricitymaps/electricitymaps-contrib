#!/usr/bin/env python3


import json
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

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

IN_WE_PROXY = "https://in-proxy-jfnx5klx2a-el.a.run.app"
EXCHANGE_URL = f"{IN_WE_PROXY}/InterRegionalLinks_Data.aspx/Get_InterRegionalLinks_Data?host=https://www.wrldc.in"
CONSUMPTION_URL = (
    f"{IN_WE_PROXY}/OnlinestateTest1.aspx/GetRealTimeData?host=https://www.wrldc.in"
)

EXCHANGES_MAPPING = {
    "WR-SR": "IN-SO->IN-WE",
    "WR-ER": "IN-EA->IN-WE",
    "WR-NR": "IN-NO->IN-WE",
}

KIND_MAPPING = {
    "exchange": {"url": EXCHANGE_URL, "datetime_column": "lastUpdate"},
    "consumption": {"url": CONSUMPTION_URL, "datetime_column": "current_datetime"},
}

TZ = ZoneInfo("Asia/Kolkata")


def is_expected_downtime() -> bool:
    current_day = datetime.now().weekday()
    expected_outage_days = [5, 6, 0]  # Saturday, Sunday and Monday

    if current_day in expected_outage_days:
        return True

    return False


def get_date_range(dt: datetime):
    return pd.date_range(
        arrow.get(dt).floor("day").datetime,
        arrow.get(dt).floor("hour").datetime,
        freq="H",
    ).to_pydatetime()


def fetch_data(
    kind: str | None = None,
    session: Session | None = None,
    target_datetime: datetime | None = None,
) -> dict:
    """- get production data from wrldc.in
    - filter all rows with same hour as target_datetime"""
    assert target_datetime is not None
    assert kind is not None

    r = session or Session()
    payload = {
        "date": target_datetime.astimezone(tz=TZ).strftime("%Y-%m-%d"),
        "Flag": 24,
    }

    resp: Response = r.post(url=KIND_MAPPING[kind]["url"], json=payload)

    try:
        data = json.loads(resp.json().get("d", {}))
    except Exception as e:
        if is_expected_downtime():
            raise ValueError(
                "IN_WE Parser cannot get latest data during the expected downtime (Saturday to Monday)."
            ) from e
        else:
            raise ParserException(
                parser="IN_WE.py",
                message=f"{target_datetime}: {kind} data is not available",
            ) from e

    datetime_col = KIND_MAPPING[kind]["datetime_column"]
    for item in data:
        item[datetime_col] = datetime.strptime(item[datetime_col], "%Y-%m-%d %H:%M:%S")
    return data


def filter_raw_data(
    kind: str,
    data: dict,
    target_datetime: datetime,
) -> pd.DataFrame:
    """
    Filters out correct datetimes (source data is 24 hour format)
    """
    assert len(data) > 0
    assert kind != ""

    dt_24_hour = arrow.get(target_datetime.strftime("%Y-%m-%d %H:%M")).datetime
    datetime_col = KIND_MAPPING[kind]["datetime_column"]
    filtered_data = pd.DataFrame(
        [item for item in data if item[datetime_col].hour == dt_24_hour.hour]
    )
    return filtered_data


def format_exchanges_data(
    data: dict, zone_key1: str, zone_key2: str, target_datetime: datetime
) -> float | None:
    """format exchanges data:
    - filters out correct datetimes (source data is 12 hour format)
    - average all data points in the target_datetime hour"""
    assert target_datetime is not None
    assert len(data) > 0

    sortedZoneKeys = "->".join(sorted([zone_key1, zone_key2]))
    filtered_data = filter_raw_data(
        kind="exchange", data=data, target_datetime=target_datetime
    )
    if filtered_data.empty:
        return None

    filtered_data["zone_key"] = filtered_data["Region_Name"].map(EXCHANGES_MAPPING)
    df_exchanges = filtered_data.loc[filtered_data["zone_key"] == sortedZoneKeys]

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
    net_flow = -round(df_exchanges.iloc[0].get("Current_Loading", 0), 3)

    return net_flow


def format_consumption_data(
    data: dict, zone_key: str, target_datetime: datetime
) -> float | None:
    """format consumption data:
    - filters out correct datetimes (source data is 12 hour format)
    - average all data points in the target_datetime hour"""
    assert target_datetime is not None
    assert len(data) > 0

    filtered_data = filter_raw_data(
        kind="consumption",
        data=data,
        target_datetime=target_datetime,
    )
    if filtered_data.empty:
        return None

    df_consumption = filtered_data

    df_consumption["target_datetime"] = target_datetime
    df_consumption = (
        df_consumption.groupby(["StateName", "target_datetime"])
        .mean(numeric_only=True)
        .reset_index()
    )

    consumption_value = round(
        df_consumption.groupby(["target_datetime"])["Demand"].sum().values[0], 3
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
    if target_datetime is None:
        target_datetime = datetime.now(TZ)

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
        if net_flow is not None:
            exchange_list.append(
                zoneKey=ZoneKey(sortedZoneKeys),
                datetime=arrow.get(dt).replace(tzinfo=TZ).datetime,
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
    if target_datetime is None:
        target_datetime = datetime.now(TZ)
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
        if consumption_data_point is not None:
            consumption_list.append(
                zoneKey=zone_key,
                datetime=arrow.get(dt).replace(tzinfo=TZ).datetime,
                consumption=consumption_data_point,
                source="wrldc.in",
            )
    return consumption_list.to_list()


if __name__ == "__main__":
    print(fetch_exchange(zone_key1="IN-WE", zone_key2="IN-NO"))
    print(fetch_consumption())
