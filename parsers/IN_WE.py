#!/usr/bin/env python3


import json
from datetime import datetime
from logging import Logger, getLogger
from typing import Optional

import arrow
import pandas as pd
import pytz
from requests import Session

from parsers.lib.exceptions import ParserException

IN_W_PROXY = "https://in-proxy-jfnx5klx2a-el.a.run.app"
HOME_URL = f"{IN_W_PROXY}/content/165_1_GeneratorScheduleVsActual.aspx?host=https://www.wrldc.in"
PRODUCTION_URL = f"{IN_W_PROXY}/GeneratorSchedule_data.aspx/Get_GeneratorScheduleData_state_Wise?host=https://www.wrldc.in"
EXCHANGE_URL = f"{IN_W_PROXY}/InterRegionalLinks_Data.aspx/Get_InterRegionalLinks_Region_Wise?host=https://www.wrldc.in"

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
    "WR-SR": "IN_SO->IN_WE",
    "WR-ER": "IN_EA->IN_WE",
    "WR-NR": "IN_NO->IN_WE",
}

KINDS_DICT = {
    "production":"https://www.wrldc.in/GeneratorSchedule_data.aspx/Get_GeneratorScheduleData_state_Wise",
    "exchanges": "https://www.wrldc.in/InterRegionalLinks_Data.aspx/Get_InterRegionalLinks_Region_Wise"
}

KINDS_URL = {"production": PRODUCTION_URL, "exchanges": EXCHANGE_URL}


def fetch_data(
    zone_key: str = "IN_WE",
    kind: str = None,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """- get production data from wrldc.in
    - filter data for target_datetime
    - format data"""
    r = session or Session()

    dt_12_hour = arrow.get(target_datetime.strftime("%Y-%m-%d %I:%M")).datetime
    payload = {"date": target_datetime.strftime("%Y-%m-%d")}

    # resp = r.post(KINDS_URL[kind], json=payload)

    resp = r.post(url= KINDS_DICT[kind], json=payload)
    if resp.json():
        data = json.loads(resp.json()["d"])
        for item in data:
            item["lastUpdate"] = datetime.strptime(
                item["lastUpdate"], "%Y-%d-%m %H:%M:%S"
            )
            dt = arrow.get(item["lastUpdate"])
            if dt.second >= 30:
                item["lastUpdate"] = dt.shift(minutes=1).floor("minute").datetime
            else:
                item["lastUpdate"] = dt.floor("minute").datetime
        df_data = pd.DataFrame(
            [item for item in data if item["lastUpdate"] == dt_12_hour]
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
    df_production = pd.DataFrame()
    if len(data) == len(POWER_PLANT_MAPPING):
        df_production = data.copy()
    else:
        for plant in POWER_PLANT_MAPPING:
            df_plant = data.loc[data.State_Name == plant].copy()
            if target_datetime.hour >= 12:
                df_production = pd.concat(
                    [df_production, df_plant.loc[df_plant["Id"] == max(df_plant["Id"])]]
                )
            else:
                df_production = pd.concat(
                    [df_production, df_plant.loc[df_plant["Id"] == min(df_plant["Id"])]]
                )

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
        df_production.groupby(["lastUpdate", "production_mode"])["Actual"]
        .mean()
        .reset_index()
    )
    production = {}
    for mode in set(df_production.production_mode):
        production[mode] = df_production.loc[
            df_production["production_mode"] == mode, "Actual"
        ].values[0]
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
    data["zone_key"] = data["Region_Name"].map(EXCHANGES_MAPPING)
    df_exchanges = data.loc[data["zone_key"] == sortedZoneKeys]
    exchanges = {}
    if len(df_exchanges) > 1:
        if target_datetime.hour >= 12:
            exchanges["netFLow"] = - df_exchanges.loc[max(df_exchanges.index)][
                "Current_Loading"
            ] # sorted keys are inverted
        else:
            exchanges["netFLow"] = - df_exchanges.loc[min(df_exchanges.index)][
                "Current_Loading"
            ]
    else:
        exchanges["netFLow"] = - df_exchanges.iloc[0]["Current_Loading"]
    exchanges["sortedZoneKeys"] = sortedZoneKeys
    exchanges["datetime"] = target_datetime.replace(
        tzinfo=pytz.timezone("Asia/Kolkata")
    )
    exchanges["source"] = "wrldc.in"
    return exchanges


def fetch_production(
    zone_key: str = "IN_W",
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
        kind="exchanges",
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )
    exchanges = format_exchanges_data(
        data=data, sortedZoneKeys=sortedZoneKeys, target_datetime=target_datetime
    )
    return exchanges
