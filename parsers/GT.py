#!/usr/bin/env python3

"""Parse Guatemalan electricity data from the Administrador del Mercado
Mayorista (AMM) API.
"""

import collections
from datetime import datetime, time, timedelta
from logging import Logger, getLogger
from typing import Literal
from zoneinfo import ZoneInfo

from requests import Session

from parsers.lib import validation

DEFAULT_ZONE_KEY = "GT"
TIMEZONE = ZoneInfo("America/Guatemala")

PRODUCTION_THRESHOLD = 10  # MW

DOMAIN = "wl12.amm.org.gt"
URL = f"https://{DOMAIN}/GraficaPW/graficaCombustible"


def fetch_consumption(
    zone_key: str = DEFAULT_ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
):
    """Fetch a list of hourly consumption data, in MW, for the day of the
    requested date-time.
    """

    target_datetime = (
        datetime.now(TIMEZONE)
        if target_datetime is None
        else target_datetime.astimezone(TIMEZONE)
    )

    api_data = _get_api_data(session, URL, target_datetime, target="consumption")

    day_datetime = datetime.combine(
        target_datetime, time(), tzinfo=TIMEZONE
    )  # truncate to day
    results = [
        {
            "consumption": row["DEM SNI"],
            "datetime": day_datetime + timedelta(hours=hour),
            "source": DOMAIN,
            "zoneKey": zone_key,
        }
        for hour, row in enumerate(api_data)
    ]
    return results


def fetch_production(
    zone_key: str = DEFAULT_ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
):
    """Fetch a list of hourly production data, in MW, for the day of the
    requested date-time.
    """

    target_datetime = (
        datetime.now(TIMEZONE)
        if target_datetime is None
        else target_datetime.astimezone(TIMEZONE)
    )

    api_data = _get_api_data(session, URL, target_datetime, target="production")

    day_datetime = datetime.combine(  # truncate to day
        target_datetime, time(), tzinfo=TIMEZONE
    )
    results = [
        {
            "datetime": day_datetime + timedelta(hours=hour),
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
        for hour, row in enumerate(api_data)
    ]
    return [
        validation.validate(
            result, logger, floor=PRODUCTION_THRESHOLD, remove_negative=True
        )
        for result in results
    ]


def _get_api_data(
    session: Session,
    url: str,
    date_time: datetime,
    target: Literal["consumption", "production"],
) -> list[dict]:
    """Get the JSON-formatted response from the AMM API for the desired date-time."""
    session = session or Session()
    response_payload = session.get(
        url, params={"dt": date_time.strftime("%d/%m/%Y")}
    ).json()

    # The JSON data returned by the API is a list of objects, each
    # representing one technology type. Collect this information into a list,
    # with the list index representing the hour of day.
    results = [collections.defaultdict(float) for _ in range(24)]
    for row in response_payload:
        # The API returns hours in the range [1, 24], so each one refers to the
        # past hour (e.g., 1 is the time period [00:00, 01:00)). Shift the hour
        # so each index represents the hour ahead and is in the range [0, 24),
        # e.g., hour 0 represents the period [00:00, 01:00).
        results[int(row["hora"]) - 1][row["tipo"]] = row["potencia"]

    is_historical_data = date_time.date() < datetime.now(TIMEZONE).date()

    # For live consumption data, an hour's data isn't updated until the hour has passed,
    # so the current (and future) hour(s) should not be included in the results.
    # For live production data, the API will return zero-filled future data until the end of the day,
    # so future hours should not be included in the results.
    cutoff_index = date_time.hour if target == "consumption" else date_time.hour + 1

    return results if is_historical_data else results[:cutoff_index]


if __name__ == "__main__":
    # Never used by the electricityMap back-end, but handy for testing.

    target_datetime = datetime.fromisoformat("2022-01-01T12:00:00+00:00")

    print("fetch_production():")
    print(fetch_production(), end="\n\n")
    print(f"fetch_production(target_datetime={target_datetime.isoformat()!r}):")
    print(fetch_production(target_datetime=target_datetime), end="\n\n")

    print("fetch_consumption():")
    print(fetch_consumption(), end="\n\n")
    print(f"fetch_consumption(target_datetime={target_datetime.isoformat()!r}):")
    print(fetch_consumption(target_datetime=target_datetime), end="\n\n")
