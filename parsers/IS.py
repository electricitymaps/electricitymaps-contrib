#!python3
from datetime import datetime
from logging import Logger, getLogger

# The arrow library is used to handle datetimes
import arrow

from requests import Session

from parsers.lib.validation import validate


def fetch_production(
    zone_key: str = "IS",
    session: Session | None = None,
    target_datetime: datetime | None = None,
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
        f"{zone_key}: error when calling url={url}"
    )

    obj = res.json()
    data = {
        "zoneKey": zone_key,
        "production": {},
        "storage": {},
        "source": "amper.landsnet.is",
    }

    for resource in ["hydro", "geothermal", "oil"]:
        data["production"][resource] = obj[resource]

    data["datetime"] = arrow.get(obj["timestamp"]).datetime
    validated_data = validate(datapoint=data, fake_zeros=True, logger=logger)
    return validated_data


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())
