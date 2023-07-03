from collections import defaultdict
from datetime import datetime
from logging import Logger, getLogger
from typing import Any, Dict, List, Optional, Tuple, Union

import arrow
from requests import Session

from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
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

REGION_EXCHANGES = {
    "BR-CS->BR-S": "sul_sudeste",
    "BR-CS->BR-NE": "sudeste_nordeste",
    "BR-CS->BR-N": "sudeste_norteFic",
    "BR-N->BR-NE": "norteFic_nordeste",
}

REGION_EXCHANGES_DIRECTIONS = {
    "BR-CS->BR-S": -1,
    "BR-CS->BR-NE": 1,
    "BR-CS->BR-N": 1,
    "BR-N->BR-NE": 1,
}

COUNTRIES_EXCHANGE = {
    "UY": {"name": "uruguai", "flow": 1},
    "AR": {"name": "argentina", "flow": -1},
    "PY": {"name": "paraguai", "flow": -1},
}


def get_data(session: Optional[Session]):
    """Requests generation data in json format."""
    s = session or Session()
    json_data = s.get(URL).json()

    return json_data


def production_processor(
    json_data: dict, zone_key: str
) -> Tuple[datetime, ProductionMix]:
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
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> List[Dict[str, Any]]:
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


def fetch_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """Requests the last known power exchange (in MW) between two regions."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    data = get_data(session)
    dt = arrow.get(data["Data"]).datetime
    sorted_zone_keys = "->".join(sorted([zone_key1, zone_key2]))

    country_exchange = COUNTRIES_EXCHANGE.get(zone_key1) or COUNTRIES_EXCHANGE.get(
        zone_key2
    )
    net_flow: Union[float, None] = None
    if country_exchange:
        net_flow = (
            data["internacional"][country_exchange["name"]] * country_exchange["flow"]
        )

    return {
        "datetime": dt,
        "sortedZoneKeys": sorted_zone_keys,
        "netFlow": net_flow,
        "source": SOURCE,
    }


def fetch_region_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """Requests the last known power exchange (in MW) between two Brazilian regions."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    data = get_data(session)
    dt = arrow.get(data["Data"]).datetime
    sorted_regions = "->".join(sorted([zone_key1, zone_key2]))

    exchange = REGION_EXCHANGES[sorted_regions]
    net_flow = (
        data["intercambio"][exchange] * REGION_EXCHANGES_DIRECTIONS[sorted_regions]
    )

    return {
        "datetime": dt,
        "sortedZoneKeys": sorted_regions,
        "netFlow": net_flow,
        "source": SOURCE,
    }


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
    print(fetch_region_exchange("BR-CS", "BR-S"))

    print("fetch_region_exchange(BR-CS->BR-NE)")
    print(fetch_region_exchange("BR-CS", "BR-NE"))

    print("fetch_region_exchange(BR-CS->BR-N)")
    print(fetch_region_exchange("BR-CS", "BR-N"))

    print("fetch_region_exchange(BR-N->BR-NE)")
    print(fetch_region_exchange("BR-N", "BR-NE"))
