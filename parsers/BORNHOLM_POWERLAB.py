#!/usr/bin/env python3
# The arrow library is used to handle datetimes
from datetime import datetime
from logging import Logger, getLogger
from typing import List, Optional

import arrow
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


def _fetch_data(session: Session):
    response = session.get(LATEST_DATA_URL)
    obj = response.json()
    return obj


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
    zone_key1: str = "DK-BHM",
    zone_key2: str = "SE-SE4",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """Requests the last known power exchange (in MW) between two countries."""

    obj = _fetch_data(session)

    data = {
        "sortedZoneKeys": "->".join(sorted([zone_key1, zone_key2])),
        "source": "bornholm.powerlab.dk",
        "datetime": arrow.get(obj["latest"]).datetime,
    }

    # Country codes are sorted in order to enable easier indexing in the database
    sorted_zone_keys = sorted([zone_key1, zone_key2])
    # Here we assume that the net flow returned by the api is the flow from
    # country1 to country2. A positive flow indicates an export from country1
    # to country2. A negative flow indicates an import.
    netFlow = obj["sub"]["seacable"]  # Export is positive
    # The net flow to be reported should be from the first country to the second
    # (sorted alphabetically). This is NOT necessarily the same direction as the flow
    # from country1 to country2
    data["netFlow"] = netFlow if zone_key1 == sorted_zone_keys[0] else -1 * netFlow

    return data


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())
    print("fetch_exchange(DK-BHM, SE-SE4) ->")
    print(fetch_exchange("DK-BHM", "SE-SE4"))
