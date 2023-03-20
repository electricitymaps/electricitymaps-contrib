#!usr/bin/env python3

"""Parser for all of India"""


from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Any, Dict, List, Optional

import arrow
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from pytz import UTC
from requests import Response, Session

from parsers.lib.exceptions import ParserException
from parsers.lib.validation import validate_consumption

IN_TZ = "Asia/Kolkata"
START_DATE_RENEWABLE_DATA = arrow.get("2020-12-17", tzinfo=IN_TZ).datetime
CONVERSION_GWH_MW = 0.024
GENERATION_MAPPING = {
    "THERMAL GENERATION": "coal",
    "GAS GENERATION": "gas",
    "HYDRO GENERATION": "hydro",
    "NUCLEAR GENERATION": "nuclear",
    "RENEWABLE GENERATION": "unknown",
}

GENERATION_URL = "http://meritindia.in/Dashboard/BindAllIndiaMap"

NPP_MODE_MAPPING = {
    "THER (GT)": "gas",
    "THERMAL": "coal",
    "HYDRO": "hydro",
    "THER (DG)": "oil",
    "NUCLEAR": "nuclear",
}
NPP_REGION_MAPPING = {
    "NORTHERN": "IN-NO",
    "EASTERN": "IN-EA",
    "WESTERN": "IN-WE",
    "SOUTERN": "IN-SO",
    "NORTH EASTERN": "IN-NE",
}

CEA_REGION_MAPPING = {
    "उत्तरी क्षेत्र / Northern Region": "IN-NO",
    "पश्चिमी क्षेत्र / Western Region": "IN-WE",
    "दक्षिणी क्षेत्र / Southern Region": "IN-SO",
    "पूर्वी क्षेत्र/ Eastern Region": "IN-EA",
    "उत्तर-पूर्वी क्षेत्र  / North-Eastern Region": "IN-NE",
}

DEMAND_URL = "https://vidyutpravah.in/state-data/{state}"
STATES_MAPPING = {
    "IN-NO": [
        "delhi",
        "haryana",
        "himachal-pradesh",
        "jammu-kashmir",
        "punjab",
        "rajasthan",
        "uttar-pradesh",
        "uttarakhand",
    ],
    "IN-WE": ["gujarat", "madya-pradesh", "maharashtra", "goa", "chhattisgarh"],
    "IN-EA": ["bihar", "west-bengal", "odisha", "sikkim"],
    "IN-NE": [
        "arunachal-pradesh",
        "assam",
        "meghalaya",
        "tripura",
        "mizoram",
        "nagaland",
        "manipur",
    ],
    "IN-SO": [
        "karnataka",
        "kerala",
        "tamil-nadu",
        "andhra-pradesh",
        "telangana",
        "puducherry",
    ],
}

DEMAND_URL = "https://vidyutpravah.in/state-data/{state}"
STATES_MAPPING = {
    "IN-NO": [
        "delhi",
        "haryana",
        "himachal-pradesh",
        "jammu-kashmir",
        "punjab",
        "rajasthan",
        "uttar-pradesh",
        "uttarakhand",
    ],
    "IN-WE": ["gujarat", "madya-pradesh", "maharashtra", "goa", "chhattisgarh"],
    "IN-EA": ["bihar", "west-bengal", "odisha", "sikkim"],
    "IN-NE": [
        "arunachal-pradesh",
        "assam",
        "meghalaya",
        "tripura",
        "mizoram",
        "nagaland",
        "manipur",
    ],
    "IN-SO": [
        "karnataka",
        "kerala",
        "tamil-nadu",
        "andhra-pradesh",
        "telangana",
        "puducherry",
    ],
}


def get_data(session: Optional[Session]) -> Dict[str, Any]:
    """
    Requests html then extracts generation data.
    Returns a dictionary.
    """

    s = session or Session()
    req: Response = s.get(GENERATION_URL)

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


def fetch_live_production(
    zone_key: str = "IN",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> Dict[str, Any]:
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
        "datetime": IN_TZ.localize(datetime.now()),
        "production": mapped_production,
        "storage": {},
        "source": "meritindia.in",
    }

    return data


