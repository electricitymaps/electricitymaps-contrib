#!usr/bin/env python3

"""Parser for all of India"""

import logging

import arrow
import requests
from bs4 import BeautifulSoup

GENERATION_MAPPING = {
    "THERMAL GENERATION": "coal",
    "GAS GENERATION": "gas",
    "HYDRO GENERATION": "hydro",
    "NUCLEAR GENERATION": "nuclear",
    "RENEWABLE GENERATION": "unknown",
}

GENERATION_URL = "http://meritindia.in/Dashboard/BindAllIndiaMap"


def get_data(session):
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
    zone_key="IN",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
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


if __name__ == "__main__":
    print("fetch_production() -> ")
    print(fetch_production())
