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
SOURCE = "openelectricity.org.au"
mapping_states = {
    "AU-NSW": "NEM/NSW1",
    "AU-QLD": "NEM/QLD1",
    "AU-SA": "NEM/SA1",
    "AU-VIC": "NEM/VIC1",
    "AU-TAS": "NEM/TAS1",
    "AU-WA": "WEM",
}
time_zone_mapping = {
    "AU-NSW": ZoneInfo("Australia/Sydney"),
    "AU-QLD": ZoneInfo("Australia/Brisbane"),
    "AU-SA": ZoneInfo("Australia/Adelaide"),
    "AU-VIC": ZoneInfo("Australia/Melbourne"),
    "AU-TAS": ZoneInfo("Australia/Hobart"),
    "AU-WA": ZoneInfo("Australia/Perth"),
}

def get_url(zone_key: ZoneKey, time_period: str = "7d") -> str:
    assert time_period in ["1d", "7d"]
    return f"https://data.openelectricity.org.au/v4/stats/au/{mapping_states[zone_key]}/power/{time_period}.json"




def fetch_production(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")
    url = get_url(zone_key, time_period='7d')
    r = session or Session()
    response = r.get(url)
    data = response.json()
    top_data = data["data"]["power"]["total"]

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
    ).replace(tzinfo=time_zone_mapping[zone_key])

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
