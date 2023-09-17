from collections import defaultdict
from datetime import datetime
from logging import Logger, getLogger
from typing import Any

from requests import Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    ProductionBreakdownList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey

URL = "http://tr.ons.org.br/Content/GetBalancoEnergetico/null"
SOURCE = "ons.org.br"

GENERATION_MAPPING = {
    "nuclear": "nuclear",
    "eolica": "wind",
    "termica": "unknown",
    "solar": "solar",
    "hidraulica": "hydro",
    "itaipu50HzBrasil": "hydro",  # BR_CS contains the Itaipu Dam.
    # We merge the hydro keys into one.
    "itaipu60Hz": "hydro",
}

# Those modes report self consumption, therefore they can be negative.
CORRECTED_NEGATIVE_PRODUCTION = {"solar"}

REGIONS = {
    "BR-NE": "nordeste",
    "BR-N": "norte",
    "BR-CS": "sudesteECentroOeste",
    "BR-S": "sul",
}

EXCHANGES = {
    "BR-CS->BR-S": {"name": "sul_sudeste", "flow": -1, "level": "intercambio"},
    "BR-CS->BR-NE": {"name": "sudeste_nordeste", "flow": 1, "level": "intercambio"},
    "BR-CS->BR-N": {"name": "sudeste_norteFic", "flow": 1, "level": "intercambio"},
    "BR-N->BR-NE": {"name": "norteFic_nordeste", "flow": 1, "level": "intercambio"},
    "BR-S->UY": {"name": "uruguai", "flow": 1, "level": "internacional"},
    "AR->BR-S": {"name": "argentina", "flow": -1, "level": "internacional"},
    "BR-S->PY": {"name": "paraguai", "flow": -1, "level": "internacional"},
}


def get_data(session: Session | None):
    """Requests generation data in json format."""
    s = session or Session()
    json_data = s.get(URL).json()

    return json_data


def production_processor(
    json_data: dict, zone_key: str
) -> tuple[datetime, ProductionMix]:
    """Extracts data timestamp and sums regional data into totals by key."""

    dt = datetime.fromisoformat(json_data["Data"])
    totals = defaultdict(lambda: 0.0)

    region = REGIONS[zone_key]
    breakdown = json_data[region]["geracao"]
    for generation, val in breakdown.items():
        totals[generation] += val

    del totals["total"]
    production = ProductionMix()
    for mode, value in totals.items():
        mode_name = GENERATION_MAPPING.get(mode, "unknown")
        production.add_value(
            mode_name, value, mode_name in CORRECTED_NEGATIVE_PRODUCTION
        )

    return dt, production


def fetch_production(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests the last known production mix (in MW) of a given country."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    data = get_data(session)
    date, production = production_processor(data, zone_key)
    productions = ProductionBreakdownList(logger)
    productions.append(
        zoneKey=zone_key,
        datetime=date,
        source=SOURCE,
        production=production,
    )

    return productions.to_list()


def get_exchange_flow(sorted_zone_keys: ZoneKey, raw_data: dict) -> float:
    """Returns the flow of the exchange between two regions."""
    name, flow, level = EXCHANGES[sorted_zone_keys].values()
    return raw_data[level][name] * flow


def fetch_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests the last known power exchange (in MW) between two regions."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    data = get_data(session)
    dt = datetime.fromisoformat(data["Data"])
    sorted_zone_keys = ZoneKey("->".join(sorted([zone_key1, zone_key2])))
    exchanges = ExchangeList(logger)

    net_flow = get_exchange_flow(sorted_zone_keys, data)
    exchanges.append(
        zoneKey=sorted_zone_keys,
        datetime=dt,
        source=SOURCE,
        netFlow=net_flow,
    )
    return exchanges.to_list()


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production(BR-NE) ->")
    print(fetch_production(ZoneKey("BR-NE")))

    print("fetch_production(BR-N) ->")
    print(fetch_production(ZoneKey("BR-N")))

    print("fetch_production(BR-CS) ->")
    print(fetch_production(ZoneKey("BR-CS")))

    print("fetch_production(BR-S) ->")
    print(fetch_production(ZoneKey("BR-S")))

    print("fetch_exchange(BR-S, UY) ->")
    print(fetch_exchange("BR-S", "UY"))

    print("fetch_exchange(BR-S, AR) ->")
    print(fetch_exchange("BR-S", "AR"))

    print("fetch_region_exchange(BR-CS->BR-S)")
    print(fetch_exchange("BR-CS", "BR-S"))

    print("fetch_region_exchange(BR-CS->BR-NE)")
    print(fetch_exchange("BR-CS", "BR-NE"))

    print("fetch_region_exchange(BR-CS->BR-N)")
    print(fetch_exchange("BR-CS", "BR-N"))

    print("fetch_region_exchange(BR-N->BR-NE)")
    print(fetch_exchange("BR-N", "BR-NE"))
