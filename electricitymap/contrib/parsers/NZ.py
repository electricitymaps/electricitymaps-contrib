#!/usr/bin/env python3

# The datetime library is used to handle datetimes
import json
from datetime import datetime, timezone
from logging import Logger, getLogger
from typing import Any

from bs4 import BeautifulSoup

# The request library is used to fetch content through HTTP
from requests import Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.lib.models.event_lists import (
    PriceList,
    ProductionBreakdownList,
)
from electricitymap.contrib.lib.models.events import ProductionMix, StorageMix

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
    zone_key: ZoneKey = ZoneKey("NZ"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
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
    price_list = PriceList(logger)
    price_list.append(
        zoneKey=zone_key,
        price=avg_price,
        currency="NZD",
        datetime=date_time,
        source="api.em6.co.nz",
    )
    return price_list.to_list()


def fetch_production(
    zone_key: ZoneKey = ZoneKey("NZ"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests the last known production mix (in MW) of a given zone."""
    if target_datetime:
        raise NotImplementedError(
            "This parser is not able to retrieve data for past dates"
        )

    obj = fetch(session)

    date_time = datetime.fromtimestamp(obj["soPgenGraph"]["timestamp"], tz=timezone.utc)

    region_key = "New Zealand"
    productions = obj["soPgenGraph"]["data"][region_key]
    production_breakdowns = ProductionBreakdownList(logger)
    production_mix = ProductionMix()
    mix_mapping = {
        "coal": "Coal",
        "oil": "Diesel/Oil",
        "gas": "Gas",
        "geothermal": "Geothermal",
        "wind": "Wind",
        "hydro": "Hydro",
        "solar": "Solar",
        "unknown": "Co-Gen",
    }
    for mix_key, prod_key in mix_mapping.items():
        production_mix.add_value(
            mix_key, productions.get(prod_key, {"generation": None})["generation"]
        )
    production_mix.add_value("nuclear", 0)  # famous issue in NZ politics
    storage_mix = StorageMix()
    storage_mix.add_value(
        "battery", productions.get("Battery", {"generation": None})["generation"]
    )
    production_breakdowns.append(
        zoneKey=zone_key,
        datetime=date_time,
        production=production_mix,
        storage=storage_mix,
        source="transpower.co.nz",
    )
    capacity = {
        mix_key: productions.get(prod_key, {"capacity": None})["capacity"]
        for mix_key, prod_key in mix_mapping.items()
    }
    capacity["battery storage"] = productions.get("Battery", {"capacity": None})[
        "capacity"
    ]
    capacity["nuclear"] = 0  # famous issue in NZ politics
    return [{**e, **{"capacity": capacity}} for e in production_breakdowns.to_list()]


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""
    print("fetch_price(NZ) ->")
    print(fetch_price("NZ"))
    print("fetch_production(NZ) ->")
    print(fetch_production("NZ"))
