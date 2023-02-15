#!/usr/bin/env python3

from datetime import datetime
from logging import Logger, getLogger
from typing import Optional

# The arrow library is used to handle datetimes consistently with other parsers
import arrow
from requests import Session

TIMEZONE = "America/Regina"
# Source: https://www.saskpower.com/Our-Power-Future/Our-Electricity/Electrical-System/System-Map
URL = "https://www.saskpower.com/ignitionapi/Content/GetNetLoad"


def fetch_consumption(
    zone_key: str = "CA-SK",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """Requests the last known consumption data (in MW) of the CA-SK zone."""

    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    requests_obj = session or Session()
    load_data = requests_obj.get(URL).json()
    consumption = int(load_data)
    if consumption < 0 or consumption > 5500:
        raise ValueError("Consumption value is not valid")

    data = {
        "datetime": arrow.utcnow().datetime,
        "zoneKey": zone_key,
        "consumption": consumption,
        "source": "saskpower.com",
    }

    return data


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_consumption() ->")
    print(fetch_consumption())
