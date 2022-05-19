#!/usr/bin/env python3

"""Parse Guatemalan electricity data from the Administrador del Mercado
Mayorista (AMM) API.
"""

# Standard library imports
import collections
import logging

# Third-party library imports
import arrow
import requests

# Local library imports
from parsers.lib import validation

DEFAULT_ZONE_KEY = "GT"
PRODUCTION_THRESHOLD = 10  # MW
TIMEZONE = "America/Guatemala"
DOMAIN = "wl12.amm.org.gt"
URL = f"https://{DOMAIN}/GraficaPW/graficaCombustible"


def fetch_consumption(
    zone_key=DEFAULT_ZONE_KEY,
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
):
    """Fetch a list of hourly consumption data, in MW, for the day of the
    requested date-time.
    """
    date_time = arrow.get(target_datetime).to(TIMEZONE).floor("hour")
    results = [
        {
            "consumption": row["DEM SNI"],
            "datetime": date_time.replace(hour=hour).datetime,
            "source": DOMAIN,
            "zoneKey": zone_key,
        }
        for hour, row in enumerate(
            index_api_data_by_hour(get_api_data(session, URL, date_time))
        )
    ]
    # An hour's data isn't updated until the hour has passed, so the current
    # (and future) hour(s) is/are not included in the results.
    return results if target_datetime else results[: date_time.hour]


def fetch_production(
    zone_key=DEFAULT_ZONE_KEY,
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
):
    """Fetch a list of hourly production data, in MW, for the day of the
    requested date-time.
    """
    date_time = arrow.get(target_datetime).to(TIMEZONE).floor("hour")
    results = [
        {
            "datetime": date_time.replace(hour=hour).datetime,
            "production": {
                "biomass": row["BIOGAS"] + row["BIOMASA"],
                "coal": row["CARBÓN"],
                "gas": row["GAS NATURAL"],
                "geothermal": row["VAPOR"],
                "hydro": row["AGUA"],
                "oil": row["BUNKER"] + row["DIESEL"],
                "solar": row["IRRADIACIÓN"],
                "unknown": row["BIOMASA/CARBÓN"]
                + row["CARBÓN/PETCOKE"]
                + row["SYNGAN"],
                "wind": row["VIENTO"],
            },
            "source": DOMAIN,
            "zoneKey": zone_key,
        }
        for hour, row in enumerate(
            index_api_data_by_hour(get_api_data(session, URL, date_time))
        )
    ]
    # If the current day is selected, the API will return zero-filled future
    # data until the end of the day. Truncate the list to avoid returning any
    # future data.
    if not target_datetime:
        results = results[: date_time.hour + 1]
    return [
        validation.validate(
            result, logger, floor=PRODUCTION_THRESHOLD, remove_negative=True
        )
        for result in results
    ]


def index_api_data_by_hour(json):
    """The JSON data returned by the API is a list of objects, each
    representing one technology type. Collect this information into a list,
    with the list index representing the hour of day.
    """
    results = [collections.defaultdict(float) for _ in range(24)]
    for row in json:
        # The API returns hours in the range [1, 24], so each one refers to the
        # past hour (e.g., 1 is the time period [00:00, 01:00)). Shift the hour
        # so each index represents the hour ahead and is in the range [0, 24),
        # e.g., hour 0 represents the period [00:00, 01:00).
        results[int(row["hora"]) - 1][row["tipo"]] = row["potencia"]
    return results


def get_api_data(session, url, date_time):
    """Get the JSON-formatted response from the AMM API for the desired
    date-time.
    """
    session = session or requests.Session()
    return session.get(url, params={"dt": date_time.format("DD/MM/YYYY")}).json()


if __name__ == "__main__":
    # Never used by the electricityMap back-end, but handy for testing.
    print("fetch_production():")
    print(fetch_production(), end="\n\n")
    print("fetch_production(target_datetime='2022-01-01T:12:00:00Z'):")
    print(fetch_production(target_datetime="2022-01-01T12:00:00Z"), end="\n\n")
    print("fetch_consumption():")
    print(fetch_consumption(), end="\n\n")
    print("fetch_consumption(target_datetime='2022-01-01T:12:00:00Z'):")
    print(fetch_consumption(target_datetime="2022-01-01T12:00:00Z"), end="\n\n")
