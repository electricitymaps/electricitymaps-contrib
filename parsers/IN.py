#!usr/bin/env python3

"""Parser for all of India"""


from datetime import datetime
from logging import Logger, getLogger
from typing import Optional

import arrow
import pytz
from bs4 import BeautifulSoup
from requests import Response, Session

from parsers.lib.exceptions import ParserException
from parsers.lib.validation import validate_consumption

IN_NO_TZ = pytz.timezone("Asia/Kolkata")

GENERATION_MAPPING = {
    "THERMAL GENERATION": "coal",
    "GAS GENERATION": "gas",
    "HYDRO GENERATION": "hydro",
    "NUCLEAR GENERATION": "nuclear",
    "RENEWABLE GENERATION": "unknown",
}

GENERATION_URL = "http://meritindia.in/Dashboard/BindAllIndiaMap"

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
    return data


if __name__ == "__main__":
    print("fetch_consumption() -> ")
    print(fetch_consumption(zone_key="IN-NO"))