def fetch_consumption(
    zone_key: str,
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> Dict[str, Any]:
    """Fetches live consumption from government dashboard. Consumption is available per state and is then aggregated at regional level.
    Data is not available for the following states: Ladakh (disputed territory), Daman & Diu, Dadra & Nagar Haveli, Lakshadweep"""
    if target_datetime is not None:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    total_consumption = 0
    for state in STATES_MAPPING[zone_key]:
        r: Response = session.get(DEMAND_URL.format(state=state))
        soup = BeautifulSoup(r.content, "html.parser")
        try:
            state_consumption = int(
                soup.find(
                    "span", attrs={"class": "value_DemandMET_en value_StateDetails_en"}
                )
                .text.strip()
                .split()[0]
                .replace(",", "")
            )
        except:
            raise ParserException(
                parser="IN.py",
                message=f"{target_datetime}: consumption data is not available for {zone_key}",
            )
        total_consumption += state_consumption

    data = {
        "zoneKey": zone_key,
        "datetime": arrow.now(tz=IN_TZ).datetime,
        "consumption": total_consumption,
        "source": "vidyupravah.in",
    }
    data = validate_consumption(data, logger)
    if data is None:
        raise ParserException(
            parser="IN.py",
            message=f"{target_datetime}: No valid consumption data found for {zone_key}",
        )
    return data


def fetch_npp_production(
    zone_key: str,
    target_datetime: datetime,
    session: Session = Session(),
    logger: Logger = getLogger(__name__),
) -> Dict[str, Any]:
    """Gets production for conventional thermal, nuclear and hydro from NPP daily reports
    This data most likely doesn't inlcude distributed generation"""
    npp_url = "https://npp.gov.in/public-reports/cea/daily/dgr/{date:%d-%m-%Y}/dgr2-{date:%Y-%m-%d}.xls".format(
        date=target_datetime
    )
    r: Response = session.get(npp_url)
    if r.status_code == 200:
        df_npp = pd.read_excel(r.content, header=3)
        df_npp = df_npp.rename(
            columns={
                df_npp.columns[0]: "power_station",
                df_npp.columns[2]: "production_mode",
                "TODAY'S\nACTUAL\n": "value",
            }
        )
        df_npp = df_npp[["power_station", "production_mode", "value"]]
        df_npp = df_npp.iloc[1:].copy()
        df_npp["production_mode"] = df_npp["production_mode"].ffill()

        df_npp["region"] = (
            df_npp["power_station"]
            .apply(lambda x: NPP_REGION_MAPPING[x] if x in NPP_REGION_MAPPING else None)
            .ffill()
        )
        df_zone = df_npp.loc[df_npp["region"] == zone_key].copy()
        df_zone = df_zone.loc[~df_zone.power_station.isna()]
        df_zone = df_zone[df_zone.power_station.str.contains("TYPE:")]
        df_zone = df_zone[["production_mode", "value"]]
        df_zone = df_zone.groupby(["production_mode"]).sum()
        production = {}
        for mode in df_zone.index:
            production[NPP_MODE_MAPPING[mode]] = round(
                df_zone.iloc[df_zone.index.get_indexer_for([mode])[0]].get("value")
                / CONVERSION_GWH_MW,
                3,
            )
        return production
    else:
        raise ParserException(
            parser="IN.py",
            message=f"{target_datetime}: {zone_key} conventional production data is not available : [{r.status_code}]",
        )


def format_ren_production_data(url: str, zone_key: str) -> Dict[str, Any]:
    """Formats daily renewable production data for each zone"""
    df_ren = pd.read_excel(url, engine="openpyxl", header=5, skipfooter=2)
    df_ren = df_ren.dropna(axis=0, how="all")
    df_ren = df_ren.rename(
        columns={
            df_ren.columns[1]: "region",
            df_ren.columns[2]: "wind",
            df_ren.columns[3]: "solar",
            df_ren.columns[4]: "unknown",
        }
    )
    df_ren.loc[:, "zone_key"] = (
        df_ren["region"].apply(lambda x: x if "Region" in x else np.nan).backfill()
    )
    df_ren["zone_key"] = df_ren["zone_key"].str.strip()
    df_ren["zone_key"] = df_ren["zone_key"].map(CEA_REGION_MAPPING)

    zone_data = df_ren.loc[
        (df_ren.zone_key == zone_key) & (~df_ren.region.str.contains("Region"))
    ][["wind", "solar", "unknown"]].sum()

    renewable_production = {
        key: round(zone_data.get(key) / CONVERSION_GWH_MW, 3) for key in zone_data.index
    }
    return renewable_production


def fetch_cea_production(
    zone_key: str,
    target_datetime: datetime,
    session: Session = Session(),
    logger: Logger = getLogger(__name__),
) -> Dict[str, Any]:
    """Gets production data for wind, solar and other renewables
    Other renewables includes a share of hydro, biomass and others and will categorized as unknown
    DISCLAIMER: this data is only available since 2020/12/17"""
    cea_data_url = (
        "https://cea.nic.in/wp-admin/admin-ajax.php?action=getpostsfordatatables"
    )
    r_all_data: Response = session.get(cea_data_url)
    if r_all_data.status_code == 200:
        all_data = r_all_data.json()["data"]
        target_elem = [
            elem
            for elem in all_data
            if target_datetime.strftime("%Y-%m-%d") in elem["date"]
        ]
        if len(target_elem) > 0:
            if target_elem[0]["link"] == "file_not_found":
                raise ParserException(
                    parser="IN.py",
                    message=f"{target_datetime}: {zone_key} renewable production data is not available",
                )
            else:
                target_url = target_elem[0]["link"].split(": ")[0]
                formatted_url = target_url.split("^")[0]
                r: Response = session.get(formatted_url)
                renewable_production = format_ren_production_data(
                    url=r.url, zone_key=zone_key
                )
                return renewable_production
    else:
        raise ParserException(
            parser="IN.py",
            message=f"{target_datetime}: {zone_key} renewable production data is not available, {r_all_data.status_code}",
        )


def fetch_production(
    zone_key: str,
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> List[Dict[str, Any]]:
    if target_datetime is None:
        target_datetime = get_start_of_day(dt=UTC.localize(datetime.now()))
    else:
        target_datetime = get_start_of_day(dt=target_datetime)
        if target_datetime < START_DATE_RENEWABLE_DATA:
            raise ParserException(
                parser="IN.py",
                message=f"{target_datetime}: {zone_key} renewable production data is not available before 2020/12/17, data is not collected prior to this data",
            )

    all_data_points = []
    days_lookback_to_try = list(range(1, 8))
    for days_lookback in days_lookback_to_try:
        _target_datetime = target_datetime - timedelta(days=days_lookback)
        try:
            renewable_production = fetch_cea_production(
                zone_key=zone_key,
                session=session,
                target_datetime=_target_datetime,
            )
            conventional_production = fetch_npp_production(
                zone_key=zone_key,
                session=session,
                target_datetime=_target_datetime,
            )
            production = {**conventional_production, **renewable_production}
            all_data_points += daily_to_hourly_production_data(
                target_datetime=_target_datetime,
                production=production,
                zone_key=zone_key,
            )
        except:
            logger.warning(
                f"{zone_key}: production not available for {_target_datetime}"
            )

    return all_data_points


def daily_to_hourly_production_data(
    target_datetime: datetime, production: dict, zone_key: str
) -> List[Dict[str, Any]]:
    """convert daily power production average to hourly values"""
    all_hourly_production = []
    for hour in list(range(0, 24)):
        hourly_production = {
            "zoneKey": zone_key,
            "datetime": target_datetime.replace(hour=hour),
            "production": production,
            "source": "npp.gov.in, cea.nic.in",
        }
        all_hourly_production.append(hourly_production)
    return all_hourly_production


def get_start_of_day(dt: datetime) -> datetime:
    dt_localised = arrow.get(dt).to(IN_TZ).datetime
    dt_start = dt_localised.replace(hour=0, minute=0, second=0, microsecond=0)
    return dt_start


# if __name__ == "__main__":
#     print("fetch_production() -> ")
#     print(fetch_production(zone_key="IN-NO"))
