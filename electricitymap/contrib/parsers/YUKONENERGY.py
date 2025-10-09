#!/usr/bin/env python3
import json
import re
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from requests import Session

from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey
from electricitymap.contrib.parsers.lib.exceptions import ParserException

SOURCE = "yukonenergy.ca"
TIMEZONE = ZoneInfo("America/Whitehorse")
URL = "http://www.yukonenergy.ca/consumption/chart_current.php?chart=current&width=420"
ZONE_KEY = ZoneKey("CA-YT")

FUEL_MAPPING = {
    "thermal": "unknown",
    "hydro": "hydro",
    "wind": "wind",
    "solar": "solar",
}


def fetch_production(
    zone_key: ZoneKey = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """
    We are using Yukon Energy's data from
    http://www.yukonenergy.ca/energy-in-yukon/electricity-101/current-energy-consumption

    Generation in Yukon is done with solar, wind, hydro, diesel oil, and LNG.

    There are two companies, Yukon Energy and ATCO aka Yukon Electric aka YECL.
    Yukon Energy does most of the generation and feeds into Yukon's grid. ATCO
    does operations, billing, and generation in some of the off-grid
    communities.

    See schema of the grid at http://www.atcoelectricyukon.com/About-Us/

    Thermal is a mix of diesel oil and LNG, therefore thermal is set to unknown.
    https://yukonenergy.ca/energy-in-yukon/projects-facilities/
    """

    if zone_key != ZONE_KEY:
        raise ParserException(
            "YUKONENERGY.py", "Cannot parse zone '{zone_key}'", zone_key
        )
    if target_datetime:
        raise ParserException(
            "YUKONENERGY.py", "Unable to fetch historical data", zone_key
        )

    session = session or Session()

    response = session.get(URL)
    html = response.text
    soup = BeautifulSoup(html, "html.parser")

    # Extract JavaScript data
    match_past_day = re.search(
        r"var rows_chart_past_day = parseDates\((\[\[.*?\]\])\);", html, re.DOTALL
    )
    match_current = re.search(
        r"var rows_chart_current = parseDates\((\[\[.*?\]\])\);", html, re.DOTALL
    )
    if not match_past_day or not match_current:
        raise ParserException("YUKONENERGY.py", "Cannot find data", zone_key)

    past_day_data = json.loads(match_past_day.group(1))
    current_data = json.loads(match_current.group(1))

    # Search html for when the data was updatead
    pane = soup.find("div", class_="consumption-pane total")
    updated_text = pane.find("p").get_text(strip=True) if pane else None

    timestamp = None
    if updated_text:
        match = re.search(r"Updated (\d+) minute", updated_text)
        if match:
            minutes_ago = int(match.group(1))
            timestamp = datetime.now(TIMEZONE) - timedelta(minutes=minutes_ago)
        else:
            timestamp = datetime.now(TIMEZONE)

    else:
        timestamp = datetime.now(TIMEZONE)

    timestamp = timestamp.replace(second=0, microsecond=0).isoformat(timespec="seconds")

    if timestamp != past_day_data[-1][0]:
        new_row = [timestamp] + [source[1] for source in current_data[:-1]]
        past_day_data.append(new_row)

    # Remove capacity
    production_mode_order = [item[0].lower() for item in current_data][:-1]

    all_production_breakdowns: list[ProductionBreakdownList] = []

    for item in past_day_data:
        time, *datetime_data = item

        production_mode_list = ProductionBreakdownList(logger)
        productionMix = ProductionMix()

        for i, data in enumerate(datetime_data):
            production_mode = FUEL_MAPPING.get(production_mode_order[i])
            productionMix.add_value(production_mode, round(float(data), 3))

        production_mode_list.append(
            zoneKey=zone_key,
            datetime=datetime.fromisoformat(time).replace(tzinfo=TIMEZONE),
            source=SOURCE,
            production=productionMix,
        )
        all_production_breakdowns.append(production_mode_list)

        production_events = ProductionBreakdownList.merge_production_breakdowns(
            all_production_breakdowns, logger
        )
        production_events = production_events.to_list()

    return production_events


if __name__ == "__main__":
    # Never used by the Electricity Map backend, but handy for testing.

    print("fetch_production() ->")
    print(fetch_production())
