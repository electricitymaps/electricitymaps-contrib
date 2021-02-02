#!/usr/bin/env python3

"""Parser for the electricity grid of Nigeria"""

import arrow
import logging
import requests
from bs4 import BeautifulSoup


LIVE_PRODUCTION_API_URL = "https://www.niggrid.org/GenerationLoadProfileBinary?readingDate={0}&readingTime={1}"
TYPE_MAPPING = {"hydro": "hydro", "gas": "gas", "gas/steam": "gas", "steam": "gas"}


def extract_name_tech(company):
    parts = company.split("(")
    tech = parts[1].strip(")").lower()

    return parts[0], TYPE_MAPPING[tech]


def template_response(zone_key, datetime, source):
    return {
        "zoneKey": zone_key,
        "datetime": datetime,
        "production": {
            "gas": 0.0,
            "hydro": 0.0,
        },
        "storage": {},
        "source": source,
    }


def fetch_production(
    zone_key=None,
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
):
    """Requests the last known production mix (in MW) of a given zone
    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple zones
    session (optional) -- request session passed in order to re-use an existing session
    target_datetime (optional) -- used if parser can fetch data for a specific day, a string in the form YYYYMMDD
    logger (optional) -- handles logging when parser is run
    Return:
    A list of dictionaries in the form:
    {
      'zoneKey': 'FR',
      'datetime': '2017-01-01T00:00:00Z',
      'production': {
          'biomass': 0.0,
          'coal': 0.0,
          'gas': 0.0,
          'hydro': 0.0,
          'nuclear': null,
          'oil': 0.0,
          'solar': 0.0,
          'wind': 0.0,
          'geothermal': 0.0,
          'unknown': 0.0
      },
      'storage': {
          'hydro': -10.0,
      },
      'source': 'mysource.com'
    }
    """

    if target_datetime is not None:
        timestamp = arrow.get(target_datetime).to("Africa/Lagos").replace(minute=0)
    else:
        timestamp = arrow.now(tz="Africa/Lagos").replace(minute=0)

    dt_day = timestamp.format("DD/MM/YYYY")
    dt_hm = timestamp.format("HH:mm")
    fullUrl = LIVE_PRODUCTION_API_URL.format(dt_day, dt_hm)

    r = session or requests.session()
    resp = r.get(fullUrl)

    try:
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table", {"id": "MainContent_gvGencoLoadProfiles"})
        rows = table.find_all("tr")[1:-1]  # ignore header and footer rows
    except AttributeError:
        raise LookupError("No data currently available for Nigeria.")

    result = template_response(zone_key, timestamp.datetime, "niggrid.org")

    for row in rows:
        _, company, mw, _ = map(lambda row: row.text.strip(), row.find_all("td"))
        _, tech = extract_name_tech(company)

        result["production"][tech] += float(mw)

    return [result]


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""
    print(fetch_production())
    print(fetch_production(target_datetime=arrow.get("20210110", "YYYYMMDD")))
