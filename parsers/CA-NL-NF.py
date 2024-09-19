#!/usr/bin/env python3

import arrow
from datetime import datetime
from logging import Logger, getLogger
from typing import Optional

from bs4 import BeautifulSoup
from requests import Session

# This parser fetches demand data for Canada-Newfoundland. The source-website https://nlhydro.com/ states:
# "Current Island System Generation", so I assume only generation for Newfoundland island, excluding Labrador, is shown.
# "Current system generation = current demand on the system" and
# "Any generation from non-utility generators, including Star Lake, Rattle Brook, Corner Brook Pulp and Paper,
# and wind generation from the St. Lawrence and Fermeuse wind farms, is included in our Hydro System Generation."
# This means we have a mix of hydro, oil, biomass and wind energy represented in the demand/generation figure.

NF_DEMAND_URL = "https://nlhydro.com/system-information/supply-and-demand/"
TZ = "Canada/Newfoundland"  # UTC-3:30

def fetch_consumption(
    zone_key: str = "CA-NL-NF",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
):
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates.")
    with session.get(NF_DEMAND_URL) as response:
        NF_DEMAND_SOUP = BeautifulSoup(response.content, "html.parser")

    consumption_MW = float(NF_DEMAND_SOUP.find_all("p")[1].text.strip(" MW"))

    timestamp_raw = NF_DEMAND_SOUP.find_all("p")[2].text.strip("AS OF ")
    timestamp = arrow.get(timestamp_raw, "M/D/YYYY H:m A", tzinfo=TZ)

    data = {
        "zoneKey": zone_key,
        "datetime": timestamp,
        "consumption": consumption_MW,
        "source": "https://nlhydro.com/",
    }

    return data

if __name__ == "__main__":
    print("fetch_consumption() ->")
    print(fetch_consumption())
