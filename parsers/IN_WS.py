#!/usr/bin/env python3


from datetime import datetime
from logging import Logger, getLogger
from typing import Dict, Optional

import pandas as pd
from requests import Session

from electricitymap.contrib.config.constants import PRODUCTION_MODES

from .lib.exceptions import ParserException

NPP_SOURCE = "https://npp.gov.in/public-reports/cea/daily/dgr/{day}-{month}-{year}/dgr2-{year}-{month}-{day}.xls"
CEA_SOURCE = "https://cea.nic.in/wp-content/uploads/daily_reports/{dt.day}_{dt:%b}_{dt.year}_Daily_Report..xlsx"


def _format_production_data(df: pd.DataFrame) -> Dict:
    dict_prod = {}
    for i in range(len(df)):
        row = df.iloc[i]
        dict_prod[row.production_mode] = row.production
    return dict_prod


def fetch_npp_data(
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
):
    """get production for conventional thermal, nuclear and hydro from NPP daily reports"""
    r = session or Session()
    _format_date = lambda x: "{:02d}".format(x)
    filtered_out_rows = [
        "REGION TOTAL",
        "CHHATISGARH",
        "STATE TOTAL",
        "             SECTOR:",
        "             TYPE:",
        "Unit",
    ]
    production_mode_mapping = {
        "THERMAL": "coal",
        "THER (GT)": "gas",
        "NUCLEAR": "nuclear",
        "HYDRO": "hydro",
    }
    if target_datetime:
        url = NPP_SOURCE.format(
            day=_format_date(target_datetime.day),
            month=_format_date(target_datetime.month),
            year=target_datetime.year,
        )
        r = r.get(url)
        df = pd.read_excel(r.url, header=3)
        df = df.rename(
            columns={
                "Unnamed: 0": "zone",
                "TODAY'S\nACTUAL\n": "production",
                "Unnamed: 2": "production_mode",
            }
        )
        df = df[
            df.index[df["zone"] == "WESTERN"].values[0]
            + 1 : df.index[df["zone"] == "SOUTHERN"].values[0]
        ]
        df.production_mode = df["production_mode"].ffill()
        df = df.loc[~df.zone.isin(filtered_out_rows)]
        df["production_mode"] = df["production_mode"].map(production_mode_mapping)
        df = df.groupby(["production_mode"])["production"].sum().reset_index()
        production = _format_production_data(df)
        return production
    else:
        raise ValueError(f"no data available for {target_datetime}")


def fetch_cea_data(
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
):
    """get production for renewables from CEA daily reports"""

    column_mapping = {
        "Unnamed: 1": "zone",
        "पवन ऊर्जा/Wind Energy": "wind",
        "सौर ऊर्जा/Solar Energy": "solar",
        "अन्य ऊर्जा/Others RES (Biomass,Bagasse,Small Hydro & Others)": "unknown",
    }
    r = session or Session()
    if target_datetime:
        url = CEA_SOURCE.format(dt=target_datetime)
        r_ren = r.get(url)
        df_ren = pd.read_excel(r_ren.url, header=5)
        df_ren = df_ren.rename(columns=column_mapping)
        df_ren = df_ren.dropna(subset=["zone"])
        df_ren = df_ren[["zone", "wind", "solar", "unknown"]]
        df_ren = df_ren.loc[df_ren["zone"].str.contains("Western Region")]
        df_ren = df_ren.melt(
            id_vars=["zone"], var_name="production_mode", value_name="production"
        )
        production = _format_production_data(df_ren[["production_mode", "production"]])
        return production
    else:
        raise ParserException(
            parser="IN_WS.py",
            message=f"data is not available for {target_datetime}",
        )


def _fetch_all_production(
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
):
    """get production from all sources"""
    production = {
        **fetch_npp_data(
            session=session, target_datetime=target_datetime, logger=logger
        ),
        **fetch_cea_data(
            session=session, target_datetime=target_datetime, logger=logger
        ),
    }
    for mode in PRODUCTION_MODES:
        if mode not in production:
            production[mode] = None
    return production


def fetch_production(
    zone_key="IN-WS",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
):

    production = {
        "zoneKey": zone_key,
        "datetime": target_datetime,
        "production": _fetch_all_production(session=session, target_datetime=target_datetime, logger=logger),
        "storage": {},
        "source": "cea.nic.in, npp.gov.in",
    }
    return production
