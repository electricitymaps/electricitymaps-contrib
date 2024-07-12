#!usr/bin/env python3

"""Parser for all of India"""

from datetime import datetime, timedelta, timezone
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

import arrow
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from requests import Response, Session

from electricitymap.contrib.lib.models.event_lists import (
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.exceptions import ParserException

IN_TZ = ZoneInfo("Asia/Kolkata")
START_DATE_RENEWABLE_DATA = arrow.get("2020-12-17", tzinfo=IN_TZ).datetime
CONVERSION_GWH_MW = 0.024
GENERATION_MAPPING = {
    "THERMAL GENERATION": "coal",
    "GAS GENERATION": "gas",
    "HYDRO GENERATION": "hydro",
    "NUCLEAR GENERATION": "nuclear",
    "RENEWABLE GENERATION": "unknown",
}
INDIA_PROXY = "https://in-proxy-jfnx5klx2a-el.a.run.app"
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
    "SOUTHERN": "IN-SO",
    "NORTH EASTERN": "IN-NE",
}

CEA_REGION_MAPPING = {
    "उत्तरी क्षेत्र / Northern Region": "IN-NO",
    "पश्चिमी क्षेत्र / Western Region": "IN-WE",
    "दक्षिणी क्षेत्र / Southern Region": "IN-SO",
    "पूर्वी क्षेत्र/ Eastern Region": "IN-EA",
    "उत्तर-पूर्वी क्षेत्र  / North-Eastern Region": "IN-NE",
}

DEMAND_URL_VIDYUTPRAVAH = "{proxy}/state-data/{state}?host=https://vidyutpravah.in"
DEMAND_URL_MERITINDIA = (
    "{proxy}/StateWiseDetails/BindCurrentStateStatus?host=https://meritindia.in"
)

# States codes as on meritindia.in
STATE_CODES = {
    "andhra-pradesh": "AP",
    "arunachal-pradesh": "ACP",
    "assam": "ASM",
    "bihar": "BHR",
    "chandiagarh": "CHG",
    "chhattisgarh": "CTG",
    "dadra-nagar-haveli": "DNH",
    "daman-diu": "DND",
    "delhi": "DL",
    "goa": "GOA",
    "gujarat": "GJT",
    "haryana": "HRN",
    "himachal-pradesh": "HP",
    "jammu-kashmir": "JAK",
    "jharkhand": "JHK",
    "karnataka": "KRT",
    "kerala": "KRL",
    "madhya-pradesh": "MPD",
    "maharashtra": "MHA",
    "manipur": "MIP",
    "meghalaya": "MGA",
    "mizoram": "MZM",
    "nagaland": "NGD",
    "odisha": "ODI",
    "puducherry": "PU",
    "punjab": "PNB",
    "rajasthan": "RJ",
    "sikkim": "SKM",
    "tamil-nadu": "TND",
    "telangana": "TLG",
    "tripura": "TPA",
    "uttar-pradesh": "UP",
    "uttarakhand": "UTK",
    "west-bengal": "WB",
}


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


def get_data(session: Session | None) -> dict[str, Any]:
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
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> dict[str, Any]:
    """Requests the last known production mix (in MW) of a given zone."""

    if target_datetime is not None:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    raw_data = get_data(session)
    processed_data = {k: float(v.replace(",", "")) for k, v in raw_data.items()}
    processed_data.pop("DEMANDMET", None)

    for k in processed_data:
        if k not in GENERATION_MAPPING:
            processed_data.pop(k)
            logger.warning(
                f"Key '{k}' in IN is not mapped to type.", extra={"key": "IN"}
            )

    mapped_production = {GENERATION_MAPPING[k]: v for k, v in processed_data.items()}

    data = {
        "zoneKey": zone_key,
        "datetime": datetime.now(tz=IN_TZ),
        "production": mapped_production,
        "storage": {},
        "source": "meritindia.in",
    }

    return data


