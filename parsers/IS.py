#!python3
from datetime import datetime
from logging import Logger, getLogger
from typing import Optional

# The arrow library is used to handle datetimes
import arrow

# The request library is used to fetch content through HTTP
from requests import Session

from parsers.lib.validation import validate

# please try to write PEP8 compliant code (use a linter). One of PEP8's
# requirement is to limit your line length to 79 characters.


def fetch_production(
    zone_key: str = "IS",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """Requests the last known production mix (in MW) of a given country."""
    r = session or Session()
    if target_datetime is None:
        url = "https://amper.landsnet.is/generation/api/Values"
    else:
        # WHEN HISTORICAL DATA IS NOT AVAILABLE
        raise NotImplementedError("This parser is not yet able to parse past dates")

    res = r.get(url)
    assert res.status_code == 200, (
        "Exception when fetching production for "
        "{}: error when calling url={}".format(zone_key, url)
    )

    obj = res.json()
    data = {
        "zoneKey": zone_key,
        "production": {},
        "storage": {},
        "source": "amper.landsnet.is",
    }

    # Parse the individual generation resources
    for resource in ["hydro", "geothermal", "oil"]:
        data["production"][resource] = obj[resource]

    # Parse the datetime and return a python datetime object
    data["datetime"] = arrow.get(obj["timestamp"]).datetime
    validated_data = validate(datapoint=data, fake_zeros=True, logger=logger)
    return validated_data


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())
