#!/usr/bin/env python3

# The arrow library is used to handle datetimes
import json
import re

import arrow
import requests

tz_bo = "America/La_Paz"

SOURCE = "cndc.bo"


def extract_xsrf_token(html):
    """Extracts XSRF token from the source code of the generation graph page."""
    return re.search(r'var ttoken = "([a-f0-9]+)";', html).group(1)


def fetch_production(
    zone_key="BO", session=None, target_datetime=None, logger=None
) -> dict:
    """Requests the last known production mix (in MW) of a given country."""
    if target_datetime is not None:
        now = arrow.get(target_datetime)
    else:
        now = arrow.now(tz=tz_bo)

    r = session or requests.session()

    # Define actual and previous day (for midnight data).
    formatted_date = now.format("YYYY-MM-DD")

    # initial path for url to request
    url_init = "https://www.cndc.bo/gene/dat/gene.php?fechag={0}"

    # XSRF token for the initial request
    xsrf_token = extract_xsrf_token(r.get("https://www.cndc.bo/gene/index.php").text)

    resp = r.get(url_init.format(formatted_date), headers={"x-csrf-token": xsrf_token})

    hour_rows = json.loads(resp.text.replace("ï»¿", ""))["data"]
    payload = []

    for hour_row in hour_rows:
        [hour, _forecast, total, thermo, hydro, wind, solar, _bagasse] = hour_row

        if target_datetime is None and hour > now.hour:
            continue

        if hour == 24:
            timestamp = now.shift(days=1)
        else:
            timestamp = now

        if target_datetime is not None and hour < 24:
            timestamp = timestamp.replace(hour=hour - 1)

        # NOTE: that thermo includes gas + oil are mixed, so this is unknown for now
        modes_extracted = [hydro, solar, wind]

        if total is None or None in modes_extracted:
            continue

        hour_resp = {
            "zoneKey": zone_key,
            "datetime": timestamp.datetime,
            "production": {
                "hydro": hydro,
                "solar": solar,
                "unknown": total - sum(modes_extracted),
                "wind": wind,
            },
            "storage": {},
            "source": SOURCE,
        }

        payload.append(hour_resp)

    return payload


def fetch_generation_forecast(
    zone_key="BO", session=None, target_datetime=None, logger=None
):
    if target_datetime is not None:
        now = arrow.get(target_datetime)
    else:
        now = arrow.now(tz=tz_bo)

    r = session or requests.session()

    # Define actual and previous day (for midnight data).
    formatted_date = now.format("YYYY-MM-DD")

    # initial path for url to request
    url_init = "https://www.cndc.bo/gene/dat/gene.php?fechag={0}"

    # XSRF token for the initial request
    xsrf_token = extract_xsrf_token(r.get("https://www.cndc.bo/gene/index.php").text)

    resp = r.get(url_init.format(formatted_date), headers={"x-csrf-token": xsrf_token})

    hour_rows = json.loads(resp.text.replace("ï»¿", ""))["data"]
    payload = []

    for hour_row in hour_rows:
        [hour, forecast, *_rest] = hour_row

        if hour == 24:
            timestamp = now.shift(days=1)
        else:
            timestamp = now

        zeroed = timestamp.replace(hour=hour - 1, minute=0, second=0, microsecond=0)

        hour_resp = {
            "zoneKey": zone_key,
            "datetime": zeroed.datetime,
            "value": forecast,
            "source": SOURCE,
        }

        payload.append(hour_resp)

    return payload


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""
    print("fetch_production() ->")
    print(fetch_production())

    print("fetch_generation_forecast() ->")
    print(fetch_generation_forecast())
