from datetime import datetime
from logging import getLogger
from typing import Any

import pandas as pd
from requests import Response, Session

from electricitymap.contrib.config.capacity import CAPACITY_PARSER_SOURCE_TO_ZONES
from electricitymap.types import ZoneKey

logger = getLogger(__name__)
SOURCE = "cea.nic.in"
CAPACITY_URL = "https://cea.nic.in/api/installed_capacity.php"
REGION_MAPPING = {
    "Northern": "IN-NO",
    "Western": "IN-WE",
    "Southern": "IN-SO",
    "Eastern": "IN-EA",
    "North Eastern": "IN-NE",
}
MODE_MAPPING = {
    "Coal": "coal",
    "Gas": "gas",
    "Diesel": "oil",
    "Nuclear": "nuclear",
    "Hydro": "hydro",
}
IN_ZONES = CAPACITY_PARSER_SOURCE_TO_ZONES["CEA"]

IN_STATE_TO_ZONE_MAPPING = {
    "Andhra Pradesh": "IN-SO",
    "Arunachal Pradesh": "IN-NE",
    "Assam": "IN-NE",
    "Bihar": "IN-EA",
    "Chhatisgarh": "IN-WE",
    "Goa": "IN-WE",
    "Gujarat": "IN-WE",
    "Haryana": "IN-NO",
    "Himachal Pradesh": "IN-NO",
    "Jammu & Kashmir": "IN-NO",
    "Jharkhand": "IN-EA",
    "Karnataka": "IN-SO",
    "Kerala": "IN-SO",
    "Ladakh": "IN-NO",
    "Madhya Pradesh": "IN-WE",
    "Maharashtra": "IN-WE",
    "Manipur": "IN-NE",
    "Meghalaya": "IN-NE",
    "Mizoram": "IN-NE",
    "Nagaland": "IN-NE",
    "Odisha": "IN-EA",
    "Punjab": "IN-NO",
    "Rajasthan": "IN-NO",
    "Sikkim": "IN-EA",
    "Tamil Nadu": "IN-SO",
    "Telangana": "IN-SO",
    "Tripura": "IN-NE",
    "Uttar Pradesh": "IN-NO",
    "Uttarakhand": "IN-NO",
    "West Bengal": "IN-EA",
    "Delhi": "IN-NO",
    "Pondicherry": "IN-SO",
}

MNRE_MODE_MAPPING = {
    "Small Hydro Power": "hydro",
    "Wind Power": "wind",
    "Bio Power Total": "biomass",
    "Solar Power Total": "solar",
}


def fetch_production_capacity_for_all_zones(
    target_datetime: datetime, session: Session
) -> dict[str, Any] | None:
    logger.warning(
        "Renewable capacity is not available and should be downloaded from https://mnre.gov.in/physical-progress/"
    )
    r: Response = session.get(CAPACITY_URL)
    data = r.json()
    df = pd.DataFrame(data)

    df_filtered = df.loc[df["Month"] == target_datetime.strftime("%b-%Y")].copy()
    if df_filtered.empty:
        raise logger.warning(f"No capacity data for IN zones in {target_datetime.year}")
    df_filtered["datetime"] = pd.to_datetime(df_filtered["Month"])
    df_filtered["zoneKey"] = df_filtered["Region"].map(REGION_MAPPING)
    df_filtered = df_filtered[["datetime", "zoneKey"] + list(MODE_MAPPING.keys())]

    df_filtered = df_filtered.set_index(["datetime", "zoneKey"])
    all_capacity = {}
    for idx, data in df_filtered.iterrows():
        capacity_dict = {}
        for cea_mode in data.index:
            mode = MODE_MAPPING[cea_mode]
            capacity_dict[mode] = {
                "datetime": idx[0].strftime("%Y-%m-%d"),
                "value": float(data[cea_mode]),
                "source": SOURCE,
            }
        all_capacity[idx[1]] = capacity_dict
    return all_capacity


def fetch_production_capacity(
    target_datetime: datetime, zone_key: ZoneKey, session: Session
) -> dict[str, Any] | None:
    all_capacities = fetch_production_capacity_for_all_zones(target_datetime, session)
    return all_capacities[zone_key]


# manual update, the output of the function should be added to the config file
def get_renewable_capacity(path: str, zone_key: ZoneKey | None = None) -> None:
    """Extract renewable capacity from MNRE report which then should be added to the config file"""
    df = pd.read_excel(path, skiprows=2)
    for col in df.columns:
        if "Unnamed:" in col:
            df = df.rename(columns={col: df[col].iloc[0]})
    df = df.iloc[2:]
    cols_to_keep = [
        "STATES / Uts",
        "Small Hydro Power",
        "Wind Power",
        "Bio Power Total",
        "Solar Power Total",
    ]
    df_filtered = df[cols_to_keep].copy()
    df_filtered = df_filtered.rename(
        columns={**{"STATES / Uts": "zoneKey"}, **MNRE_MODE_MAPPING}
    )
    df_filtered["zoneKey"] = df_filtered["zoneKey"].map(IN_STATE_TO_ZONE_MAPPING)
    df_filtered = df_filtered.groupby(["zoneKey"]).sum()
    all_capacity = {}
    for idx, data in df_filtered.iterrows():
        capacity_dict = {}
        for mode in data.index.sort_values():
            capacity_dict[mode] = round(data[mode], 1)
        all_capacity[idx] = capacity_dict
    if zone_key:
        return all_capacity[zone_key]
    return all_capacity


if __name__ == "__main__":
    print(
        get_renewable_capacity(
            "/Users/mathildedaugy/Downloads/202401091363179073.xlsx", "IN-SO"
        )
    )
