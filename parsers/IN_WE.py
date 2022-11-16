#!/usr/bin/env python3


import json
from datetime import datetime
from logging import Logger, getLogger
from typing import Optional

import arrow
import pandas as pd
import pytz
from requests import Response, Session

from parsers.lib.exceptions import ParserException

IN_WE_PROXY = "https://in-proxy-jfnx5klx2a-el.a.run.app"
PRODUCTION_URL = f"{IN_WE_PROXY}/GeneratorSchedule_data.aspx/Get_GeneratorScheduleData_state_Wise?host=https://www.wrldc.in"
EXCHANGE_URL = f"{IN_WE_PROXY}/InterRegionalLinks_Data.aspx/Get_InterRegionalLinks_Region_Wise?host=https://www.wrldc.in"
CONSUMPTION_URL = f"{IN_WE_PROXY}/OnlinestateTest1.aspx/GetRealTimeData_state_Wise?host=https://www.wrldc.in"

POWER_PLANT_MAPPING = {
    "Korba I": "coal",
    "Korba III": "coal",
    "VSTPS-I": "coal",
    "VSTPS-II": "coal",
    "VSTPS-III": "coal",
    "VSTPS-IV": "coal",
    "VSTPS-V": "coal",
    "Kawas": "gas",
    "Gandhar": "gas",
    "Kakrapar": "nuclear",
    "Tarapur": "nuclear",
    "SSP": "hydro",
    "Sipat I": "coal",
    "Sipat II": "coal",
    "RGPPL": "gas",
    "NSPCL": "coal",
    "Mauda I": "coal",
    "Mauda II": "coal",
    "Sasan": "coal",
    "CGPL": "coal",
    "Solapur": "coal",
    "Gadarwara": "coal",
    "Lara": "coal",
    "Khargone": "coal",
}

EXCHANGES_MAPPING = {
    "WR-SR": "IN-SO->IN-WE",
    "WR-ER": "IN-EA->IN-WE",
    "WR-NR": "IN-NO->IN-WE",
}

KIND_MAPPING = {
    "production": {"url": PRODUCTION_URL, "datetime_column": "lastUpdate"},
    "exchange": {"url": EXCHANGE_URL, "datetime_column": "lastUpdate"},
    "consumption": {"url": CONSUMPTION_URL, "datetime_column": "current_datetime"},
}


