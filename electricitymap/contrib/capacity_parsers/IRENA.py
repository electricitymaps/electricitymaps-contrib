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
    0: "unknown",  # Total Renewable -> Do not consider
    1: "solar",  # Solar photovoltaic	
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
    13: "unknown",  # Total Non-Renewable -> Do not consider
    14: "hydro_storage",  # Pumped storage
    15: "coal",  # Coal and peat
    16: "oil",  # Oil
    17: "gas",  # Natural gas
    18: "unknown",  # Fossil fuels n.e.s.
    19: "nuclear",  # Nuclear
    20: "unknown",  # Other non-renewable energy
}

def get_data_from_url(target_datetime: datetime, session: Session, zone_key_3_letters: str|None=None) -> list:
    base_url = (
        "https://pxweb.irena.org:443/api/v1/en/IRENASTAT/Power Capacity and Generation/"
    )
    url_year = datetime.now().year
    filename_combinations = [
        f"Country_ELECSTAT_{url_year}_H2.px",
        f"Country_ELECSTAT_{url_year-1}_H2.px",
    ]
    query_list = [
            {
                "code": "Year",
                "selection": {
                    "filter": "item",
                    "values": [target_datetime.strftime("%y")],
                }
            },
            {
                "code": "Data Type",
                "selection": {
                    "filter": "item",
                    "values": [
                    "1"  # 1 = Capacity (MW) # 0 = Generation (GWh)
                    ]
                }
            },
            {
                "code": "Technology",
                "selection": { # We are not selecting 0 and 13 because they are total renewable and total non-renewable (see mapping above)
                    "filter": "item",
                    "values": [
                    "1",
                    "2",
                    "3",
                    "4",
                    "5",
                    "6",
                    "7",
                    "8",
                    "9",
                    "10",
                    "11",
                    "12",
                    "14",
                    "15",
                    "16",
                    "17",
                    "18",
                    "19",
                    "20"
                    ]
                }
                },
            {
            "code": "Grid connection",
            "selection": {
                    "filter": "item",
                    "values": [
                    "0" # 0 = Total # 1 = on grid (connected to the main power lines) # 2 = off grid (completely independent of the main power lines)
                    ]
                }
            },
            ]
    if zone_key_3_letters is not None:
        query_list.append({
            "code": "Country/area",
            "selection": {
                "filter": "item",
                "values": [zone_key_3_letters]
            }
        })
    json_query = {
        "query": query_list,
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


def get_capacity_data_for_zones(
    target_datetime: datetime, session: Session, zone_key: ZoneKey|None=None
) -> dict:
    """
    Get capacity data for a specific zone or all zones. The unit is the MW
    If zone_key is None, get data for all zones.
    If zone_key is not None, get data for the specific zone.
    """
    if zone_key is None:
        data = get_data_from_url(target_datetime, session)
    else:
        if pycountry.countries.get(alpha_2=zone_key) is not None:
            zone_key_3_letters = pycountry.countries.get(alpha_2=zone_key).alpha_3
        else:
            raise ValueError(f"Impossible to find the pycountry.countries 3 letters for {zone_key}")
        data = get_data_from_url(target_datetime, session, zone_key_3_letters)
    capacity_dict = {}
    for item in data:
        if pycountry.countries.get(alpha_3=item["key"][0]) is not None:
            zone = pycountry.countries.get(alpha_3=item["key"][0]).alpha_2
        else:
            pass
        if int(item["key"][1]) not in IRENA_JSON_TO_MODE_MAPPING:
            continue
        mode: str = IRENA_JSON_TO_MODE_MAPPING[int(item["key"][1])]
        value: float = float(item["values"][0] if item["values"][0] != "-" else 0)
        datetime_value: datetime = datetime.strptime(item["key"][-1], "%y")

        if zone not in capacity_dict:
            zone_dict = {
                mode: {
                    "datetime": datetime_value.strftime("%Y-%m-%d"),
                    "value": round(value,2),
                    "source": SOURCE,
                }
            }
            capacity_dict[zone] = zone_dict
        else:
            if mode in capacity_dict[zone]:
                zone_dict = capacity_dict[zone][mode]
                capacity_dict[zone][mode]["value"] += value
                capacity_dict[zone][mode]["value"] = round(capacity_dict[zone][mode]["value"], 2)
            else:
                capacity_dict[zone] = {
                    **capacity_dict[zone],
                    **{
                        mode: {
                            "datetime": datetime_value.strftime("%Y-%m-%d"),
                            "value": round(value,2),
                            "source": SOURCE,
                        }
                    },
                }
    return capacity_dict


def fetch_production_capacity(
    target_datetime: datetime, zone_key: ZoneKey, session: Session
) -> dict[str, Any] | None:
    all_capacity = get_capacity_data_for_zones(target_datetime, session, zone_key)
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
    all_capacity = get_capacity_data_for_zones(target_datetime, session)

    all_capacity = {k: v for k, v in all_capacity.items() if k in IRENA_ZONES}
    logger.info(f"Fetched capacity data from IRENA for {target_datetime.year}")
    return all_capacity
