#!/usr/bin/env python3

"""Parser for the electricity grid of Nigeria"""

import arrow
import logging
import requests
import json


LIVE_PRODUCTION_API_URL = "https://cebcare.ceb.lk/GenSum/GetLoadCurveData"


def template_response(zone_key, datetime, source) -> dict:
    return {
        "zoneKey": zone_key,
        "datetime": datetime,
        "production": {
            "biomass": 0.0,
            "coal": 0.0,
            "gas": 0.0,
            "hydro": 0.0,
            "oil": 0.0,
            "solar": 0.0,
            "wind": 0.0,
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
    resp = r.get(LIVE_PRODUCTION_API_URL)

    readings = json.loads(resp.content.decode('unicode_escape').strip("\""))

    last = readings[-1]

    datetime = arrow.get(last["DateTime"]).replace(tzinfo="Asia/Colombo").datetime
    result = template_response(zone_key, datetime, "cebcare.ceb.lk")

    result["production"]["biomass"] += float(last["SPP Biomass"])
    result["production"]["coal"] += float(last["Coal"])
    result["production"]["hydro"] += float(last["Major Hydro"]) + float(last["SPP Minihydro"])
    result["production"]["solar"] += float(last["Solar"])
    result["production"]["oil"] += float(last["Thermal-Oil"])
    result["production"]["wind"] += float(last["Wind"])

    return [result]


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""
    print(fetch_production())
