#!usr/bin/env python3

"""Parser for all of India"""


from datetime import datetime
from logging import Logger, getLogger
from typing import Optional

import arrow
import requests
from bs4 import BeautifulSoup
from requests import Session

import pandas as pd

from electricitymap.contrib.config.constants import PRODUCTION_MODES
from parsers.lib.exceptions import ParserException

NPP_SOURCE = "https://npp.gov.in/public-reports/cea/daily/dgr/{day}-{month}-{year}/dgr2-{year}-{month}-{day}.xls"
CEA_SOURCE = "https://cea.nic.in/wp-content/uploads/daily_reports/{dt.day}_{dt:%b}_{dt.year}_Daily_Report..xlsx"
NPP_XLS_ZONES = {"IN_N":["NORTHERN","WESTERN"],
                "IN_W":["WESTERN","SOUTHERN"],
                "IN_S":["SOUTHERN","EASTERN"],
                "IN_E":["EASTERN", "NORTH EASTERN"],
                "IN_NE":["NORTH EASTERN","BHUTAN IMP."]}
CEA_XLS_ZONES = {"IN_N":"Northern Region",
                "IN_W":"Western Region",
                "IN_S":"Southern Region",
                "IN_E":"Eastern Region",
                "IN_NE":"North-Eastern Region"}

GENERATION_MAPPING = {
    "THERMAL GENERATION": "coal",
    "GAS GENERATION": "gas",
    "HYDRO GENERATION": "hydro",
    "NUCLEAR GENERATION": "nuclear",
    "RENEWABLE GENERATION": "unknown",
}

GENERATION_URL = "http://meritindia.in/Dashboard/BindAllIndiaMap"


def get_data(session: Optional[Session]):
    """
    Requests html then extracts generation data.
    Returns a dictionary.
    """

    s = session or requests.Session()
    req = s.get(GENERATION_URL)
    soup = BeautifulSoup(req.text, "lxml")
    tables = soup.findAll("table")

    gen_info = tables[-1]
    rows = gen_info.findAll("td")

    generation = {}
    for row in rows:
        gen_title = row.find("div", {"class": "gen_title_sec"})
        gen_val = row.find("div", {"class": "gen_value_sec"})
        val = gen_val.find("span", {"class": "counter"})
        generation[gen_title.text] = val.text.strip()

    return generation


def fetch_production(
    zone_key: str = "IN",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """Requests the last known production mix (in MW) of a given zone."""

    if target_datetime is not None:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    raw_data = get_data(session)
    processed_data = {k: float(v.replace(",", "")) for k, v in raw_data.items()}
    processed_data.pop("DEMANDMET", None)

    for k in processed_data:
        if k not in GENERATION_MAPPING.keys():
            processed_data.pop(k)
            logger.warning(
                "Key '{}' in IN is not mapped to type.".format(k), extra={"key": "IN"}
            )

    mapped_production = {GENERATION_MAPPING[k]: v for k, v in processed_data.items()}

    data = {
        "zoneKey": zone_key,
        "datetime": arrow.now("Asia/Kolkata").datetime,
        "production": mapped_production,
        "storage": {},
        "source": "meritindia.in",
    }

    return data


def _format_production_data(df: pd.DataFrame) -> Dict:
    dict_prod = {}
    for i in range(len(df)):
        row = df.iloc[i]
        dict_prod[row.production_mode] = row.production * 1000 / 24 # convert to MW (in the xls it's in MU which are GWh)
    return dict_prod


def fetch_npp_data(zone_key: str,
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
        resp = r.get(url)
        df = pd.read_excel(resp.url, header=3)
        df = df.rename(
            columns={
                "Unnamed: 0": "zone",
                "TODAY'S\nACTUAL\n": "production",
                "Unnamed: 2": "production_mode",
            }
        )
        df = df[
            df.index[df["zone"] == NPP_XLS_ZONES[zone_key][0]].values[0]
            + 1 : df.index[df["zone"] == NPP_XLS_ZONES[zone_key][1]].values[0]
        ]
        df.production_mode = df["production_mode"].ffill()
        df = df.loc[~df.zone.isin(filtered_out_rows)]
        df["production_mode"] = df["production_mode"].map(production_mode_mapping)
        df = df.groupby(["production_mode"])["production"].sum().reset_index()
        production = _format_production_data(df)
        return production
    else:
        raise ValueError(f"no data available for {target_datetime}")


def fetch_cea_data(zone_key: str,
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
        df_ren = df_ren.loc[df_ren["zone"].str.contains(CEA_XLS_ZONES[zone_key])]
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


def _fetch_cea_npp_production(zone_key: str,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
):
    """get production from all sources"""
    production = {
        **fetch_npp_data(zone_key=zone_key,
            session=session, target_datetime=target_datetime, logger=logger
        ),
        **fetch_cea_data(zone_key=zone_key,
            session=session, target_datetime=target_datetime, logger=logger
        ),
    }
    for mode in PRODUCTION_MODES:
        if mode not in production:
            production[mode] = None
    return production


def fetch_daily_production(
    zone_key: str,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
):

    production = {
        "zoneKey": zone_key,
        "datetime": target_datetime,
        "production": _fetch_cea_npp_production(zone_key=zone_key, session=session, target_datetime=target_datetime, logger=logger),
        "storage": {},
        "source": "cea.nic.in, npp.gov.in",
    }
    return production


if __name__ == "__main__":
    print("fetch_production() -> ")
    print(fetch_production())
