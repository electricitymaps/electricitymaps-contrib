from datetime import datetime
from logging import getLogger
from typing import Any

import pandas as pd
from requests import Response, Session

from electricitymap.contrib.config import ZoneKey
from parsers.lib.utils import get_token
from parsers.OPENNEM import ZONE_KEY_TO_REGION

"""Disclaimer: only works for real-time data. There is retired capacity included but we do not have the information on when the capacity was retired."""
logger = getLogger(__name__)
REGION_MAPPING = {
    ZONE_KEY_TO_REGION[key]: key for key in ZONE_KEY_TO_REGION
}  # NT only has solar capacity so it will be excluded

FUEL_MAPPING = {
    "wind": "wind",
    "solar_rooftop": "solar",
    "battery_charging": "battery storage",
    "solar_utility": "solar",
    "coal_black": "coal",
    "battery_discharging": "battery storage",
    "pumps": "hydro storage",
    "gas_steam": "gas",
    "gas_ocgt": "gas",
    "hydro": "hydro",
    "coal_brown": "coal",
    "distillate": "oil",
    "bioenergy_biogas": "biomass",
    "gas_ccgt": "gas",
    "gas_wcmg": "gas",
    "gas_recip": "gas",
    "bioenergy_biomass": "biomass",
}

CAPACITY_URL = "https://api.openelectricity.org.au/v4/facilities/"
SOURCE = "https://openelectricity.org.au/"


def get_openelectricity_capacity_data(session: Session) -> pd.DataFrame:
    token = get_token("OPENELECTRICITY_TOKEN")
    headers = {"Authorization": f"Bearer {token}"}
    r: Response = session.request("GET", CAPACITY_URL, headers=headers)
    data = r.json()
    result = []

    time_stamp = data.get("created_at")

    for entry in data.get("data", []):
        region = entry.get("network_region")

        for unit in entry.get("units", []):
            if unit.get("dispatch_type") != "GENERATOR":
                continue

            if unit.get("status_id") != "operating":
                continue

            transformed = {
                "zone_key": region,
                "value": unit.get("capacity_registered"),
                "mode": unit.get("fueltech_id"),
                "datetime": time_stamp,
            }
            result.append(transformed)

    capacity_df = pd.DataFrame(result)
    capacity_df["datetime"] = capacity_df["datetime"].apply(
        lambda x: pd.to_datetime(x).replace(
            month=1, day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=None
        )
    )

    return capacity_df


def filter_capacity_data_by_datetime(
    data: pd.DataFrame, target_datetime: datetime
) -> pd.DataFrame:
    """Filter capacity data by datetime. For a given target_datetime, the capacity should only include plants created before then."""
    df = data.copy()
    max_datetime = df["datetime"].max()
    min_datetime = df["datetime"].min()

    if target_datetime >= max_datetime:
        df = df.copy()
    elif target_datetime <= min_datetime:
        df = df.loc[
            df["datetime"] == min_datetime
        ].copy()  # we backfill the capacity data using the first data point
    else:
        df = df.loc[df["datetime"] <= target_datetime]
    return df


def fetch_production_capacity_for_all_zones(
    target_datetime: datetime, session: Session | None = None
) -> dict[str, Any]:
    session = session or Session()
    capacity_df = get_openelectricity_capacity_data(session)
    capacity_df = filter_capacity_data_by_datetime(capacity_df, target_datetime)

    capacity_df["zone_key"] = capacity_df["zone_key"].map(REGION_MAPPING)
    capacity_df["mode"] = capacity_df["mode"].map(FUEL_MAPPING)

    capacity_df = (
        capacity_df.groupby(["zone_key", "mode"])[["value"]].sum().reset_index()
    )

    capacity_df = capacity_df.dropna(subset=["value"])

    capacity = {}
    for zone in capacity_df["zone_key"].unique():
        zone_capacity_df = capacity_df.loc[capacity_df["zone_key"] == zone]
        zone_capacity = {}
        for _idx, data in zone_capacity_df.iterrows():
            zone_capacity[data["mode"]] = {
                "datetime": target_datetime.strftime("%Y-%m-%d"),
                "value": round(data["value"], 2),
                "source": SOURCE,
            }
        capacity[zone] = zone_capacity
    return capacity


def fetch_production_capacity(
    zone_key: ZoneKey, target_datetime: datetime, session: Session | None = None
) -> dict[str, Any] | None:
    session = session or Session()
    capacity = fetch_production_capacity_for_all_zones(target_datetime, session)[
        zone_key
    ]
    if capacity:
        logger.info(
            f"Updated capacity for {zone_key} in {target_datetime}: \n{capacity}"
        )
        return capacity
    else:
        logger.error(f"No capacity data for {zone_key} in {target_datetime}")


def get_solar_capacity_au_nt(target_datetime: datetime) -> float | None:
    """Get solar capacity for AU-NT."""
    session = Session()
    capacity_df = get_openelectricity_capacity_data(session)
    capacity_df = filter_capacity_data_by_datetime(capacity_df, target_datetime)

    capacity_df = capacity_df.loc[capacity_df["zone_key"] == "NT1"]
    capacity_df["zone_key"] = "AU-NT"

    capacity_df["mode"] = capacity_df["mode"].map(FUEL_MAPPING)

    capacity_df = (
        capacity_df.groupby(["zone_key", "mode"])[["value"]].sum().reset_index()
    )

    solar_capacity = capacity_df.get("value")
    if solar_capacity is not None:
        return round(solar_capacity.values[0], 0)
    else:
        logger.error(f"No capacity data for AU-NT in {target_datetime.date()}")


if __name__ == "__main__":
    session = Session()

    print(fetch_production_capacity("AU-QLD", datetime(2025, 1, 1), session))
    # print(fetch_production_capacity("AU-VIC", datetime(2015, 1, 1), Session()))
    # print(get_solar_capacity_au_nt(datetime(2021, 1, 1)))
