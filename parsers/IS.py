#!python3
import datetime
import logging

# The arrow library is used to handle datetimes
import arrow

# The request library is used to fetch content through HTTP
import requests

# please try to write PEP8 compliant code (use a linter). One of PEP8's
# requirement is to limit your line length to 79 characters.


def fetch_production(
    zone_key="IS",
    session=None,
    target_datetime: datetime.datetime = None,
    logger: logging.Logger = logging.getLogger(__name__),
) -> dict:
    """Requests the last known production mix (in MW) of a given country."""
    r = session or requests.session()
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

    return data


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())
