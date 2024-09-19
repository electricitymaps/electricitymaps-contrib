#!/usr/bin/env python3

# The datetime library is used to handle datetimes
import json
from datetime import datetime, timezone
from logging import Logger, getLogger

from bs4 import BeautifulSoup

# The request library is used to fetch content through HTTP
from requests import Session

time_zone = "Pacific/Auckland"

NZ_PRICE_REGIONS = set(range(1, 14))
PRODUCTION_URL = "https://www.transpower.co.nz/system-operator/live-system-and-market-data/consolidated-live-data"
PRICE_URL = "https://api.em6.co.nz/ords/em6/data_api/region/price/"


def fetch(session: Session | None = None):
    r = session or Session()
    url = PRODUCTION_URL
    response = r.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    for item in soup.find_all("script"):
        if item.attrs.get("data-drupal-selector"):
            body = item.contents[0]
            obj = json.loads(body)
    return obj


def fetch_price(
    zone_key: str = "NZ",
    session: Session | None = None,
    target_datetime: datetime | None = None,
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
    url = PRICE_URL
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
    date_time = datetime.strptime(time, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc
    )

    return {
        "datetime": date_time,
        "price": avg_price,
        "currency": "NZD",
        "source": "api.em6.co.nz",
        "zoneKey": zone_key,
    }


def fetch_production(
    zone_key: str = "NZ",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """Requests the last known production mix (in MW) of a given zone."""
    if target_datetime:
        raise NotImplementedError(
            "This parser is not able to retrieve data for past dates"
        )

    obj = fetch(session)

    date_time = datetime.fromtimestamp(obj["soPgenGraph"]["timestamp"], tz=timezone.utc)

    region_key = "New Zealand"
    productions = obj["soPgenGraph"]["data"][region_key]

    data = {
        "zoneKey": zone_key,
        "datetime": date_time,
        "production": {
            "coal": productions.get("Coal", {"generation": None})["generation"],
            "oil": productions.get("Diesel/Oil", {"generation": None})["generation"],
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
            "oil": productions.get("Diesel/Oil", {"capacity": None})["capacity"],
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
