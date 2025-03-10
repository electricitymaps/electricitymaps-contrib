#!/usr/bin/env python3
import json
import urllib.parse
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

import requests
from requests import Response, Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.lib.models.event_lists import (
    PriceList,
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException
from parsers.lib.validation import validate

from .lib.utils import get_token

TR_TZ = ZoneInfo("Europe/Istanbul")

EPIAS_MAIN_URL = "https://seffaflik.epias.com.tr/electricity-service/v1"
KINDS_MAPPING = {
    "production": {
        "url": "generation/data/realtime-generation",
    },
    "consumption": {
        "url": "consumption/data/realtime-consumption",
    },
    "price": {"url": "markets/dam/data/mcp"},
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
    "nuclear": ["nucklear"],
    "unknown": ["wasteheat"],
}
INVERT_PRODUCTION_MAPPPING = {
    val: mode for mode in PRODUCTION_MAPPING for val in PRODUCTION_MAPPING[mode]
}
IGNORED_KEYS = ["total", "date", "importExport", "hour"]
SOURCE = "epias.com.tr"


def fetch_ticket_TGT() -> str:
    url = "https://giris.epias.com.tr/cas/v1/tickets"

    TR_USERNAME = urllib.parse.quote_plus(get_token("TR_USERNAME"))
    TR_PASSWORD = urllib.parse.quote_plus(get_token("TR_PASSWORD"))

    payload = f"username={TR_USERNAME}&password={TR_PASSWORD}"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "text/plain",
    }

    response_TGT = requests.request("POST", url, headers=headers, data=payload)

    return response_TGT.text


def fetch_data(target_datetime: datetime, kind: str) -> dict:
    TGT_ticket = fetch_ticket_TGT()
    url = "/".join((EPIAS_MAIN_URL, KINDS_MAPPING[kind]["url"]))

    is_last_page = False
    pagenum = 1
    results = []

    target_datetime = target_datetime.replace(tzinfo=TR_TZ)

    while not is_last_page:
        payload = json.dumps(
            {
                "startDate": (target_datetime).strftime("%Y-%m-%dT%H:%M:%S+03:00"),
                "endDate": (target_datetime).strftime("%Y-%m-%dT%H:%M:%S+03:00"),
                "page": {
                    "number": pagenum,
                    "size": 24,
                    "sort": {"field": "date", "direction": "ASC"},
                },
            }
        )
        headers = {
            "TGT": TGT_ticket,
            "Content-Type": "application/json",
        }

        r: Response = requests.request("POST", url, headers=headers, data=payload)

        if r.status_code == 200:
            results += r.json()["items"]
            pagenum += 1

        else:
            raise ParserException(
                parser="TR.py",
                message=f"{target_datetime}: {kind} data is not available for TR",
            )

        if r.json()["items"] == [] or pagenum > 20:
            is_last_page = True

    return results


def validate_production_data(
    data: list,
    exclude_last_data_point: bool,
    logger: Logger = getLogger(__name__),
) -> list:
    """detects outliers: for real-time data the latest data point can be completely out of the expected range and needs to be excluded"""
    floor = (
        17000  # as seen during the Covid-19 pandemic, the minimum production was 17 GW
    )
    all_data_points_validated = [x for x in data if validate(x, logger, floor=floor)]
    if exclude_last_data_point:
        all_data_points_validated = all_data_points_validated[:-1]
    return all_data_points_validated


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: ZoneKey = ZoneKey("TR"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    # For real-time data, the last data point seems to but continously updated thoughout the hour and will be excluded as not final
    exclude_last_data_point = False
    if target_datetime is None:
        target_datetime = datetime.now(tz=TR_TZ)
        exclude_last_data_point = True

    data = fetch_data(target_datetime=target_datetime, kind="production")

    production_breakdowns = ProductionBreakdownList(logger)
    for item in data:
        mix = ProductionMix()
        for key, value in item.items():
            if key in INVERT_PRODUCTION_MAPPPING:
                mix.add_value(INVERT_PRODUCTION_MAPPPING[key], value)
            elif key not in IGNORED_KEYS:
                logger.warning("Unrecognized key '%s' in data skipped", key)

        production_breakdowns.append(
            zoneKey=zone_key,
            datetime=datetime.fromisoformat(item.get("date")).replace(tzinfo=TR_TZ),
            production=mix,
            source=SOURCE,
        )

    all_data_points_validated = validate_production_data(
        data=production_breakdowns.to_list(),
        exclude_last_data_point=exclude_last_data_point,
        logger=logger,
    )

    return all_data_points_validated


@refetch_frequency(timedelta(days=1))
def fetch_consumption(
    zone_key: ZoneKey = ZoneKey("TR"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    if target_datetime is None:
        target_datetime = datetime.now(tz=TR_TZ).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    data = fetch_data(target_datetime=target_datetime, kind="consumption")

    consumptions = TotalConsumptionList(logger)
    for item in data:
        consumptions.append(
            zoneKey=zone_key,
            datetime=datetime.fromisoformat(item.get("date")).replace(tzinfo=TR_TZ),
            consumption=item.get("consumption"),
            source=SOURCE,
        )

    return consumptions.to_list()


@refetch_frequency(timedelta(days=1))
def fetch_price(
    zone_key: ZoneKey = ZoneKey("TR"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    if target_datetime is None:
        target_datetime = datetime.now(tz=TR_TZ)

    data = fetch_data(target_datetime=target_datetime, kind="price")
    prices = PriceList(logger)
    for item in data:
        prices.append(
            zoneKey=zone_key,
            datetime=datetime.fromisoformat(item.get("date")).replace(tzinfo=TR_TZ),
            price=item.get("price"),
            source=SOURCE,
            currency="TRY",
        )

    return prices.to_list()


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())
    print("fetch_price() ->")
    print(fetch_price())
    print("fetch_consumption() ->")
    print(fetch_consumption())
