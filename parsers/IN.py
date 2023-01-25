#!usr/bin/env python3

"""Parser for all of India"""


from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Optional

import arrow
import numpy as np
import pandas as pd
import pytz
from bs4 import BeautifulSoup
from requests import Response, Session

from parsers.lib.exceptions import ParserException
from parsers.lib.validation import validate_consumption

IN_NO_TZ = pytz.timezone("Asia/Kolkata")
CONVERSION_MWH_MW = 0.024
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


def get_data(session: Optional[Session]):
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


def fetch_consumption(
    zone_key: str,
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
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
        "datetime": datetime.now(tz=IN_NO_TZ),
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
) -> dict:
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
                / CONVERSION_MWH_MW,
                3,
            )
        return production
    else:
        raise ParserException(
            parser="IN.py",
            message=f"{target_datetime}: {zone_key} conventional production data is not available : [{r.status_code}]",
        )

def format_ren_production_data(url: str, zone_key:str) -> dict:
    """Formats daily renewable production data for each zone"""
    df_ren = pd.read_excel(
        url, engine="openpyxl", header=5, skipfooter=2
    )
    df_ren = df_ren.dropna(axis=0, how='all')
    df_ren = df_ren.rename(
        columns={
            df_ren.columns[1]: "region",
            df_ren.columns[2]: "wind",
            df_ren.columns[3]: "solar",
            df_ren.columns[4]: "unknown",
        }
    )
    df_ren.loc[:, "zone_key"] = (
        df_ren["region"]
        .apply(lambda x: x if "Region" in x else np.nan)
        .backfill()
    )
    df_ren["zone_key"] = df_ren["zone_key"].str.strip()
    df_ren["zone_key"] = df_ren["zone_key"].map(CEA_REGION_MAPPING)

    zone_data = df_ren.loc[
        (df_ren.zone_key == zone_key) & (~df_ren.region.str.contains("Region"))
    ][["wind", "solar", "unknown"]].sum()

    renewable_production = {
        key: round(zone_data.get(key) / CONVERSION_MWH_MW, 3)
        for key in zone_data.index
    }
    return renewable_production

def fetch_cea_production(
    zone_key: str,
    target_datetime: datetime,
    session: Session = Session(),
    logger: Logger = getLogger(__name__),
) -> dict:
    """Gets production data for wind, solar and other renewables
    Other renewables includes a share of hydro, biomass and others and will categorized as unknown
    DISCLAIMER: this data is only available since 2020/12/17"""

    # the following list of links is a combination of possible names for renewable reports. NB: this doesn't include all possible links but covers the majority
    cea_links = [
        "https://cea.nic.in/wp-content/uploads/daily_reports/{date:%d_%b_%Y}_Daily_Report.xlsx",
        "https://cea.nic.in/wp-content/uploads/daily_reports/{date:%d_%m_%Y}_Daily_Report.xlsx",
        "https://cea.nic.in/wp-content/uploads/daily_reports/DailyRE{date:%d_%m_%Y}.xlsx",
        "https://cea.nic.in/wp-content/uploads/daily_reports/DailyRE{date:%d%m%Y}.xlsx",
        "https://cea.nic.in/wp-content/uploads/daily_reports/{date.day}_{date:%B__%Y}.xlsx",
        "https://cea.nic.in/wp-content/uploads/daily_reports/{date.day}_{date:%B_%Y}.xlsx",
        "https://cea.nic.in/wp-content/uploads/daily_reports/{date.day}_{date:%B_%Y}_Daily_Report.xlsx",
        "https://cea.nic.in/wp-content/uploads/daily_reports/{date.day}_{date:%b__%Y}.xlsx",
        "https://cea.nic.in/wp-content/uploads/daily_reports/{date.day}_{date:%b_%Y}.xlsx",
        "https://cea.nic.in/wp-content/uploads/daily_reports/{date.day}_{date.month}_{date.year}_Daily_Report.xlsx",
    ]
    i = 0
    link_found = False
    while i in range(len(cea_links)) and not link_found:
        r = session.get(cea_links[i].format(date=target_datetime))
        if r.status_code == 200:
            link_found = True
        i += 1
    if link_found:
       renewable_production= format_ren_production_data(url=r.url, zone_key=zone_key)
    else:
        renewable_production = fetch_renewablesindia_production(
            zone_key=zone_key, target_datetime=target_datetime
        )

    if len(renewable_production):
        return renewable_production
    else:
        raise ParserException(
            parser="IN.py",
            message=f"{target_datetime}: {zone_key} renewable production data is not available, {r.status_code}",
        )


def fetch_renewablesindia_production(
    zone_key: str,
    target_datetime: datetime,
    session: Session = Session(),
    logger: Logger = getLogger(__name__),
) -> dict:
    """gets data from India Renewable dashboard, delayed but naming is consistent unlike CEA reports"""
    main_url = "https://www.renewablesindia.in"
    params = {
        "utf8": "✓",
        "report_type": "daily",
        "sub_report_type": "state_isgs",
        "daily_start_date": (target_datetime - timedelta(days=20)).strftime("%Y-%m-%d"),
        "daily_end_date": (target_datetime + timedelta(days=20)).strftime("%Y-%m-%d"),
        "commit": "Apply",
    }

    r: Response = session.get(main_url + "/reports?", params=params)
    if r.status_code == 200:
        soup = BeautifulSoup(r.content, "html.parser")
        href_tags = soup.find_all("a", href=True, attrs={"target": "_blank", "alt": ""})
        excel_elems = []
        for elem in href_tags:
            if ".xlsx" in elem.get("href"):
                excel_elems += [elem.get("href")]
        target_dt_file = [
                    elem
                    for elem in excel_elems
                    if target_datetime.strftime("%d%m%Y") in elem
                ]
        if len(target_dt_file) > 0:
            target_url = (
                main_url
                + target_dt_file[0]
            )
            r_excel = session.get(target_url)
            return format_ren_production_data(url = r_excel.url, zone_key=zone_key)
        else:
            raise ParserException(
                parser="IN.py",
                message=f"{target_datetime}: {zone_key} renewable production data is not available",
            )


def fetch_production(
    zone_key: str,
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    if target_datetime is None:
        target_datetime = arrow.now(tz=IN_NO_TZ).floor("day").datetime - timedelta(
            days=2
        )
    elif target_datetime < datetime(2020, 5, 1).replace(tzinfo=IN_NO_TZ):
        raise ParserException(
            parser="IN.py",
            message=f"{target_datetime}: {zone_key} renewable production data is not available before 2020/12/17, data is not collected prior to this data",
        )
    else:
        target_datetime = (
            arrow.get(target_datetime).floor("day").datetime.replace(tzinfo=IN_NO_TZ)
        )

    renewable_production = fetch_cea_production(
        zone_key=zone_key, session=session, target_datetime=target_datetime
    )
    conventional_production = fetch_npp_production(
        zone_key=zone_key, session=session, target_datetime=target_datetime
    )
    data_point = {
        "zoneKey": zone_key,
        "datetime": target_datetime,
        "production": {**conventional_production, **renewable_production},
        "source": "npp.gov.in, cea.nic.in",
    }

    return data_point


if __name__ == "__main__":
    print("fetch_production() -> ")
    print(fetch_production(zone_key="IN-NO"))
