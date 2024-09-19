#!/usr/bin/env python3

"""Parser for the Orkney Islands"""

from datetime import datetime
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from requests import Response, Session

from parsers.lib.session import get_session_with_legacy_adapter

# There is a 2MW storage battery on the islands.
# http://www.oref.co.uk/orkneys-energy/innovations-2/

TIMEZONE = ZoneInfo("Europe/London")
DATETIME_LINK = "https://distribution.ssen.co.uk/anmorkneygraph/"
GENERATION_LINK = "https://distribution.ssen.co.uk/Sse_Components/Views/Controls/FormControls/Handlers/ActiveNetworkManagementHandler.ashx?action=graph&contentId=14973&_=1537467858726"

GENERATION_MAPPING = {
    "Live Demand": "Demand",
    "Orkney ANM": "ANM Renewables",
    "Non-ANM Renewable Generation": "Renewables",
}


def get_json_data():
    """
    Requests json data and extracts generation information.
    Returns a dictionary.
    """
    req = get_session_with_legacy_adapter().get(GENERATION_LINK)
    raw_json_data = req.json()

    generation_data = raw_json_data["data"]["datasets"]

    production = {}
    for datapoint in generation_data:
        gen_type = datapoint["label"]
        val = float(max(datapoint["data"]))
        production[gen_type] = val

    for k in list(production.keys()):
        if k not in GENERATION_MAPPING:
            # Get rid of unneeded keys.
            production.pop(k)

    return production


def get_datetime():
    """
    Extracts data timestamp from html and checks it's less than 2 hours old.
    Returns a Python datetime object.
    """
    req: Response = get_session_with_legacy_adapter().get(DATETIME_LINK)
    soup = BeautifulSoup(req.text, "html.parser")

    data_table = soup.find("div", {"class": "Widget-Base Widget-ANMGraph"})

    last_updated = data_table.find("div", {"class": "button"}).contents
    raw_dt = last_updated[-1].strip().split("  ", 1)[-1]
    naive_dt = datetime.strptime(raw_dt, "%d %B %Y %H:%M:%S")
    aware_dt = naive_dt.replace(tzinfo=TIMEZONE)

    current_time = datetime.now(tz=TIMEZONE)
    diff = current_time - aware_dt

    if diff.total_seconds() > 7200:
        raise ValueError(
            f"Orkney data is too old to use, data is {int(diff.total_seconds() / 3600)} hours old."
        )

    return aware_dt


def fetch_production(
    zone_key: str = "GB-ORK",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """Requests the last known production mix (in MW) of a given country."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    raw_data = get_json_data()
    raw_data.pop("Live Demand")

    mapped_data = {}
    mapped_data["unknown"] = raw_data.get("Orkney ANM", 0.0) + raw_data.get(
        "Non-ANM Renewable Generation", 0.0
    )

    dt = get_datetime()

    data = {
        "zoneKey": zone_key,
        "datetime": dt,
        "production": mapped_data,
        "storage": {
            "battery": None,
        },
        "source": "ssen.co.uk",
    }

    return data


def fetch_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """Requests the last known power exchange (in MW) between two zones."""
    sorted_zone_keys = "->".join(sorted([zone_key1, zone_key2]))
    raw_data = get_json_data()
    dt = get_datetime()

    # +ve importing from mainland
    # -ve export to mainland
    total_generation = raw_data["Orkney ANM"] + raw_data["Non-ANM Renewable Generation"]
    netflow = raw_data["Live Demand"] - total_generation

    data = {
        "netFlow": netflow,
        "datetime": dt,
        "sortedZoneKeys": sorted_zone_keys,
        "source": "ssen.co.uk",
    }

    return data


if __name__ == "__main__":
    print("fetch_production() ->")
    print(fetch_production())
    print("fetch_exchange(GB, GB-ORK)")
    print(fetch_exchange("GB", "GB-ORK"))
