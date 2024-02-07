#!/usr/bin/env python3
from datetime import datetime
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from requests import Session

from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.exceptions import ParserException

SOURCE = "yukonenergy.ca"
TIMEZONE = ZoneInfo("America/Whitehorse")
URL = "http://www.yukonenergy.ca/consumption/chart_current.php?chart=current&width=420"
ZONE_KEY = ZoneKey("CA-YT")


def _parse_mw(text):
    """
    Extract the power value from the source's HTML text content. The text
    is formatted as, e.g., "37.69 MW - hydro".
    """
    try:
        return float(text[: text.index(" MW")])
    except ValueError as e:
        raise ParserException(
            "YUKONENERGY.py",
            f"Unable to parse power value from '{text}'",
            ZONE_KEY,
        ) from e


def fetch_production(
    zone_key: ZoneKey = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """
    Requests the last known production mix (in MW) of a given region.

    We are using Yukon Energy's data from
    http://www.yukonenergy.ca/energy-in-yukon/electricity-101/current-energy-consumption

    Generation in Yukon is done with hydro, diesel oil, and LNG.

    There are two companies, Yukon Energy and ATCO aka Yukon Electric aka YECL.
    Yukon Energy does most of the generation and feeds into Yukon's grid. ATCO
    does operations, billing, and generation in some of the off-grid
    communities.

    See schema of the grid at http://www.atcoelectricyukon.com/About-Us/

    Per https://en.wikipedia.org/wiki/Yukon#Municipalities_by_population of
    total population 35874 (2016 census), 28238 are in municipalities that are
    connected to the grid - that is 78.7%.

    Off-grid generation is with diesel generators, this is not reported online
    as of 2017-06-23 and is not included in this calculation.

    Yukon Energy reports only "hydro" and "thermal" generation. Per
    http://www.yukonenergy.ca/ask-janet/lng-and-boil-off-gas, in 2016 the
    thermal generation was about 50% diesel and 50% LNG. But since Yukon Energy
    doesn't break it down on their website, we return all thermal as "unknown".

    Per https://en.wikipedia.org/wiki/List_of_generating_stations_in_Yukon
    Yukon Energy operates about 98% of Yukon's hydro capacity, the only
    exception is the small 1.3 MW Fish Lake dam operated by ATCO/Yukon
    Electrical. That's small enough to not matter, I think.

    There is also a small 0.81 MW wind farm, its current generation is not
    available.
    """

    if zone_key != ZONE_KEY:
        raise ParserException("CA_YT.py", "Cannot parse zone '{zone_key}'", zone_key)
    if target_datetime:
        raise ParserException("CA_YT.py", "Unable to fetch historical data", zone_key)

    session = session or Session()
    soup = BeautifulSoup(session.get(URL).text, "html.parser")

    # Extract the relevant HTML data.
    # The date is formatted as, e.g., "Thursday, June 22, 2017".
    date = soup.find("div", class_="current_date").text
    # The time is formatted as, e.g., "11:55 pm" or "2:25 am".
    time = soup.find("div", class_="current_time").text
    # Note: hydro capacity is not provided when thermal is in use.
    _hydro_capacity = soup.find(
        "div", class_="avail_hydro"
    )  # Should we just remove the capacity parsing?
    thermal = soup.find("div", class_="load_thermal").div

    production_mix = ProductionMix()
    production_mix.add_value("coal", 0)
    production_mix.add_value("geothermal", 0)
    production_mix.add_value(
        "hydro", _parse_mw(soup.find("div", class_="load_hydro").div.text)
    )
    production_mix.add_value("nuclear", 0)
    production_mix.add_value("unknown", _parse_mw(thermal.text) if thermal else 0)

    production_breakdowns = ProductionBreakdownList(logger=logger)
    production_breakdowns.append(
        datetime=datetime.strptime(f"{date} {time}", "%A, %B %d, %Y %I:%M %p").replace(
            tzinfo=TIMEZONE
        ),
        production=production_mix,
        source=SOURCE,
        zoneKey=ZONE_KEY,
    )

    return production_breakdowns.to_list()


if __name__ == "__main__":
    # Never used by the Electricity Map backend, but handy for testing.

    print("fetch_production() ->")
    print(fetch_production())
