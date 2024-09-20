#!/usr/bin/env python3

"""Parser for the Nigerian electricity grid"""

import re
import urllib.parse
from datetime import datetime, timedelta, timezone
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

import bs4
from requests import Session

from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib import config

API_URL = urllib.parse.urlparse("https://niggrid.org/GenerationProfile2")
API_URL_STRING = API_URL.geturl()
NORMALISE = {
    "gas": "gas",
    "gas/steam": "gas",
    "hydro": "hydro",
    # Per the "Electricity generation by source" plot at
    # https://www.iea.org/countries/nigeria, the majority of Nigeria's
    # generation comes from natural gas, so "steam" most likely implies "gas";
    # therefore, we do not map "steam" to "unknown" (coal/gas/oil). See issues
    # #2570 and #3651 for more information.
    "steam": "gas",
}
PATTERN = re.compile(r"\((.*)\)")
TIMEZONE = ZoneInfo("Africa/Lagos")


def get_data(session: Session, logger: Logger, timestamp: datetime):
    # GET the landing page (HTML) and scrape some form data from it.
    response = session.get(API_URL_STRING)
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    data = {tag["name"]: tag["value"] for tag in soup.find_all("input")}
    data["ctl00$MainContent$txtReadingDate"] = timestamp.strftime("%Y/%m/%d")

    # Send a POST request for the desired grid data using parameters from the
    # landing page form. The grid data is presented as an HTML table; we ignore
    # its header and footer rows.
    response = session.post(API_URL_STRING, data=data)
    rows = bs4.BeautifulSoup(response.text, "html.parser").find_all("tr")[1:-1]

    # Values from the future should not be returned
    max_hour = min(
        int(
            (datetime.now(TIMEZONE) - timestamp.replace(hour=0)).total_seconds() / 3600
        ),
        24,
    )

    production_dict = {}
    production_mix = ProductionMix()

    for hour in range(0, max_hour):
        production_dict[timestamp.replace(hour=hour)] = production_mix.copy()

    for row in rows:
        _, source, *power, _ = (tag.text for tag in row.find_all("td"))
        try:
            technology = NORMALISE[PATTERN.search(source).group(1).casefold()]
        except (AttributeError, KeyError):
            logger.warning(f"Unexpected source '{source.strip()}' encountered")
            continue
        for hour in range(0, max_hour):
            production_dict[timestamp.replace(hour=hour)].add_value(
                technology,
                float(power.pop(0)),
            )
    return production_dict


# The data is hourly, but it takes a few minutes after the turn of each hour
# for the server to populate it. Setting the re-fetch frequency to 45 min will
# ensure that if the live data is missing for a given hour when it's first
# fetched, it will be fetched again during the same hour. (As far as I can
# tell, the table is always populated within 15 min of the turn of the hour).
@config.refetch_frequency(timedelta(minutes=45))
def fetch_production(
    zone_key: ZoneKey = ZoneKey("NG"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Requests the last known production mix (in MW) of a given zone."""

    if target_datetime is None:
        target_datetime = datetime.now(timezone.utc)
    timestamp = target_datetime.replace(minute=0, second=0, microsecond=0).astimezone(
        TIMEZONE
    )

    session = session or Session()
    production_dict = get_data(session=session, logger=logger, timestamp=timestamp)

    # Add data from previous day if few hours ago to update preliminary data
    if len(production_dict) < 12:
        production_dict = production_dict | get_data(
            session=session, logger=logger, timestamp=timestamp - timedelta(days=1)
        )

    production_list = ProductionBreakdownList(logger=logger)
    for ts in production_dict:
        production_list.append(
            zoneKey=zone_key,
            datetime=ts,
            production=production_dict[ts],
            source=API_URL.netloc,
        )
    return production_list.to_list()


if __name__ == "__main__":
    """Never used by the Electricity Map backend, but handy for testing."""
    print(fetch_production())
    print(
        fetch_production(target_datetime=datetime.fromisoformat("2022-03-09T15:00:00"))
    )
