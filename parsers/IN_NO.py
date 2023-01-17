#!/usr/bin/env python3


import json
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Optional

import arrow
import pandas as pd
import pytz
from bs4 import BeautifulSoup
from requests import Response, Session

from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

IN_NO_TZ = pytz.timezone("Asia/Kolkata")

IN_NO_PROXY = "https://in-proxy-jfnx5klx2a-el.a.run.app"
PRODUCTION_URL = f"{IN_NO_PROXY}/GeneratorSchedule_data.aspx/Get_GeneratorScheduleData_state_Wise?host=https://www.wrldc.in"
EXCHANGE_URL = f"{IN_NO_PROXY}/InterRegionalLinks_Data.aspx/Get_InterRegionalLinks_Region_Wise?host=https://www.wrldc.in"
SOLAR_FORECAST_URL = (
    f"{IN_NO_PROXY}/Websitedata/Solar/slr%d%m%Y.csv?host=https://nrldc.in"
)

STATES = [
    "delhi",
    "haryana",
    "himachal-pradesh",
    "jammu-kashmir",
    "punjab",
    "rajasthan",
    "uttar-pradesh",
    "uttarakhand",
]
LIVE_DEMAND_URL = "https://vidyutpravah.in/state-data/{state}"

CONSUMPTION_COLUMNS = [
    "Pun_Drwl",
    "Har_Drwl",
    "Raj_Drwl",
    "Del_Drwl",
    "UP_Drwl",
    "Utt_Drwl",
    "HP_Drwl",
    "JK_Drwl",
    "Chd_Drwl",
]
EXCHANGE_MAPPING = {"IN-EA->IN-NO": "ER-NR", "IN-NO->IN-WE": "WR-NR"}
POWER_PLANT_MAPPING = {
    "SINGRAULI": "coal",
    "Rihand1": "coal",
    "Rihand 2": "coal",
    "DADRIT": "coal",
    "DADRT2": "coal",
    "Unchahar1": "coal",
    "Unchahar2": "coal",
    "Unchahar3": "coal",
    "DadriGPS": "gas",
    "AntaGPS": "gas",
    "AuraiyaGPS": "gas",
    "NAPS": "nuclear",
    "RAPP-B": "nuclear",
    "RAPP-C": "nuclear",
    "BSIUL": "hydro",
    "SALAL": "hydro",
    "TANAKPUR": "hydro",
    "CHAMERA_1": "hydro",
    "CHAMERA 2": "hydro",
    "URI": "hydro",
    "Dhauliganga": "hydro",
    "Dulhasti": "hydro",
    "Sewa - II": "hydro",
    "NJPC": "hydro",
    "TEHRI": "hydro",
    "BHAKRA": "hydro",
    "Dehar": "hydro",
    "Pong": "hydro",
    "ADHPL": "hydro",
    "JHAJJAR": "coal",
    "KOTESHWR": "hydro",
    "KWHEP": "hydro",
    "SCLTPS": "coal",
    "UNCHAHAR 4": "coal",
    "Chamera-3": "hydro",
    "Budhil": "hydro",
    "Uri-2": "hydro",
    "Rihand3": "coal",
    "Parbati-3": "hydro",
    "Rampur": "hydro",
    "Koldam": "hydro",
    "ERCPL": "solar",
    "SPCEPL": "solar",
    "RSWPL": "solar",
    "AHEJ1L-TOTAL": "wind",
    "RESJ3PL": "solar",
    "AHEJ2L": "wind",
    "AHEJ3L": "wind",
    "APFOL": "solar",
    "ASEPL_350": "solar",
    "RSBPL": "solar",
    "ARP1PL": "solar",
    "RSUPL": "solar",
    "AHEJ4L-Total": "wind",
    "AVAADA_RJHN": "solar",
    "NTPC_296": "solar",
    "AVAADA_SUSTAIN": "solar",
    "RSRPL": "solar",
    "AMPL": "solar",
    "ReNew-Bhadla": "solar",
    "Azure": "solar",
    "SB_Energy": "solar",
    "ARERJL(200MW)": "solar",
    "KSMPL_(50MW)": "solar",
    "ASEJTL_(50MW)": "solar",
    "TPREL_2*300": "solar",
    "APTFPL": "solar",
    "ACME": "solar",
    "Renew_Bikaner": "solar",
    "Clean_Solar": "solar",
    "APFTPL_2*300": "solar",
    "MRPL(250MW)": "solar",
    "SB_Six": "solar",
    "CSPJPL": "solar",
    "TS1PL": "solar",
    "AcHPPL": "solar",
    "MSUPL": "solar",
    "TPGEL": "solar",
    "KOLAYAT": "solar",
    "AvSEPL": "solar",
    "ASEJOPL": "wind",
    "Devikot": "solar",
}

