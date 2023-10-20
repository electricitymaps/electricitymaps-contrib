#!/usr/bin/env python3

"""Quarter-hourly data parser for Sri Lanka
Fetches data for the previous day in 15-minute increments
Data is from the backend for the load curve graph on https://cebcare.ceb.lk/gensum/details
"""

import json
from datetime import datetime, timedelta
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

# The request library is used to fetch content through HTTP
from requests import Session

from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

TIMEZONE = ZoneInfo("Asia/Colombo")
GENERATION_BREAKDOWN_URL = "https://cebcare.ceb.lk/GenSum/GetLoadCurveData"
SOURCE_NAME = "ceb.lk"

PRODUCTION_MAPPING = {
    "SPP Biomass": "biomass",
    "Coal": "coal",
    "Thermal-Oil": "oil",
    "SPP Minihydro": "hydro",
    "Major Hydro": "hydro",
    "Solar": "solar",
    "Wind": "wind",
}


@refetch_frequency(timedelta(hours=24))
def fetch_production(
    zone_key: ZoneKey = ZoneKey("LK"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
):
    """Requests the previous day's production mix (in MW) for Sri Lanka, per quarter-hour"""
    if target_datetime is None:
        target_datetime = datetime.now(tz=TIMEZONE)

    if session is None:
        session = Session()

    params = {
        "date": target_datetime.strftime("%Y-%m-%d"),
    }

    response = session.get(GENERATION_BREAKDOWN_URL, params=params)

    if not response.ok:
        raise ParserException(
            "CEB.py",
            f"Failed to fetch production data. Response Code: {response.status_code}\nError:\n{response.text}",
            zone_key,
        )

    source_data = json.loads(
        response.json()
    )  # Response is double encoded; a JSON array encoded as a JSON string

    production_data = ProductionBreakdownList(logger)

    for quarter_hourly_source_data in source_data:
        production = ProductionMix()

        for generation_type, outputInMW in quarter_hourly_source_data.items():
            if generation_type == "DateTime":
                continue
            elif generation_type in PRODUCTION_MAPPING:
                production.add_value(PRODUCTION_MAPPING[generation_type], outputInMW)
            else:
                logger.warning(
                    f"Unknown generation type {generation_type}",
                    extra={"zone_key": zone_key},
                )

        production_data.append(
            zoneKey=zone_key,
            datetime=datetime.fromisoformat(
                quarter_hourly_source_data["DateTime"]
            ).replace(tzinfo=TIMEZONE),
            production=production,
            source=SOURCE_NAME,
        )

    return production_data.to_list()


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())
