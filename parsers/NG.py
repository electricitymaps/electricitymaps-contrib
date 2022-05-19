#!/usr/bin/env python3

"""Parser for the Nigerian electricity grid"""

# Standard library imports
import datetime
import logging
import re
import urllib.parse

# Third-party library imports
import arrow
import bs4
import requests

# Local library imports
from parsers.lib import config, validation

API_URL = urllib.parse.urlparse("https://niggrid.org/GenerationProfile")
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


# The data is hourly, but it takes a few minutes after the turn of each hour
# for the server to populate it. Setting the re-fetch frequency to 45 min will
# ensure that if the live data is missing for a given hour when it's first
# fetched, it will be fetched again during the same hour. (As far as I can
# tell, the table is always populated within 15 min of the turn of the hour).
@config.refetch_frequency(datetime.timedelta(minutes=45))
def fetch_production(
    zone_key="NG",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
) -> dict:
    """Requests the last known production mix (in MW) of a given zone."""
    timestamp = (
        arrow.get(target_datetime)
        .to("Africa/Lagos")
        .replace(minute=0, second=0, microsecond=0)
    )

    # GET the landing page (HTML) and scrape some form data from it.
    session = session or requests.Session()
    response = session.get(API_URL_STRING)
    soup = bs4.BeautifulSoup(response.text, "html.parser")
    data = {tag["name"]: tag["value"] for tag in soup.find_all("input")}
    data["ctl00$MainContent$txtReadingDate"] = timestamp.format("DD/MM/YYYY")
    data["ctl00$MainContent$ddlTime"] = timestamp.format("HH:mm")

    # Send a POST request for the desired grid data using parameters from the
    # landing page form. The grid data is presented as an HTML table; we ignore
    # its header and footer rows.
    response = session.post(API_URL_STRING, data=data)
    rows = bs4.BeautifulSoup(response.text, "html.parser").find_all("tr")[1:-1]
    production_mix = {technology: 0.0 for technology in NORMALISE.values()}
    for row in rows:
        _, source, power, _ = (tag.text for tag in row.find_all("td"))
        try:
            technology = NORMALISE[PATTERN.search(source).group(1).casefold()]
        except (AttributeError, KeyError) as error:
            logger.warning(f"Unexpected source '{source.strip()}' encountered")
            continue
        production_mix[technology] += float(power)

    # Return the production mix.
    return validation.validate(
        {
            "zoneKey": zone_key,
            "datetime": timestamp.datetime,
            "production": production_mix,
            "source": API_URL.netloc,
        },
        logger,
        floor=10.0,
        remove_negative=True,
    )


if __name__ == "__main__":
    """Never used by the Electricity Map backend, but handy for testing."""
    print(fetch_production())
    print(fetch_production(target_datetime="2022-03-09T15:00:00"))
