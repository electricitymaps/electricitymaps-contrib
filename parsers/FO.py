#!/usr/bin/env python3
# coding=utf-8

from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Dict, List, Literal, Optional, TypedDict

import arrow
from requests import Response, Session

from parsers.lib.config import refetch_frequency

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

VALID_ZONE_KEYS = Literal["FO", "FO-NI", "FO-SI"]


class ValidationObject(TypedDict):
    required: List[str]
    floor: int


class ZoneData(TypedDict):
    data_key: str
    validation: ValidationObject


ZONE_MAP: Dict[VALID_ZONE_KEYS, ZoneData] = {
    "FO": {"data_key": "Sev_E", "validation": {"required": ["hydro"], "floor": 10}},
    "FO-NI": {"data_key": "H_E", "validation": {"required": ["hydro"], "floor": 9}},
    "FO-SI": {"data_key": "S_E", "validation": {"required": ["hydro"], "floor": 1}},
}


def map_generation_type(raw_generation_type):
    return MAP_GENERATION.get(raw_generation_type, None)


@refetch_frequency(timedelta(minutes=5))
def fetch_production(
    zone_key: VALID_ZONE_KEYS = "FO",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger("FO"),
) -> dict:
    if target_datetime:
        # There is a API endpoint at https://www.sev.fo/api/elproduction/last7days
        # but it's currently returning nothing at all. Last checked on 2022-08-09
        raise NotImplementedError("This parser is not yet able to parse past dates")

    ses = session or Session()
    url = "https://www.sev.fo/api/realtimemap/now"
    response: Response = ses.get(url)
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
        elif key.endswith(ZONE_MAP[zone_key]["data_key"]):
            # E stands for Energy
            raw_generation_type: str = key.replace(ZONE_MAP[zone_key]["data_key"], "")
            generation_type = map_generation_type(raw_generation_type)
            if not generation_type:
                raise ParserException(
                    "FO.py", f"Unknown generation type: {raw_generation_type}", zone_key
                )
            # Power (MW)
            value = float(value.replace(",", "."))
            data["production"][generation_type] = (
                data["production"].get(generation_type, 0) + value
            )
        else:
            # print 'Unhandled key %s' % key
            pass

    data = validate(
        data,
        logger,
        required=ZONE_MAP[zone_key]["validation"]["required"],
        floor=ZONE_MAP[zone_key]["validation"]["floor"],
    )
    if isinstance(data, dict):
        return data
    else:
        raise ParserException(
            "FO.py",
            f"No valid data was returned for {zone_key}",
            zone_key,
        )


if __name__ == "__main__":
    print(fetch_production())