def fetch_data(
    zone_key: str = "IN-WE",
    kind: Optional[str] = None,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> pd.DataFrame:
    """- get production data from wrldc.in
    - filter all rows with same hour as target_datetime"""
    assert target_datetime is not None

    r = session or Session()

    dt_12_hour = arrow.get(target_datetime.strftime("%Y-%m-%d %I:%M")).datetime
    payload = {"date": target_datetime.strftime("%Y-%m-%d")}

    resp: Response = r.post(url=KIND_MAPPING[kind]["url"], json=payload)

    datetime_col = KIND_MAPPING[kind]["datetime_column"]
    if resp.json():
        data = json.loads(resp.json()["d"])
        for item in data:
            item[datetime_col] = datetime.strptime(
                item[datetime_col], "%Y-%d-%m %H:%M:%S"
            )
            dt = arrow.get(item[datetime_col])
            if dt.second >= 30:
                item[datetime_col] = dt.shift(minutes=1).floor("minute").datetime
            else:
                item[datetime_col] = dt.floor("minute").datetime
        df_data = pd.DataFrame(
            [item for item in data if item[datetime_col].hour == dt_12_hour.hour]
        )
        return df_data
    else:
        raise ParserException(
            parser="IN_WE.py",
            message=f"{target_datetime}: {kind} data is not available",
        )


def format_production_data(
    data: pd.DataFrame, zone_key: str, target_datetime: Optional[datetime]
) -> dict:
    """format production data:
    - filters out correct datetimes (source data is 12 hour format)
    - average all data points in the target_datetime hour
    - map power plants
    - sum production per mode"""
    df_production = pd.DataFrame()
    df_unique_dt = (
        pd.DataFrame()
    )  # for older datetimes datetimes are not the same in the AM and the PM which makes sorting harder
    if len(data) == len(POWER_PLANT_MAPPING):
        df_production = data.copy()
    else:
        for plant in set(data.State_Name):
            df_plant = data.loc[data.State_Name == plant].copy()
            for dt in set(df_plant.lastUpdate):
                df_dt = df_plant.loc[df_plant.lastUpdate == dt]
                if len(df_dt) > 1:
                    if target_datetime.hour >= 12:
                        df_production = pd.concat(
                            [df_production, df_dt.loc[df_dt["Id"] == max(df_dt["Id"])]]
                        )
                    else:
                        df_production = pd.concat(
                            [df_production, df_dt.loc[df_dt["Id"] == min(df_dt["Id"])]]
                        )
                else:
                    df_unique_dt = pd.concat([df_unique_dt, df_dt])

            if not df_unique_dt.empty:
                if target_datetime.hour >= 12:
                    df_production = pd.concat(
                        [
                            df_production,
                            df_unique_dt.loc[
                                df_unique_dt.Id > df_plant["Id"].mean(numeric_only=True)
                            ],
                        ]
                    )
                else:
                    df_production = pd.concat(
                        [
                            df_production,
                            df_unique_dt.loc[
                                df_unique_dt.Id
                                <= df_plant["Id"].mean(numeric_only=True)
                            ],
                        ]
                    )

    df_production.loc[:, "target_datetime"] = target_datetime
    df_production = (
        df_production.groupby(["target_datetime", "State_Name"])["Actual"]
        .mean(numeric_only=True)
        .reset_index()
    )  # get one hourly data point

    df_production.loc[:, "production_mode"] = df_production["State_Name"].map(
        POWER_PLANT_MAPPING
    )
    df_production["Actual"] = df_production.apply(
        lambda x: 0
        if (x["Actual"] < 0 and x["production_mode"] != "hydro")
        else x["Actual"],
        axis=1,
    )
    df_production = (
        df_production.groupby(["target_datetime", "production_mode"])["Actual"]
        .sum()
        .reset_index()
    )  # aggregate by production mode
    production = {}
    for mode in set(df_production.production_mode):
        production[mode] = round(
            df_production.loc[
                df_production["production_mode"] == mode, "Actual"
            ].values[0],
            3,
        )
    production_data_point = {
        "zoneKey": zone_key,
        "datetime": target_datetime.replace(tzinfo=pytz.timezone("Asia/Kolkata")),
        "production": production,
        "source": "wrldc.in",
    }
    return production_data_point


def format_exchanges_data(
    data: pd.DataFrame, sortedZoneKeys: str, target_datetime: Optional[datetime]
) -> dict:
    """format exchanges data:
    - filters out correct datetimes (source data is 12 hour format)
    - average all data points in the target_datetime hour"""
    data["zone_key"] = data["Region_Name"].map(EXCHANGES_MAPPING)
    df_exchanges = data.loc[data["zone_key"] == sortedZoneKeys]
    exchanges = {}
    if target_datetime.hour >= 12:
        df_exchanges = df_exchanges.drop_duplicates(
            subset=["Region_Name", "lastUpdate"], keep="last"
        )
    else:
        df_exchanges = data.drop_duplicates(
            subset=["Region_Name", "lastUpdate"], keep="first"
        )
    df_exchanges.loc[:, "target_datetime"] = target_datetime
    df_exchanges = (
        df_exchanges.groupby(["Region_Name", "target_datetime"])
        .mean(numeric_only=True)
        .reset_index()
    )

    exchanges = {
        "netFLow": -round(df_exchanges.iloc[0]["Current_Loading"], 3),
        "sortedZoneKeys": sortedZoneKeys,
        "datetime": target_datetime.replace(tzinfo=pytz.timezone("Asia/Kolkata")),
        "source": "wrldc.in",
    }
    return exchanges


def format_consumption_data(
    data: pd.DataFrame, zone_key: str, target_datetime: Optional[datetime]
) -> dict:
    """format consumption data:
    - filters out correct datetimes (source data is 12 hour format)
    - average all data points in the target_datetime hour"""
    consumption = {
        "zoneKey": zone_key,
        "datetime": target_datetime.replace(tzinfo=pytz.timezone("Asia/Kolkata")),
        "source": "wrldc.in",
    }

    if target_datetime.hour >= 12:
        df_consumption = data.drop_duplicates(
            subset=["StateName", "current_datetime"], keep="last"
        )
    else:
        df_consumption = data.drop_duplicates(
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


def fetch_production(
    zone_key: str = "IN-WE",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    if target_datetime is None:
        target_datetime = arrow.utcnow().datetime
    data = fetch_data(
        zone_key=zone_key,
        kind="production",
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )
    production = format_production_data(
        data=data, zone_key=zone_key, target_datetime=target_datetime
    )
    return production


def fetch_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    sortedZoneKeys = "->".join(sorted([zone_key1, zone_key2]))
    if target_datetime is None:
        target_datetime = arrow.utcnow().datetime
    data = fetch_data(
        zone_key=zone_key1,
        kind="exchange",
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )
    exchanges = format_exchanges_data(
        data=data, sortedZoneKeys=sortedZoneKeys, target_datetime=target_datetime
    )
    return exchanges


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
    consumption = format_consumption_data(
        data=data, zone_key=zone_key, target_datetime=target_datetime
    )
    return consumption
