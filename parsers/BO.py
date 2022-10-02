#!/usr/bin/env python3

import json
import re
from datetime import datetime
from logging import Logger, getLogger
from typing import NamedTuple, Optional

import arrow
from requests import Session

tz_bo = "America/La_Paz"

SOURCE = "cndc.bo"


class HourlyProduction(NamedTuple):
    datetime: datetime
    forecast: Optional[float]
    total: Optional[float]
    thermo: Optional[float]
    hydro: Optional[float]
    wind: Optional[float]
    solar: Optional[float]
    bagasse: Optional[float]


def extract_xsrf_token(html):
    """Extracts XSRF token from the source code of the generation graph page."""
    return re.search(r'var ttoken = "([a-f0-9]+)";', html).group(1)


def fetch_data(
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list[HourlyProduction]:
    if target_datetime is not None:
        dt = arrow.get(target_datetime, tz_bo)
    else:
        dt = arrow.now(tz=tz_bo)
        print("current dt", dt)

    r = session or Session()

    # Define actual and previous day (for midnight data).
    formatted_dt = dt.format("YYYY-MM-DD")

    # initial path for url to request
    url_init = "https://www.cndc.bo/gene/dat/gene.php?fechag={0}"

    # XSRF token for the initial request
    xsrf_token = extract_xsrf_token(r.get("https://www.cndc.bo/gene/index.php").text)

    resp = r.get(url_init.format(formatted_dt), headers={"x-csrf-token": xsrf_token})

    hour_rows = json.loads(resp.text.replace("ï»¿", ""))["data"]

    result: list[HourlyProduction] = []

    for hour_row in hour_rows:
        [hour, forecast, total, thermo, hydro, wind, solar, bagasse] = hour_row

        # isn't this Bolivia time and not UTC?

        timestamp = dt.replace(
            # "hour" is one-indexed
            hour=hour - 1,
            minute=0,
            second=0,
            microsecond=0,
        )

        result.append(
            HourlyProduction(
                datetime=timestamp.datetime,
                forecast=forecast,
                total=total,
                thermo=thermo,
                hydro=hydro,
                wind=wind,
                solar=solar,
                bagasse=bagasse,
            )
        )

    return result


def fetch_production(
    zone_key: str = "BO",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Requests the last known production mix (in MW) of a given country."""
    payload = []

    for row in fetch_data(
        session=session, target_datetime=target_datetime, logger=logger
    ):
        # NOTE: thermo includes gas + oil mixed, so we set these as unknown for now
        # The modes here should match the ones we extract in the production payload
        modes_extracted = [row.hydro, row.solar, row.wind, row.bagasse]

        if row.total is None or None in modes_extracted:
            continue

        payload.append(
            {
                "zoneKey": zone_key,
                "datetime": row.datetime,
                "production": {
                    "biomass": row.bagasse,
                    "hydro": row.hydro,
                    "solar": row.solar,
                    "unknown": row.total - sum(modes_extracted),
                    "wind": row.wind,
                },
                "storage": {},
                "source": SOURCE,
            }
        )

    return payload


def fetch_generation_forecast(
    zone_key: str = "BO",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    return [
        {
            "zoneKey": zone_key,
            "datetime": row.datetime,
            "value": row.forecast,
            "source": SOURCE,
        }
        for row in fetch_data(
            session=session, target_datetime=target_datetime, logger=logger
        )
    ]


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""
    print("fetch_production() ->")
    print(fetch_production())

    print("fetch_generation_forecast() ->")
    print(fetch_generation_forecast())
