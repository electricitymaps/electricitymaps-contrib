#!/usr/bin/env python3

import json
import logging
import re

import arrow
import lxml
import requests
from bs4 import BeautifulSoup

TZ = "Pacific/Tahiti"


def fetch_production(
    zone_key="PF",
    session=None,
    target_datetime=None,
    logger: logging.Logger = logging.getLogger(__name__),
) -> dict:
    """Requests the last known production mix (in MW) of a given country."""
    r = session or requests.Session()
    if target_datetime is None:
        url = "https://www.edt.pf/transition-energetique-innovation"
    else:
        # WHEN HISTORICAL DATA IS NOT AVAILABLE
        raise NotImplementedError("This parser is not yet able to parse past dates")

    res = r.get(url)
    assert res.status_code == 200, (
        "Exception when fetching production for "
        "{}: error when calling url={}".format(zone_key, url)
    )

    soup = BeautifulSoup(res.text, "lxml")
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

    data = {
        "zoneKey": zone_key,
        "datetime": arrow.utcnow().floor("minute").datetime,
        "production": {
            "biomass": 0.0,
            "coal": 0.0,
            "gas": 0.0,
            "hydro": None,
            "nuclear": 0.0,
            "oil": None,
            "solar": None,
            "wind": None,
            "geothermal": 0.0,
            "unknown": None,
        },
        "storage": {},
        "source": "edt.pf",
    }

    # Parse the dict 'data_dict' containing the production mix (the values are in kW)
    for line in data_dict["rows"]:
        resource = line["c"][0].get("v")
        production_value = line["c"][1].get("v")
        production_value_mw = production_value / 1000
        data["production"][resource] = production_value_mw

    return data


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())
