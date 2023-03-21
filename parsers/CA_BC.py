#!/usr/bin/env python3

# The arrow library is used to handle datetimes
from datetime import datetime
from logging import Logger, getLogger
from typing import Optional

import arrow
from requests import Session

# More info:
# https://www.bchydro.com/energy-in-bc/our_system/transmission/transmission-system/actual-flow-data.html

TIMEZONE = "Canada/Pacific"

EXCHANGE_REGIONS = {
    "CA-AB": "Alberta",
    "CA-BC": "British Columbia",
    "US-NW-BPAT": "Bonneville",
    "US-BPA": "Bonneville",
}


def fetch_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """Requests the last known power exchange (in MW) between two countries."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    r = session or Session()
    url = "localhost:8000/province/BC"
    data = r.get(f"{url}/exchange").json()
    flow = data["flow"]

    sorted_zone_keys = "->".join(sorted((zone_key1, zone_key2)))
    if EXCHANGE_REGIONS[zone_key2] not in flow:
        raise NotImplementedError(f"Pair '{sorted_zone_keys}' not implemented")

    return {
        "datetime": get_current_timestamp(),
        "sortedZoneKeys": sorted_zone_keys,
        "netFlow": float(flow[EXCHANGE_REGIONS[zone_key2]]),
        "source": data["source"],
    }

def get_current_timestamp():
    return arrow.to(TIMEZONE).datetime


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_exchange(CA-BC, US-BPA) ->")
    print(fetch_exchange("CA-BC", "US-BPA"))
    print("fetch_exchange(CA-AB, CA-BC) ->")
    print(fetch_exchange("CA-AB", "CA-BC"))