def fetch_consumption_from_vidyutpravah(
    zone_key: str,
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> TotalConsumptionList:
    """Fetches live consumption from government dashboard. Consumption is available per state and is then aggregated at regional level.
    Data is not available for the following states: Ladakh (disputed territory), Daman & Diu, Dadra & Nagar Haveli, Lakshadweep
    """
    if target_datetime is not None:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    total_consumption = 0
    for state in STATES_MAPPING[zone_key]:
        # By default the request headers are set to accept gzip.
        # If this header is set, the proxy will not decompress the content, therefore we set it to an empty string.
        resp: Response = session.get(
            DEMAND_URL_VIDYUTPRAVAH.format(proxy=INDIA_PROXY, state=state),
            headers={"User-Agent": "Mozilla/5.0", "Accept-Encoding": ""},
        )
        soup = BeautifulSoup(resp.content, "html.parser")
        try:
            state_consumption = int(
                soup.find(
                    "span", attrs={"class": "value_DemandMET_en value_StateDetails_en"}
                )
                .text.strip()
                .split()[0]
                .replace(",", "")
            )
        except Exception as e:
            raise ParserException(
                parser="IN.py",
                message=f"{target_datetime}: consumption data is not available for {zone_key}",
            ) from e
        total_consumption += state_consumption

    if total_consumption == 0:
        raise ParserException(
            parser="IN.py",
            message=f"{target_datetime}: No valid consumption data found for {zone_key}",
        )

    consumption_list = TotalConsumptionList(logger=logger)
    consumption_list.append(
        zoneKey=ZoneKey(zone_key),
        datetime=datetime.now(tz=IN_TZ),
        consumption=total_consumption,
        source="vidyupravah.in",
    )

    return consumption_list


def fetch_consumption_from_meritindia(
    zone_key: ZoneKey,
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> TotalConsumptionList:
    """Fetches the live consumption from the Merit Order Despatch of Electricity.
    This source seems to be a bit more stable right now than vidyutpravah.in"""
    if target_datetime is not None:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    import concurrent.futures

    total_consumption = 0
    futures = []

    def fetch_state_consumption(session, state):
        resp: Response = session.post(
            DEMAND_URL_MERITINDIA.format(proxy=INDIA_PROXY),
            data={"StateCode": STATE_CODES[state]},
        )
        data = resp.json()[0]
        return float(str(data["Demand"]).replace(",", ""))

    with concurrent.futures.ThreadPoolExecutor() as executor:
        for state in STATES_MAPPING[zone_key]:
            future = executor.submit(fetch_state_consumption, session, state)
            futures.append(future)

        for future in concurrent.futures.as_completed(futures):
            total_consumption += future.result()

    consumption_list = TotalConsumptionList(logger=logger)
    consumption_list.append(
        zoneKey=ZoneKey(zone_key),
        datetime=datetime.now(tz=IN_TZ),
        consumption=total_consumption,
        source="meritindia.in",
    )
    return consumption_list


def fetch_npp_production(
    zone_key: str,
    target_datetime: datetime,
    session: Session = Session(),
    logger: Logger = getLogger(__name__),
) -> dict[str, Any]:
    """Gets production for conventional thermal, nuclear and hydro from NPP daily reports
    This data most likely doesn't inlcude distributed generation"""

    npp_url = f"https://npp.gov.in/public-reports/cea/daily/dgr/{target_datetime:%d-%m-%Y}/dgr2-{target_datetime:%Y-%m-%d}.xls"
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
        df_npp["region"] = (
            df_npp["power_station"].apply(lambda x: NPP_REGION_MAPPING.get(x)).ffill()
        )
        df_npp = df_npp[["region", "production_mode", "value"]]

        df_npp_filtered = df_npp.loc[~df_npp["production_mode"].isna()].copy()

        df_zone = df_npp_filtered.loc[df_npp_filtered["region"] == zone_key].copy()
        df_zone["production_mode"] = df_zone["production_mode"].map(NPP_MODE_MAPPING)
        production_in_zone = df_zone.groupby(["production_mode"])["value"].sum()
        production_dict = {
            mode: round(production_in_zone.get(mode) / CONVERSION_GWH_MW, 3)
            for mode in production_in_zone.index
        }
        return production_dict
    else:
        raise ParserException(
            parser="IN.py",
            message=f"{target_datetime}: {zone_key} conventional production data is not available : [{r.status_code}]",
        )


def fetch_consumption(
    zone_key: ZoneKey,
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    return fetch_consumption_from_meritindia(
        zone_key=zone_key,
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    ).to_list()


def format_ren_production_data(url: str, zone_key: str) -> dict[str, Any]:
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
) -> dict[str, Any] | None:
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
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    if target_datetime is None:
        target_datetime = get_start_of_day(dt=datetime.now(timezone.utc))
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
                logger=logger,
            )
        except Exception:
            logger.warning(
                f"{zone_key}: production not available for {_target_datetime}"
            )
    return all_data_points


def daily_to_hourly_production_data(
    target_datetime: datetime, production: dict, zone_key: str, logger: Logger
) -> list[dict[str, Any]]:
    """convert daily power production average to hourly values"""
    all_hourly_production = ProductionBreakdownList(logger)
    production_mix = ProductionMix()
    for mode, value in production.items():
        production_mix.add_value(mode, value)
    for hour in list(range(0, 24)):
        all_hourly_production.append(
            zoneKey=ZoneKey(zone_key),
            datetime=target_datetime.replace(hour=hour),
            production=production_mix,
            source="npp.gov.in, cea.nic.in",
        )
    return all_hourly_production.to_list()


def get_start_of_day(dt: datetime) -> datetime:
    dt_localised = arrow.get(dt).to(IN_TZ).datetime
    dt_start = dt_localised.replace(hour=0, minute=0, second=0, microsecond=0)
    return dt_start


if __name__ == "__main__":
    # print(fetch_production(target_datetime=datetime(2021, 8, 16), zone_key="IN-WE"))
    print(fetch_consumption(zone_key=ZoneKey("IN-NO")))
