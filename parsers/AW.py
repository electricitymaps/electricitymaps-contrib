#!/usr/bin/env python3

from datetime import datetime
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

from requests import Session

from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey

from .lib.exceptions import ParserException

FUEL_MAPPING = {
    "Fossil": "oil",
    "Wind": "wind",
    "TotalSolar": "solar",
    "total_bio_gas": "biomass",
}
TIMEZONE = ZoneInfo("America/Aruba")
PRODUCTION_URL = (
    "https://www.webaruba.com/renewable-energy-dashboard/app/rest/results.json"
)
SOURCE = "webaruba.com"


def fetch_production(
    zone_key: ZoneKey = ZoneKey("AW"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    r = session or Session()
    # User agent is mandatory or services answers 404
    headers = {
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)"
    }
    response = r.get(PRODUCTION_URL, headers=headers)
    aruba_json = response.json()
    top_data = aruba_json["dashboard_top_data"]
    mix = ProductionMix()
    sources_total = 0
    for fuel, mode in FUEL_MAPPING.items():
        value = float(top_data[fuel]["value"])
        mix.add_value(mode, value)
        sources_total += value
    # "unknown" is when data reported in the categories above is less than total reported.
    # If categories sum up to more than total, accept the datapoint, but only if it's less than 10% of total.
    # This helps avoid missing data when it's a little bit off, due to rounding or reporting
    reported_total = float(top_data["TotalPower"]["value"])

    if (sources_total / reported_total) > 1.1:
        raise ParserException(
            "AW.py",
            f"AW parser reports fuel sources add up to {sources_total} but total generation {reported_total} is lower",
            zone_key,
        )

    mix.add_value(
        "unknown", reported_total - sources_total, correct_negative_with_zero=True
    )
    # We're using Fossil data to get timestamp in correct time zone
    local_date_time = datetime.strptime(
        top_data["total_bio_gas"]["timestamp"], "%Y-%m-%d %H:%M:%S.%f"
    ).replace(tzinfo=TIMEZONE)

    production_list = ProductionBreakdownList(logger)
    production_list.append(
        zone_key,
        local_date_time,
        SOURCE,
        production=mix,
    )

    return production_list.to_list()


if __name__ == "__main__":
    print(fetch_production())
