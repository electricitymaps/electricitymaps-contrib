#!/usr/bin/env python3
# coding=utf-8

from datetime import datetime
from logging import getLogger
from typing import Optional

import arrow
from requests import Session

from .lib.exceptions import ParserException
from .lib.validation import validate

MAP_GENERATION = {
    "Vand": "hydro",
    "Olie": "oil",
    "Diesel": "oil",
    "Vind": "wind",
    "Sol": "solar",
    "Biogas": "biomass",
    "Tidal": "unknown",
}


def map_generation_type(raw_generation_type):
    return MAP_GENERATION.get(raw_generation_type, None)


def fetch_production(
    zone_key="FO",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger=getLogger("FO"),
) -> dict:
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    r = session or Session()
    url = "https://www.sev.fo/api/realtimemap/now"
    response = r.get(url)
    obj = response.json()

    data = {
        "zoneKey": zone_key,
        "capacity": {},
        "production": {
            "biomass": 0,
            "coal": 0,
            "gas": 0,
            "geothermal": 0,
            "nuclear": 0,
            "solar": 0,
            "unknown": 0,
        },
        "storage": {},
        "source": "sev.fo",
    }
    for key, value in obj.items():
        if key == "tiden":
            data["datetime"] = arrow.get(
                arrow.get(value).datetime, "Atlantic/Faroe"
            ).datetime
        elif "Sum" in key:
            continue
        elif "Test" in key:
            continue
        elif "VnVand" in key:
            # This is the sum of hydro (Mýrarnar + Fossá + Heygar)
            continue
        elif key.endswith("Sev_E"):
            # E stands for Energy
            raw_generation_type = key.replace("Sev_E", "")
            generation_type = map_generation_type(raw_generation_type)
            if not generation_type:
                raise ParserException(
                    "FO.py", f"Unknown generation type: {raw_generation_type}", "FO"
                )
            # Power (MW)
            value = float(value.replace(",", "."))
            data["production"][generation_type] = (
                data["production"].get(generation_type, 0) + value
            )
        else:
            # print 'Unhandled key %s' % key
            pass

    data = validate(data, logger, required=["hydro"], floor=10.0)

    return data


if __name__ == "__main__":
    print(fetch_production())
