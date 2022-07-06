#!/usr/bin/env python3

# The arrow library is used to handle datetimes
import json

import arrow

# The request library is used to fetch content through HTTP
import requests
from bs4 import BeautifulSoup

timezone = "Pacific/Auckland"

NZ_PRICE_REGIONS = set([i for i in range(1, 14)])


def fetch(session=None):
    r = session or requests.session()
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


def fetch_price(zone_key="NZ", session=None, target_datetime=None, logger=None) -> dict:
    """
    Requests the current price of electricity based on the zone key.

    Note that since EM6 breaks the electricity price down into regions,
    the regions are averaged out for each island.
    """
    if target_datetime:
        raise NotImplementedError(
            "This parser is not able to retrieve data for past dates"
        )

    r = session or requests.session()
    url = "https://api.em6.co.nz/ords/em6/data_api/region/price/"
    response = requests.get(url, verify=False)
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
    zone_key="NZ", session=None, target_datetime=None, logger=None
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
            "coal": productions.get("Coal", {"generation": 0.0})["generation"],
            "oil": productions.get("Liquid", {"generation": 0.0})["generation"],
            "gas": productions.get("Gas", {"generation": 0.0})["generation"],
            "geothermal": productions.get("Geothermal", {"generation": 0.0})[
                "generation"
            ],
            "wind": productions.get("Wind", {"generation": 0.0})["generation"],
            "hydro": productions.get("Hydro", {"generation": 0.0})["generation"],
            "unknown": productions.get("Co-Gen", {"generation": 0.0})["generation"],
            "nuclear": 0,  # famous issue in NZ politics
        },
        "capacity": {
            "coal": productions.get("Coal", {"capacity": 0.0})["capacity"],
            "oil": productions.get("Liquid", {"capacity": 0.0})["capacity"],
            "gas": productions.get("Gas", {"capacity": 0.0})["capacity"],
            "geothermal": productions.get("Geothermal", {"capacity": 0.0})["capacity"],
            "wind": productions.get("Wind", {"capacity": 0.0})["capacity"],
            "hydro": productions.get("Hydro", {"capacity": 0.0})["capacity"],
            "battery storage": productions.get("Battery", {"capacity": 0.0})[
                "capacity"
            ],
            "unknown": productions.get("Co-Gen", {"capacity": 0.0})["capacity"],
            "nuclear": 0,  # famous issue in NZ politics
        },
        "storage": {
            "battery": productions.get("Battery", {"generation": 0.0})["generation"],
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
