#!/usr/bin/env python3
# The arrow library is used to handle datetimes
from datetime import datetime
from logging import Logger, getLogger
from typing import List, Optional

from pytz import timezone
from requests import Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    ProductionBreakdownList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey

PRODUCTION_MAPPING = {
    "wind": "wind_turbines",
    "biomass": "factory",
    "solar": "solar_cells",
}
LATEST_DATA_URL = "http://bornholm.powerlab.dk/visualizer/latestdata"

SOURCE = "bornholm.powerlab.dk"
TIMEZONE = timezone("Europe/Copenhagen")


def fetch_production(
    zone_key: ZoneKey = ZoneKey("DK-BHM"),
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> List[dict]:
    """Requests the last known production mix (in MW) of a given country."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")
    if session is None:
        session = Session()
    response = session.get(LATEST_DATA_URL).json()
    production = ProductionBreakdownList(logger)
    production.append(
        zoneKey=zone_key,
        datetime=datetime.fromtimestamp(response["latest"], tz=TIMEZONE),
        source=SOURCE,
        production=ProductionMix(
            biomass=response["sub"]["factory"],
            solar=response["sub"]["solar_cells"],
            wind=response["sub"]["wind_turbines"],
        ),
    )
    return production.to_list()


def fetch_exchange(
    zone_key1: ZoneKey = ZoneKey("DK-BHM"),
    zone_key2: ZoneKey = ZoneKey("SE-SE4"),
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> List[dict]:
    """Requests the last known power exchange (in MW) between two countries."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")
    if session is None:
        session = Session()
    response = session.get(LATEST_DATA_URL).json()
    exchange = ExchangeList(logger)
    sorted_zone_keys = sorted([zone_key1, zone_key2])
    flow = 1 if zone_key1 == sorted_zone_keys[0] else -1
    exchange.append(
        zoneKey=ZoneKey("->".join(sorted_zone_keys)),
        datetime=datetime.fromtimestamp(response["latest"], tz=TIMEZONE),
        source=SOURCE,
        netFlow=flow * response["sub"]["seacable"],
    )

    return exchange.to_list()


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())
    print("fetch_exchange(DK-BHM, SE-SE4) ->")
    print(fetch_exchange())
