#!/usr/bin/env python3
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Optional

import arrow
import pytz
from requests import Response, Session

from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException
from parsers.lib.validation import validate

TR_TZ = pytz.timezone("Europe/Istanbul")

EPIAS_MAIN_URL = "https://seffaflik.epias.com.tr/transparency/service"
KINDS_MAPPING = {
    "production": {
        "url": "production/real-time-generation",
        "json_key": "hourlyGenerations",
    },
    "consumption": {
        "url": "consumption/real-time-consumption",
        "json_key": "hourlyConsumptions",
    },
    "price": {"url": "market/day-ahead-mcp", "json_key": "dayAheadMCPList"},
}
PRODUCTION_MAPPING = {
    "biomass": ["biomass"],
    "solar": ["sun"],
    "geothermal": ["geothermal"],
    "oil": ["fueloil", "gasOil", "naphta"],
    "gas": ["naturalGas", "lng"],
    "wind": ["wind"],
    "coal": ["blackCoal", "asphaltiteCoal", "lignite", "importCoal"],
    "hydro": ["river", "dammedHydro"],
}


def fetch_data(session: Session, target_datetime: datetime, kind: str) -> dict:
    url = "/".join((EPIAS_MAIN_URL, KINDS_MAPPING[kind]["url"]))
    params = {
        "startDate": (target_datetime).strftime("%Y-%m-%d"),
        "endDate": (target_datetime + timedelta(days=1)).strftime("%Y-%m-%d"),
    }
    r: Response = session.get(url=url, params=params)
    if r.status_code == 200:
        return r.json()["body"][KINDS_MAPPING[kind]["json_key"]]
    else:
        raise ParserException(
            parser="TR.py",
            message=f"{target_datetime}: {kind} data is not available for TR",
        )


def validate_production_data(
    data: list,
    exclude_last_data_point: bool,
    logger: Logger = getLogger(__name__),
) -> list:
    """detects outliers: for real-time data the latest data point can be completely out of the expected range and needs to be excluded"""
    required = [mode for mode in PRODUCTION_MAPPING]
    floor = (
        17000  # as seen during the Covid-19 pandemic, the minimum production was 17 GW
    )
    all_data_points_validated = [
        x for x in data if validate(x, logger, required=required, floor=floor)
    ]
    if exclude_last_data_point:
        all_data_points_validated = all_data_points_validated[:-1]
    return all_data_points_validated


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: str = "TR",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    # For real-time data, the last data point seems to but continously updated thoughout the hour and will be excluded as not final
    exclude_last_data_point = False
    if target_datetime is None:
        target_datetime = datetime.now(tz=TR_TZ)
        exclude_last_data_point = True

    data = fetch_data(
        session=session, target_datetime=target_datetime, kind="production"
    )

    all_data_points = []
    for item in data:
        production = {}
        for mode in PRODUCTION_MAPPING:
            value = sum([item[key] for key in item if key in PRODUCTION_MAPPING[mode]])
            production[mode] = round(value, 4)
        data_point = {
            "zoneKey": zone_key,
            "datetime": arrow.get(item.get("date")).datetime.replace(tzinfo=TR_TZ),
            "production": production,
            "source": "epias.com.tr",
        }

        all_data_points += [data_point]

    all_data_points_validated = validate_production_data(
        data=all_data_points,
        exclude_last_data_point=exclude_last_data_point,
        logger=logger,
    )

    return all_data_points_validated


@refetch_frequency(timedelta(days=1))
def fetch_consumption(
    zone_key: str = "TR",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    if target_datetime is None:
        target_datetime = datetime.now(tz=TR_TZ) - timedelta(hours=2)

    data = fetch_data(
        session=session, target_datetime=target_datetime, kind="consumption"
    )

    all_data_points = []
    for item in data:
        data_point = {
            "zoneKey": zone_key,
            "datetime": arrow.get(item.get("date")).datetime.replace(tzinfo=TR_TZ),
            "consumption": item.get("consumption"),
            "source": "epias.com.tr",
        }

        all_data_points += [data_point]
    return all_data_points


@refetch_frequency(timedelta(days=1))
def fetch_price(
    zone_key: str = "TR",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    if target_datetime is None:
        target_datetime = datetime.now(tz=TR_TZ)

    data = fetch_data(session=session, target_datetime=target_datetime, kind="price")
    all_data_points = []
    for item in data:
        data_point = {
            "zoneKey": zone_key,
            "datetime": arrow.get(item.get("date")).datetime.replace(tzinfo=TR_TZ),
            "price": item.get("price"),
            "source": "epias.com.tr",
            "currency": "TRY",
        }

        all_data_points += [data_point]
    return all_data_points


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())
    print("fetch_price() ->")
    print(fetch_price())
    print("fetch_consumption() ->")
    print(fetch_consumption())
