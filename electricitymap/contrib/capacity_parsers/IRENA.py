import json
from datetime import datetime

import pandas as pd
import pycountry
from requests import Response, Session

from electricitymap.contrib.config import ZoneKey

"""The data is downloaded from the IRENA API. """

IRENA_ZONES = ["IL", "IS", "LK", "NI", "GF", "PF"]

IRENA_JSON_TO_MODE_MAPPING = {
    0: "solar",
    1: "solar",
    2: "wind",
    3: "wind",
    4: "hydro",
    5: "hydro",
    6: "hydro storage",
    7: "unknown",
    8: "biomass",
    9: "biomass",
    10: "biomass",
    11: "biomass",
    12: "geothermal",
    13: "coal",
    14: "oil",
    15: "gas",
    16: "unknown",
    17: "nuclear",
    18: "unknown",
}

SPECIFIC_MODE_MAPPING = {"IS": {16: "oil"}}  # unknown -> oil


def get_data_from_url(target_datetime: datetime) -> list:
    base_url = (
        "https://pxweb.irena.org:443/api/v1/en/IRENASTAT/Power Capacity and Generation/"
    )
    url_year = datetime.now().year
    filename_combinations = [
        f"ELECCAP_{url_year}_cycle2.px",
        f"ELECCAP_{url_year}_cycle1.px",
        f"ELECCAP_{url_year}.px",
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
        r: Response = Session().post(url, data=json_data)
        if r.status_code == 200:
            data = r.json()
        else:
            continue
    if not data:
        raise ValueError(f"Could not fetch data for {target_datetime.year}")
    return data["data"]


def reallocate_capacity_mode(zone_key: ZoneKey, mode: int) -> dict:
    if zone_key in SPECIFIC_MODE_MAPPING:
        if mode in SPECIFIC_MODE_MAPPING[zone_key]:
            return SPECIFIC_MODE_MAPPING[zone_key][mode]
    else:
        return IRENA_JSON_TO_MODE_MAPPING[mode]


def get_capacity_data_for_all_zones(target_datetime: datetime):
    data = get_data_from_url(target_datetime)
    capacity_dict = {}
    for item in data:
        if pycountry.countries.get(alpha_3=item["key"][0]) is not None:
            zone = pycountry.countries.get(alpha_3=item["key"][0]).alpha_2
        else:
            pass
        mode = IRENA_JSON_TO_MODE_MAPPING[int(item["key"][1])]
        if zone not in capacity_dict:
            zone_dict = {
                mode: {
                    "datetime": datetime.strptime(item["key"][-1], "%y"),
                    "value": float(item["values"][0]),
                }
            }
            capacity_dict[zone] = zone_dict
        else:
            mode = reallocate_capacity_mode(zone, int(item["key"][1]))
            if mode in capacity_dict[zone]:
                zone_dict = capacity_dict[zone][mode]
                capacity_dict[zone][mode]["value"] += float(item["values"][0])
            else:
                capacity_dict[zone] = {
                    **capacity_dict[zone],
                    **{
                        mode: {
                            "datetime": datetime.strptime(item["key"][-1], "%y"),
                            "value": float(item["values"][0]),
                        }
                    },
                }
    return capacity_dict


def fetch_production_capacity(target_datetime: datetime, zone_key: ZoneKey) -> dict:
    all_capacity = get_capacity_data_for_all_zones(target_datetime)
    zone_capacity = all_capacity[zone_key]

    if zone_capacity:
        print(
            f"Fetched capacity for {zone_key} in {target_datetime.year}: \n{zone_capacity}"
        )
        return zone_capacity
    else:
        raise ValueError(f"No capacity data for {zone_key} in {target_datetime.year}")


def fetch_production_capacity_for_all_zones(target_datetime: datetime) -> dict:
    all_capacity = get_capacity_data_for_all_zones(target_datetime)

    all_capacity = {k: v for k, v in all_capacity.items() if k in IRENA_ZONES}
    print(f"Fetched capacity data from IRENA for {target_datetime.year}")
    return all_capacity


if __name__ == "__main__":
    fetch_production_capacity(datetime(2022, 1, 1), "IS")
