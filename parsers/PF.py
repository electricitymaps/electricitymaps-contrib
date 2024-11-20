#!/usr/bin/env python3

import json
import re
from datetime import datetime
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from requests import Session

from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.exceptions import ParserException

PARSER = "PF.py"
TIMEZONE = ZoneInfo("Pacific/Tahiti")

PRODUCTION_API_URL = "https://www.edt.pf/transition-energetique-innovation"
PRODUCTION_SOURCE = "edt.pf"


def fetch_production(
    zone_key: ZoneKey = ZoneKey("PF"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Requests the last known production mix (in MW) of a given country."""
    session = session or Session()

    if target_datetime is not None:
        raise ParserException(
            PARSER, "This parser is not yet able to parse historical data", zone_key
        )

    time = datetime.now(tz=TIMEZONE)
    response = session.get(PRODUCTION_API_URL)
    if not response.ok:
        raise ParserException(
            PARSER,
            f"Exception when fetching production error code: {response.status_code}: {response.text}",
            zone_key,
        )

    soup = BeautifulSoup(response.text, "lxml")
    block = soup.find(
        id="id1____detailMesurePortlet__WAR__EDTAEL2018__Script"
    ).prettify()
    block = block.replace("\n", "")
    block = re.search(r'\{"cols.*\}\]\}\]\}', block)
    data_table = block.group(0)
    data_table = re.sub("Thermique", "oil", data_table)
    data_table = re.sub("Hydro électricité", "hydro", data_table)
    data_table = re.sub("Solaire", "solar", data_table)
    data_dict = json.loads(data_table)

    # Parse the dict 'data_dict' containing the production mix (the values are in kW)
    production_mix = ProductionMix()
    for line in data_dict["rows"]:
        resource = line["c"][0].get("v")
        production_value = line["c"][1].get("v")
        production_value_mw = production_value / 1000
        production_mix.add_value(resource, production_value_mw)

    production_breakdown_list = ProductionBreakdownList(logger)
    production_breakdown_list.append(
        zoneKey=zone_key,
        datetime=time.replace(second=0, microsecond=0),  # truncate to minutes
        source=PRODUCTION_SOURCE,
        production=production_mix,
    )
    return production_breakdown_list.to_list()


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())
