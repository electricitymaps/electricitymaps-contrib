#!/usr/bin/env python3

# The arrow library is used to handle datetimes
import json
from datetime import datetime
from logging import Logger, getLogger
from typing import Optional

import arrow
from bs4 import BeautifulSoup

# The request library is used to fetch content through HTTP
from requests import Session

timezone = "Pacific/Auckland"

NZ_PRICE_REGIONS = set([i for i in range(1, 14)])


def fetch(session: Optional[Session] = None):
    r = session or Session()
    url = "https://www.transpower.co.nz/power-system-live-data"
    response = r.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    for item in soup.find_all("script"):
        if "src" in item.attrs:
            continue
        body = item.contents[0]
        if not body.startswith("jQuery.extend(Drupal.settings"):
            continue
        obj = json.loads(
            body.replace("jQuery.extend(Drupal.settings, ", "").replace(");", "")
        )
        break
    return obj


def fetch_price(
    zone_key: str = "NZ",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """
    Requests the current price of electricity based on the zone key.

    Note that since EM6 breaks the electricity price down into regions,
    the regions are averaged out for each island.
    """
    if target_datetime:
        raise NotImplementedError(
            "This parser is not able to retrieve data for past dates"
        )

    r = session or Session()
    url = "https://api.em6.co.nz/ords/em6/data_api/region/price/"
    response = r.get(url, verify=False)
    obj = response.json()
    region_prices = []

    regions = NZ_PRICE_REGIONS
    for item in obj.get("items"):
        region = item.get("grid_zone_id")
        if region in regions:
            time = item.get("timestamp")
            price = float(item.get("price"))
            region_prices.append(price)

    avg_price = sum(region_prices) / len(region_prices)
    datetime = arrow.get(time, tzinfo="UTC")

    return {
        "datetime": datetime.datetime,
        "price": avg_price,
        "currency": "NZD",
        "source": "api.em6.co.nz",
        "zoneKey": zone_key,
    }


def fetch_production(
    zone_key: str = "NZ",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """Requests the last known production mix (in MW) of a given zone."""
    if target_datetime:
        raise NotImplementedError(
            "This parser is not able to retrieve data for past dates"
        )

    obj = fetch(session)

    datetime = arrow.get(str(obj["soPgenGraph"]["timestamp"]), "X").datetime

    region_key = "New Zealand"
    productions = obj["soPgenGraph"]["data"][region_key]

    data = {
        "zoneKey": zone_key,
        "datetime": datetime,
        "production": {
            "coal": productions.get("Coal", {"generation": None})["generation"],
            "oil": productions.get("Liquid", {"generation": None})["generation"],
            "gas": productions.get("Gas", {"generation": None})["generation"],
            "geothermal": productions.get("Geothermal", {"generation": None})[
                "generation"
            ],
            "wind": productions.get("Wind", {"generation": None})["generation"],
            "hydro": productions.get("Hydro", {"generation": None})["generation"],
            "solar": productions.get("Solar", {"generation": None})["generation"],
            "unknown": productions.get("Co-Gen", {"generation": None})["generation"],
            "nuclear": 0,  # famous issue in NZ politics
        },
        "capacity": {
            "coal": productions.get("Coal", {"capacity": None})["capacity"],
            "oil": productions.get("Liquid", {"capacity": None})["capacity"],
            "gas": productions.get("Gas", {"capacity": None})["capacity"],
            "geothermal": productions.get("Geothermal", {"capacity": None})["capacity"],
            "wind": productions.get("Wind", {"capacity": None})["capacity"],
            "hydro": productions.get("Hydro", {"capacity": None})["capacity"],
            "solar": productions.get("Solar", {"capacity": None})["capacity"],
            "battery storage": productions.get("Battery", {"capacity": None})[
                "capacity"
            ],
            "unknown": productions.get("Co-Gen", {"capacity": None})["capacity"],
            "nuclear": 0,  # famous issue in NZ politics
        },
        "storage": {
            "battery": productions.get("Battery", {"generation": None})["generation"],
        },
        "source": "transpower.co.nz",
    }

    return data


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""
    print("fetch_price(NZ) ->")
    print(fetch_price("NZ"))
    print("fetch_production(NZ) ->")
    print(fetch_production("NZ"))
