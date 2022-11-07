#!/usr/bin/env python3


from datetime import datetime
from logging import Logger, getLogger
from typing import Dict, Optional

import pandas as pd
from requests import Session

from electricitymap.contrib.config.constants import PRODUCTION_MODES
from parsers.lib.exceptions import ParserException


IN_W_PROXY = "https://in-proxy-jfnx5klx2a-el.a.run.app"
HOME_URL = f"{IN_W_PROXY}/https://www.wrldc.in/content/165_1_GeneratorScheduleVsActual.aspx?host=https://www.wrldc.in"
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


def fetch_production(
    zone_key: str = "IN_W",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> Dict:

    r = session or Session()
    request_payload = {"date": target_datetime.strftime("%Y-%m-%d")}
    resp = r.post(PRODUCTION_URL, json=request_payload)
    return resp.text
