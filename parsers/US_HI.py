#!/usr/bin/env python3

import datetime
import logging

import arrow
import requests

BASE_URL = "https://www.islandpulse.org/api/mix?"

EARLIEST_PROD_DT = arrow.get(
    "2013/12/04 08:30", tzinfo="Pacific/Honolulu"
)  # this is the earliest datetime with recorded data


def get_historical_prod(r, request_dt):
    """Return the closest historical data (as a dictionary) for the requested datetime."""
    if request_dt < EARLIEST_PROD_DT.shift(hours=-2):
        return None

    # The API does not provide energy production data between 11:31pm and 11:59pm HST, so adjust date to query if needed
    if request_dt.hour == 23 and (31 <= request_dt.minute <= 59):
        query_url = BASE_URL + "date={}".format(
            request_dt.shift(days=+1).format("YYYY-MM-DD")
        )
    else:
        query_url = BASE_URL + "date={}".format(request_dt.format("YYYY-MM-DD"))
    res = r.get(query_url).json()

    # the first entry returned always has a UTC datetime, but any additional entries are in descending HST (local time)
    res[0]["dateTime"] = (
        arrow.get(res[0]["dateTime"]).to(tz="Pacific/Honolulu").datetime
    )

    raw_data = res[0]
    for entry in res:
        if arrow.get(entry["dateTime"], tzinfo="Pacific/Honolulu") >= request_dt:
            raw_data = entry
        else:
            break

    return raw_data


def validate_prod_timestamp(logger, energy_dt, request_dt):
    """Check that the energy production data was captured up to 2 hours after the requested datetime.
    Compares two Arrow objects in local HST time."""
    diff = energy_dt - request_dt
    if diff.total_seconds() > 7200:
        msg = (
            "Hawaii data is too old to use, " "parsed data timestamp was {0}."
        ).format(energy_dt)
        logger.warning(msg, extra={"key": "US-HI-OA"})
        return False

    return True


def fetch_production(
    zone_key="US-HI-OA",
    session=None,
    target_datetime: datetime.datetime = None,
    logger: logging.Logger = logging.getLogger(__name__),
) -> dict:
    """Requests the last known production mix (in MW) of a given country."""
    r = session or requests.session()
    if target_datetime is None:
        request_dt = arrow.now("Pacific/Honolulu")
        res = r.get(BASE_URL + "limit=1").json()
        raw_data = res[0]
        # the first entry returned by the API always has a UTC datetime, but any additional entries are in HST (local time)
        raw_data["dateTime"] = (
            arrow.get(raw_data["dateTime"]).to(tz="Pacific/Honolulu").datetime
        )
    else:
        request_dt = arrow.get(target_datetime).to(tz="Pacific/Honolulu")
        raw_data = get_historical_prod(r, request_dt)
        if raw_data is None:
            return None

    energy_dt = arrow.get(raw_data["dateTime"], tzinfo="Pacific/Honolulu")
    if validate_prod_timestamp(logger, energy_dt, request_dt) is False:
        return None

    production = {
        "biomass": float(raw_data["Waste2Energy"] + raw_data["BioFuel"]),
        "coal": float(raw_data["Coal"]),
        "oil": float(raw_data["Fossil_Fuel"]),
        "solar": float(raw_data["Solar"]),
        "wind": float(raw_data["WindFarm"]),
    }

    data = {
        "zoneKey": zone_key,
        "production": production,
        "datetime": energy_dt.datetime,
        "storage": {},
        "source": "islandpulse.org",
    }

    return data


if __name__ == "__main__":
    print("fetch_production ->")
    print(fetch_production())
