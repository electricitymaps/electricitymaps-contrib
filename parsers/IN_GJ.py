#!/usr/bin/env python3

import collections
import itertools
import re
from logging import getLogger
from operator import itemgetter

import arrow
import requests

from .lib import IN, web, zonekey
from .lib.validation import validate

SLDCGUJ_URL = (
    "http://www.sldcguj.com/RealTimeData/PrintPage.php?page=realtimedemand.php"
)

station_map = {
    "coal": [
        "Ukai(1-5)+Ukai6",
        "Wanakbori",
        "Gandhinagar",
        "Sikka(3-4)",
        "KLTPS(1-3)+KLTPS4",
        "SLPP(I+II)",
        "Akrimota",
        "TPAECo",
        "EPGL(I+II)",
        "Adani(I+II+III)",
        "BECL(I+II)",
        "CGPL",
    ],
    "hydro": ["Ukai(Hydro)", "Kadana(Hydro)", "SSP(RBPH)"],
    "gas": [
        "Utran(Gas)(II)",
        "Dhuvaran(Gas)(I)+(II)+(III)",
        "GIPCL(I)+(II)",
        "GSEG(I+II)",
        "GPPC",
        "CLPI",
        "KAWAS",
        "Sugen+Unosgn",
        "JHANOR",
    ],
    "nuclear": ["KAPP"],
}


def split_and_sum(expression) -> float:
    """Avoid using literal_eval for simple addition expressions."""

    split_vals = expression.split("+")
    float_vals = [float(v) for v in split_vals]
    total = sum([v for v in float_vals if v > 0.0])

    return total


def fetch_data(zone_key, session=None, logger=None):
    session = session or requests.session()

    values = collections.Counter()
    zonekey.assert_zone_key(zone_key, "IN-GJ")

    cookies_params = {
        "ASPSESSIONIDSUQQQTRD": "ODMNNHADJFGCMLFFGFEMOGBL",
        "PHPSESSID": "a301jk6p1p8d50dduflceeg6l1",
    }

    soup = web.get_response_soup(zone_key, SLDCGUJ_URL, session)
    rows = soup.find_all("tr")
    cells = [c.text.strip() for c in soup.find_all("td")]

    # get wind and solar values
    values["date"] = arrow.get(cells[1], "D-MM-YYYY H:mm:ss").replace(
        tzinfo="Asia/Kolkata"
    )
    [wind_solar_index] = [
        i for i, c in enumerate(cells) if c == "(Wind+Solar) Generation"
    ]
    value = cells[wind_solar_index + 1]
    values["wind"], values["solar"] = [int(v) for v in value.split(" + ")]

    # get other production values
    for row in rows:
        elements = row.find_all("td")
        if len(elements) > 3:  # will find production rows
            v1, v2 = (
                re.sub(r"\s+", r"", x.text) for x in itemgetter(*[0, 3])(elements)
            )
            energy_type = [k for k, v in station_map.items() if v1 in v]
            if len(energy_type) > 0:
                v2 = split_and_sum(v2)
                values[energy_type[0]] += v2
            else:
                if "StationName" in (v1, v2):  # meta data row
                    continue
                elif "DSMRate" in v2:  # demand side management
                    continue
                else:
                    try:
                        logger.warning(
                            "Unknown fuel for station name: {}".format(v1),
                            extra={"key": zone_key},
                        )
                        v2 = split_and_sum(v2)
                        values["unknown"] += v2
                    except ValueError as e:
                        # handle float failures
                        logger.warning(
                            "couldn't convert {} to float".format(v2),
                            extra={"key": zone_key},
                        )
                        continue
        elif len(elements) == 3:  # will find consumption row
            v1, v2 = (
                re.sub(r"\s+", r"", x.text) for x in itemgetter(*[0, 2])(elements)
            )
            if v1 == "GujaratCatered":
                values["total consumption"] = split_and_sum(v2.split("MW")[0])
        elif len(elements) == 1:
            # CGPL/KAPP/KAWAS/JHANOR plants have a different html structure.
            plant_name = re.sub(r"\s+", r"", elements[0].text)
            known_plants = itertools.chain.from_iterable(station_map.values())

            if plant_name in known_plants:
                energy_type = [k for k, v in station_map.items() if plant_name in v][0]
                generation_tag = row.find_all_next("td")[3]
                val = float(re.sub(r"\s+", r"", generation_tag.text))
                if val > 0:
                    values[energy_type] += val
            else:
                if plant_name and plant_name != "GMR":
                    # GMR is outside Gujarat, sometimes plant_name is ''
                    logger.warning(
                        "Unknown fuel for station name: {}".format(plant_name),
                        extra={"key": zone_key},
                    )

    return values


def fetch_production(
    zone_key="IN-GJ", session=None, target_datetime=None, logger=getLogger("IN-GJ")
) -> list:
    """Requests the last known production mix (in MW) of a given country."""
    session = session or requests.session()
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    value_map = fetch_data(zone_key, session, logger=logger)

    data = {
        "zoneKey": zone_key,
        "datetime": value_map["date"].datetime,
        "production": {
            "biomass": None,
            "coal": value_map.get("coal", 0),
            "gas": value_map.get("gas", 0),
            "hydro": value_map.get("hydro", 0),
            "nuclear": value_map.get("nuclear", 0),
            "oil": None,
            "solar": value_map.get("solar", 0),
            "wind": value_map.get("wind", 0),
            "geothermal": None,
            "unknown": value_map.get("unknown", 0),
        },
        "storage": {"hydro": None},
        "source": "sldcguj.com",
    }

    valid_data = validate(data, logger, remove_negative=True, floor=7000)

    return valid_data


def fetch_consumption(
    zone_key="IN-GJ", session=None, target_datetime=None, logger=getLogger("IN-GJ")
) -> dict:
    """Method to get consumption data of Gujarat."""
    session = session or requests.session()
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    value_map = fetch_data(zone_key, session, logger=logger)

    data = {
        "zoneKey": zone_key,
        "datetime": value_map["date"].datetime,
        "consumption": value_map["total consumption"],
        "source": "sldcguj.com",
    }

    return data


if __name__ == "__main__":
    session = requests.Session()
    print(fetch_production("IN-GJ", session))
    print(fetch_consumption("IN-GJ", session))
