#!/usr/bin/env python3

import json
import re
from datetime import datetime
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

from requests import Session

from electricitymap.contrib.config import CONFIG_DIR
from electricitymap.contrib.config.reading import read_zones_config
from electricitymap.contrib.lib.models.event_lists import (
    EventSourceType,
    ProductionBreakdownList,
    ProductionMix,
    TotalProductionList,
)
from electricitymap.contrib.lib.types import ZoneKey
from electricitymap.contrib.parsers.lib.config import use_proxy
from electricitymap.contrib.parsers.lib.exceptions import ParserException

tz_bo = ZoneInfo("America/La_Paz")

ZONES_CONFIG = read_zones_config(config_dir=CONFIG_DIR)
gas_oil_ratio = ZONES_CONFIG["BO"]["capacity"]["gas"][-1]["value"] / (
    ZONES_CONFIG["BO"]["capacity"]["gas"][-1]["value"]
    + ZONES_CONFIG["BO"]["capacity"]["oil"][-1]["value"]
)
INDEX_URL = "https://www.cndc.bo/gene/index.php"
DATA_URL = "https://www.cndc.bo/gene/dat/gene.php?fechag={0}"
SOURCE = "cndc.bo"
# User-Agent to avoid being blocked as a bot
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
REQUEST_TIMEOUT = 30  # seconds


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


def _check_response(response, context: str = ""):
    """Check HTTP response and raise appropriate ParserException if needed."""
    if response.status_code == 403:
        raise ParserException(
            "CNDC.py",
            f"Access forbidden (403){context}. The server may be blocking requests.",
            "BO",
        )
    elif response.status_code == 429:
        raise ParserException("CNDC.py", f"Rate limit exceeded (429){context}.", "BO")
    elif response.status_code >= 500:
        raise ParserException(
            "CNDC.py",
            f"Server error ({response.status_code}){context}. The CNDC server may be down.",
            "BO",
        )
    elif not response.ok:
        raise ParserException("CNDC.py", f"HTTP {response.status_code}{context}", "BO")


def fetch_data(
    session: Session | None = None, target_datetime: datetime | None = None
) -> tuple[list[dict], datetime]:
    session = session or Session()
    target_datetime = (target_datetime or datetime.now()).astimezone(tz_bo)
    formatted_dt = target_datetime.strftime("%Y-%m-%d")

    # Headers to mimic a browser and avoid being blocked
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
    }

    try:
        # Get XSRF token from index page
        index_response = session.get(
            INDEX_URL, headers=headers, timeout=REQUEST_TIMEOUT
        )
        _check_response(index_response)

        try:
            xsrf_token = extract_xsrf_token(index_response.text)
        except (AttributeError, IndexError) as e:
            raise ParserException(
                "CNDC.py",
                "Failed to extract XSRF token. Website structure may have changed.",
                "BO",
            ) from e

        # Fetch data with XSRF token
        headers["x-csrf-token"] = xsrf_token
        data_response = session.get(
            DATA_URL.format(formatted_dt), headers=headers, timeout=REQUEST_TIMEOUT
        )
        _check_response(data_response, " when fetching data")

        # Parse JSON response
        try:
            hour_rows = json.loads(data_response.text.replace("ï»¿", ""))["data"]
        except (json.JSONDecodeError, KeyError) as e:
            raise ParserException(
                "CNDC.py",
                f"Failed to parse JSON response. API format may have changed: {e}",
                "BO",
            ) from e

        return hour_rows, target_datetime

    except ParserException:
        raise
    except Exception as e:
        raise ParserException(
            "CNDC.py",
            f"Unexpected error: {type(e).__name__}: {e}",
            "BO",
        ) from e


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

        unknown_value = round(total - thermo - hydro - solar - wind - bagasse, 3)
        unknown_value = None if abs(unknown_value) < 0.05 else unknown_value

        result.append(
            zoneKey=zone_key,
            datetime=timestamp,
            production=ProductionMix(
                hydro=hydro,
                solar=solar,
                wind=wind,
                biomass=bagasse,
                gas=round(thermo * gas_oil_ratio, 3),
                oil=round(thermo * (1 - gas_oil_ratio), 3),
                unknown=unknown_value,
            ),
            source=SOURCE,
        )

    return result


@use_proxy(country_code="BO")
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
    print(fetch_production())
    print("fetch_production() ->")

    # print("fetch_generation_forecast() ->")
    # print(fetch_generation_forecast())
