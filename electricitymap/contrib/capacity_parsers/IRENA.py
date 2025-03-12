import json
from datetime import datetime
from logging import getLogger
from typing import Any

import pycountry
from requests import Response, Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.config.capacity import CAPACITY_PARSER_SOURCE_TO_ZONES

"""The data is downloaded from the IRENA API. """
logger = getLogger(__name__)
IRENA_ZONES = CAPACITY_PARSER_SOURCE_TO_ZONES["IRENA"]
SOURCE = "IRENA.org"
IRENA_JSON_TO_MODE_MAPPING = {
    1: "solar",  # Total Renewable
    2: "solar",  # Solar thermal energy
    3: "wind",  # Onshore wind energy
    4: "wind",  # Offshore wind energy
    5: "hydro",  # Renewable hydropower
    6: "hydro",  # Mixed Hydro Plants
    7: "marine",  # Marine energy
    8: "biomass",  # Solid biofuels
    9: "biomass",  # Renewable municipal waste
    10: "biomass",  # Liquid biofuels
    11: "biomass",  # Biogas
    12: "geothermal",  # Geothermal energy
    14: "hydro_storage",  # Pumped storage
    15: "coal",  # Coal and peat
    16: "oil",  # Oil
    17: "gas",  # Natural gas
    18: "unknown",  # Fossil fuels n.e.s.
    19: "nuclear",  # Nuclear
    20: "unknown",  # Other non-renewable energy
}

SPECIFIC_MODE_MAPPING = {
    "IS": {16: "oil"}
}  # After investigating the data, it seems like IRENA reports oil production as unknown so it will be reallocated as oil.


def get_data_from_url(target_datetime: datetime, session: Session) -> list:
    base_url = (
        "https://pxweb.irena.org:443/api/v1/en/IRENASTAT/Power Capacity and Generation/"
    )
    url_year = datetime.now().year
    filename_combinations = [
        f"Country_ELECSTAT_{url_year}_H2.px",
        f"Country_ELECSTAT_{url_year-1}_H2.px",
    ]
    json_query = {
        "query": [
            {
                "code": "Year",
                "selection": {
                    "filter": "item",
                    "values": [target_datetime.strftime("%y")],
                },
            }
        ],
        "response": {"format": "json"},
    }
    data = None
    for filename in filename_combinations:
        url = base_url + filename

        json_data = json.dumps(json_query)
        r: Response = session.post(url, data=json_data)
        if r.status_code == 200:
            data = r.json()
        else:
            continue
    if not data:
        raise ValueError(f"Could not fetch data for {target_datetime.year}")
    return data["data"]


def reallocate_capacity_mode(zone_key: ZoneKey, mode: int) -> dict:
    if zone_key in SPECIFIC_MODE_MAPPING and mode in SPECIFIC_MODE_MAPPING[zone_key]:
        return SPECIFIC_MODE_MAPPING[zone_key][mode]
    return IRENA_JSON_TO_MODE_MAPPING[mode]


def get_capacity_data_for_all_zones(
    target_datetime: datetime, session: Session
) -> dict:
    data = get_data_from_url(target_datetime, session)
    capacity_dict = {}
    for item in data:
        if pycountry.countries.get(alpha_3=item["key"][0]) is not None:
            zone = pycountry.countries.get(alpha_3=item["key"][0]).alpha_2
        else:
            pass
        if int(item["key"][1]) not in IRENA_JSON_TO_MODE_MAPPING:
            continue
        mode: str = IRENA_JSON_TO_MODE_MAPPING[int(item["key"][1])]
        value: float = round(
            float(item["values"][0] if item["values"][0] != "-" else 0), 0
        )
        datetime_value: datetime = datetime.strptime(item["key"][-1], "%y")

        if zone not in capacity_dict:
            zone_dict = {
                mode: {
                    "datetime": datetime_value.strftime("%Y-%m-%d"),
                    "value": value,
                    "source": SOURCE,
                }
            }
            capacity_dict[zone] = zone_dict
        else:
            mode = reallocate_capacity_mode(zone, int(item["key"][1]))
            if mode in capacity_dict[zone]:
                zone_dict = capacity_dict[zone][mode]
                capacity_dict[zone][mode]["value"] += value
            else:
                capacity_dict[zone] = {
                    **capacity_dict[zone],
                    **{
                        mode: {
                            "datetime": datetime_value.strftime("%Y-%m-%d"),
                            "value": value,
                            "source": SOURCE,
                        }
                    },
                }
    return capacity_dict


def fetch_production_capacity(
    target_datetime: datetime, zone_key: ZoneKey, session: Session
) -> dict[str, Any] | None:
    all_capacity = get_capacity_data_for_all_zones(target_datetime, session)
    zone_capacity = all_capacity[zone_key]

    if zone_capacity:
        logger.info(
            f"Fetched capacity for {zone_key} in {target_datetime.year}: \n{zone_capacity}"
        )
        return zone_capacity
    else:
        logger.warning(f"No capacity data for {zone_key} in {target_datetime.year}")


def fetch_production_capacity_for_all_zones(
    target_datetime: datetime, session: Session
) -> dict[str, Any] | None:
    all_capacity = get_capacity_data_for_all_zones(target_datetime, session)

    all_capacity = {k: v for k, v in all_capacity.items() if k in IRENA_ZONES}
    logger.info(f"Fetched capacity data from IRENA for {target_datetime.year}")
    return all_capacity
