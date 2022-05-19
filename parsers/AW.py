#!/usr/bin/env python3

import datetime

import arrow
import requests


def fetch_production(zone_key="AW", session=None, target_datetime=None, logger=None):
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    r = session or requests.session()
    url = "https://www.webaruba.com/renewable-energy-dashboard/app/rest/results.json"
    # User agent is mandatory or services answers 404
    headers = {"user-agent": "electricitymap.org"}
    response = r.get(url, headers=headers)
    aruba_json = response.json()
    top_data = aruba_json["dashboard_top_data"]

    # Values currenlty used from service
    fossil = top_data["Fossil"]
    wind = top_data["Wind"]
    solar = top_data["TotalSolar"]
    # biogas live value is 0 MW all the time (2021)
    biogas = top_data["total_bio_gas"]
    total = top_data["TotalPower"]
    # "unknown" is when data reported in the categories above is less than total reported.
    # If categories sum up to more than total, accept the datapoint, but only if it's less than 2% of total.
    # This helps avoid missing data when it's a little bit off, due to rounding or reporting
    reported_total = float(total["value"])
    sources_total = (
        float(fossil["value"])
        + float(wind["value"])
        + float(solar["value"])
        + float(biogas["value"])
    )

    if (sources_total / reported_total) > 1.1:
        raise RuntimeError(
            f"AW parser reports fuel sources add up to {sources_total} but total generation {reported_total} is lower"
        )

    missing_from_total = reported_total - sources_total
    unknown = missing_from_total if missing_from_total > 0 else 0
    # We're using Fossil data to get timestamp in correct time zone
    local_date_time = datetime.datetime.strptime(
        fossil["timestamp"], "%Y-%m-%d %H:%M:%S.%f"
    )
    zone_date_time = arrow.Arrow.fromdatetime(local_date_time, "America/Aruba")

    data = {
        "zoneKey": zone_key,
        "datetime": zone_date_time.datetime,
        "production": {
            "oil": float(fossil["value"]),
            "wind": float(wind["value"]),
            "solar": float(solar["value"]),
            "biomass": float(biogas["value"]),
            "unknown": unknown,
        },
        "storage": {},
        "source": "webaruba.com",
    }

    return data


if __name__ == "__main__":
    print(fetch_production())
