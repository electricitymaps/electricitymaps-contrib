#!/usr/bin/env python3
"""
This parser returns Kuwait's electricity system load (assumed to be equal to electricity production)
Source: Ministry of Electricity and Water / State of Kuwait
URL: https://www.mew.gov.kw/en/
Scroll down to see the system load gauge
Shares of Electricity production in 2017: 65.6% oil, 34.4% gas (source: IEA; https://www.iea.org/statistics/?country=KUWAIT&indicator=ElecGenByFuel)
"""

import re
from datetime import datetime
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

from requests import Session


def fetch_consumption(
    zone_key: str = "KW",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
):
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    r = session or Session()
    url = "https://www.mew.gov.kw/en"
    response = r.get(url)
    load = re.findall(r"\((\d{4,5})\)", response.text)
    load = int(load[0])
    consumption = load

    datapoint = {
        "zoneKey": zone_key,
        "datetime": datetime.now(tz=ZoneInfo("Asia/Kuwait")),
        "consumption": consumption,
        "source": "mew.gov.kw",
    }

    return datapoint


if __name__ == "__main__":
    """Main method, never used by the electricityMap backend, but handy for testing."""

    print("fetch_consumption() ->")
    print(fetch_consumption())
