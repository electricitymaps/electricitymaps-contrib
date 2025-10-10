#!/usr/bin/env python3

import json
import re
from datetime import datetime
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

from requests import Session

from electricitymap.contrib.lib.models.event_lists import (
    EventSourceType,
    ProductionBreakdownList,
    ProductionMix,
    TotalProductionList,
)
from electricitymap.contrib.lib.types import ZoneKey

tz_bo = ZoneInfo("America/La_Paz")

INDEX_URL = "https://www.cndc.bo/gene/index.php"
DATA_URL = "https://www.cndc.bo/gene/dat/gene.php?fechag={0}"
SOURCE = "cndc.bo"


def extract_xsrf_token(html):
    """Extracts XSRF token from the source code of the generation graph page."""
    return re.search(r'var ttoken = "([a-f0-9]+)";', html).group(1)


def get_datetime(query_date: datetime, hour: int) -> datetime:
    return datetime(
        year=query_date.year,
        month=query_date.month,
        day=query_date.day,
        hour=hour,
        tzinfo=tz_bo,
    )


def fetch_data(
    session: Session | None = None, target_datetime: datetime | None = None
) -> tuple[list[dict], datetime]:
    if session is None:
        session = Session()

    if target_datetime is None:
        target_datetime = datetime.now()
    target_datetime = target_datetime.astimezone(tz_bo)
    # Define actual and previous day (for midnight data).
    formatted_dt = target_datetime.strftime("%Y-%m-%d")

    # XSRF token for the initial request
    xsrf_token = extract_xsrf_token(session.get(INDEX_URL).text)

    resp = session.get(
        DATA_URL.format(formatted_dt), headers={"x-csrf-token": xsrf_token}
    )

    hour_rows = json.loads(resp.text.replace("ï»¿", ""))["data"]
    return hour_rows, target_datetime


def parse_generation_forecast(
    zone_key: ZoneKey, date: datetime, raw_data: list[dict], logger: Logger
) -> TotalProductionList:
    result = TotalProductionList(logger)
    assert date.tzinfo == tz_bo
    for hour_row in raw_data:
        [hour, forecast, total, thermo, hydro, wind, solar, bagasse] = hour_row

        # "hour" is one-indexed
        timestamp = get_datetime(query_date=date, hour=hour - 1)

        result.append(
            zoneKey=zone_key,
            datetime=timestamp,
            value=forecast,
            source=SOURCE,
            sourceType=EventSourceType.forecasted,
        )

    return result


def parser_production_breakdown(
    zone_key: ZoneKey, date: datetime, raw_data: list[dict], logger: Logger
) -> ProductionBreakdownList:
    result = ProductionBreakdownList(logger)
    assert date.tzinfo == tz_bo
    for hour_row in raw_data:
        [hour, forecast, total, thermo, hydro, wind, solar, bagasse] = hour_row

        # "hour" is one-indexed
        timestamp = get_datetime(query_date=date, hour=hour - 1)
        modes_extracted = [hydro, solar, wind, bagasse]

        if total is None or None in modes_extracted:
            continue

        result.append(
            zoneKey=zone_key,
            datetime=timestamp,
            production=ProductionMix(
                hydro=hydro,
                solar=solar,
                wind=wind,
                biomass=bagasse,
                # NOTE: thermo includes gas + oil mixed, so we set these as unknown for now
                # The modes here should match the ones we extract in the production payload
                unknown=total - (hydro + solar + wind + bagasse),
            ),
            source=SOURCE,
        )

    return result


def fetch_production(
    zone_key: ZoneKey = ZoneKey("BO"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Requests the last known production mix (in MW) of a given country."""
    production = ProductionBreakdownList(logger)
    raw_data, query_date = fetch_data(session=session, target_datetime=target_datetime)
    production = parser_production_breakdown(zone_key, query_date, raw_data, logger)

    return production.to_list()


def fetch_generation_forecast(
    zone_key: ZoneKey = ZoneKey("BO"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    raw_data, query_date = fetch_data(session=session, target_datetime=target_datetime)
    generation_forecast = parse_generation_forecast(
        zone_key, query_date, raw_data, logger
    )
    return generation_forecast.to_list()


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""
    print("fetch_production() ->")
    print(fetch_production())

    print("fetch_generation_forecast() ->")
    print(fetch_generation_forecast())
