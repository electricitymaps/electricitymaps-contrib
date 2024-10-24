#!/usr/bin/env python3

# The arrow library is used to handle datetimes consistently with other parsers
from datetime import datetime
from logging import Logger, getLogger
from typing import List, NamedTuple, Optional

import arrow

# BeautifulSoup is used to parse HTML to get information
from bs4 import BeautifulSoup
from requests import Session

tz_bo = "America/La_Paz"

SOURCE = "cndc.bo"


class HourlyProduction(NamedTuple):
    datetime: datetime
    total: Optional[float]
    thermo: Optional[float]
    hydro: Optional[float]
    wind: Optional[float]
    solar: Optional[float]

def has_row_name(names: set):
    def filter(tag):
        try:
            return tag.name == "tr" and tag.contents[1].string in names
        except AttributeError:
            return False
    return filter

def fetch_data_by_hour(
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> List[HourlyProduction]:

    if target_datetime is not None:
        dt = arrow.get(target_datetime, tz_bo)
    else:
        dt = arrow.now(tz=tz_bo)
        print("current dt", dt)

    formatted_dt = dt.format("DDMMYY")
    url = "https://www.cndc.bo/media/archivos/boletindiario/dcdr_{0}.htm"
    response = session.get(url.format(formatted_dt))

    soup = BeautifulSoup(response.text, "html.parser")
    trs = soup.find_all(has_row_name({"SUBTOTAL HIDRO", "SUBTOTAL EOLICO", "SUBTOTAL SOLAR", "SUBTOTAL TERMO"}))
    hourly = dict()
    for tr in trs:
        source: str = tr.contents[1].string
        vals = []
        for i in range(24):
            vals.append(float(tr.contents[3+2*i].string))
        hourly[source] = vals

    return hourly


def fetch_production(
    zone_key: str = "CA-NB",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """Requests the last known production mix (in MW) of a given country."""

    """
    In this case, we are calculating the amount of electricity generated
    in New Brunswick, versus imported and exported elsewhere.
    """

    requests_obj = session or Session()
    flows = fetch_data_by_hour(requests_obj)

    # nb_flows['NB Demand'] is the use of electricity in NB
    # 'EMEC', 'ISO-NE', 'MPS', 'NOVA SCOTIA', 'PEI', and 'QUEBEC'
    # are exchanges - positive for exports, negative for imports
    # Electricity generated in NB is then 'NB Demand' plus all the others

    generated = (
        flows["NB Demand"]
        + flows["EMEC"]
        + flows["ISO-NE"]
        + flows["MPS"]
        + flows["NOVA SCOTIA"]
        + flows["PEI"]
        + flows["QUEBEC"]
    )

    data = {
        "datetime": arrow.utcnow().floor("minute").datetime,
        "zoneKey": zone_key,
        "production": {"unknown": generated},
        "storage": {},
        "source": "tso.nbpower.com",
    }

    return data


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())

