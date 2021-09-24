#!/usr/bin/env python3

"""Parser for the electricity grid of Nigeria"""

import arrow
import logging
import requests


LIVE_PRODUCTION_API_URL = "https://www.sothailand.com/sysgen/ws/sysgen/actual"


def template_response(zone_key, datetime, source) -> dict:
    return {
        "zoneKey": zone_key,
        "datetime": datetime,
        "production": {
            "unknown": 0.0,
        },
        "storage": {},
        "source": source,
    }


def fetch_production(
    zone_key=None,
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
) -> list:
    """Requests the last known production mix (in MW) of a given zone."""

    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    r = session or requests.session()
    resp = r.post(LIVE_PRODUCTION_API_URL, {
        "name": "SYSTEM_GEN(MW)",
        "day": arrow.now().replace(tzinfo="Asia/Bangkok").format("DD-MM-YYYY"),
        "timestart": "0"
    }).json()


    last = resp["list"][-1]

    datetime = arrow.get(resp["day"], "DD-MM-YYYY").shift(seconds=last[0]).replace(tzinfo="Asia/Bangkok").datetime
    result = template_response(zone_key, datetime, "www.sothailand.com")
    result["production"]["unknown"] += float(last[1])

    return [result]


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""
    print(fetch_production())