PUNJAB_MERINT_URL = "https://meritindia.in/StateWiseDetails/ExportToExcel?StateCode=PNB&RecordDate=15%20Jan%202023&DiscomCode=0"


def fetch_live_consumption(
    session: Optional[Session] = None,
) -> dict:
    total_demand = 0
    for state in STATES:
        r = session.get(LIVE_DEMAND_URL.format(state=state))
        soup = BeautifulSoup(r.content, "html.parser")
        try:
            state_demand = int(
                soup.find(
                    "span", attrs={"class": "value_DemandMET_en value_StateDetails_en"}
                )
                .text.strip()
                .split()[0]
                .replace(",", "")
            )
        except:
            state_demand = 0
        total_demand += state_demand
    return total_demand


def fetch_solar_forecast(
    zone_key: str = "IN-WE",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    if target_datetime is None:
        target_datetime = datetime.now(tz=IN_NO_TZ)

    r = session.get(target_datetime.strftime(SOLAR_FORECAST_URL))


def fetch_sem_data(
    zone_key: str = "IN-WE",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    r = session.get("https://nrldc.in/reports/scada-sem-comparision-report/")
    soup = BeautifulSoup(r.content, "html.parser")
    all_links = soup.find_all(
        "a", attrs={"class": "wpdm-download-link wpdm-download-locked btn btn-primary "}
    )
    all_links_formatted = [
        link.get("onclick")
        .replace("location.href='", "")
        .replace("';return false;", "")
        for link in all_links
    ]
    week_number = target_datetime.isocalendar()[1]
    start_of_week = datetime.fromisocalendar(target_datetime.year, week_number, 1)
    end_of_week = datetime.fromisocalendar(
        target_datetime.year, week_number + 1, 1
    ) - timedelta(days=1)
    link = [
        link
        for link in all_links_formatted
        if (start_of_week.strftime("%d-%m-%Y") in link)
        and (end_of_week.strftime("%d-%m-%Y") in link)
    ]
    if not len(link):
        raise ParserException(
            parser="IN_NO.py",
            message=f"{target_datetime}: data is not available",
        )
    else:
        r_xls = session.get(link[0])
        data = pd.read_excel(r_xls.url, sheet_name="SEM")
        data = data.rename(
            columns={"ALL DATA IN MW": "datetime", "Unnamed: 1": "minute_block"}
        )
        data.columns = data.columns.str.strip()
        data = data.loc[data["datetime"].notna()].loc[1:]
        data.datetime = pd.to_datetime(data.datetime)
        data = data.loc[data.datetime == target_datetime]
        data["datetime"] = data.apply(
            lambda x: x.datetime + timedelta(minutes=(x["minute_block"] - 1) * 15),
            axis=1,
        )
        data = data.drop(columns=["minute_block"])

        data_production = data.set_index("datetime")[
            [col for col in data.columns if col in POWER_PLANT_MAPPING]
        ]
        data_production = pd.melt(
            data_production,
            var_name="production_mode",
            value_name="value",
            ignore_index=False,
        )
        data_production["production_mode"] = data_production["production_mode"].map(
            POWER_PLANT_MAPPING
        )
        data_production = data_production.groupby(
            [data_production.index, "production_mode"]
        ).sum()
