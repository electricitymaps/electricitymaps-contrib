import calendar
from datetime import datetime
from logging import getLogger
from typing import Any

import pandas as pd
from requests import Response, Session

from electricitymap.contrib.config import ZoneKey
from parsers.EIA import REGIONS
from parsers.lib.utils import get_token

logger = getLogger(__name__)

CAPACITY_URL = "https://api.eia.gov/v2/electricity/operating-generator-capacity/data/?frequency=monthly&data[0]=nameplate-capacity-mw&facets[balancing_authority_code][]={}"
SOURCE = "EIA.gov"
US_ZONES = {key: value for key, value in REGIONS.items() if key.startswith("US-")}
TECHNOLOGY_TO_MODE = {
    "All Other": "unknown",
    "Batteries": "battery storage",
    "Coal Integrated Gasification Combined Cycle": "coal",
    "Conventional Hydroelectric": "hydro",
    "Conventional Steam Coal": "coal",
    "Flywheels": "battery storage",
    "Geothermal": "geothermal",
    "Hydroelectric Pumped Storage": "hydro storage",
    "Landfill Gas": "biomass",
    "Municipal Solid Waste": "biomass",  # or unknown?
    "Natural Gas Fired Combined Cycle": "gas",
    "Natural Gas Fired Combustion Turbine": "gas",
    "Natural Gas Internal Combustion Engine": "gas",
    "Natural Gas Steam Turbine": "gas",
    "Natural Gas with Compressed Air Storage": "gas",
    "Nuclear": "nuclear",
    "Offshore Wind Turbine": "wind",
    "Onshore Wind Turbine": "wind",
    "Other Gases": "unknown",
    "Other Natural Gas": "gas",
    "Other Waste Biomass": "biomass",
    "Petroleum Coke": "coal",
    "Petroleum Liquids": "oil",
    "Solar Photovoltaic": "solar",
    "Solar Thermal with Energy Storage": "solar",
    "Solar Thermal without Energy Storage": "solar",
    "Wood/Wood Waste Biomass": "biomass",
}


def format_capacity(df: pd.DataFrame, target_datetime: datetime) -> dict[str, Any]:
    df = df.copy()
    df = df.loc[df["statusDescription"] == "Operating"]
    df["mode"] = df["technology"].map(TECHNOLOGY_TO_MODE)
    df_aggregated = df.groupby(["mode"])[["nameplate-capacity-mw"]].sum().reset_index()
    capacity_dict = {}
    for mode in df_aggregated["mode"].unique():
        mode_dict = {}
        mode_dict["value"] = float(
            df_aggregated.loc[df_aggregated["mode"] == mode][
                "nameplate-capacity-mw"
            ].sum()
        )
        mode_dict["source"] = SOURCE
        mode_dict["datetime"] = target_datetime.strftime("%Y-%m-%d")
        capacity_dict[mode] = mode_dict
    return capacity_dict


def fetch_production_capacity(
    zone_key: ZoneKey,
    target_datetime: datetime,
    session: Session,
) -> dict[str, Any] | None:
    API_KEY = get_token("EIA_KEY")
    url_prefix = CAPACITY_URL.format(REGIONS[zone_key])
    start_date = target_datetime.strftime("%Y-%m-01")
    end_date = target_datetime.replace(
        day=calendar.monthrange(target_datetime.year, target_datetime.month)[1]
    ).strftime("%Y-%m-%d")
    url = f"{url_prefix}&api_key={API_KEY}&start={start_date}&end={end_date}&sort[0][column]=period&sort[0][direction]=desc&offset=0&length=5000"
    r: Response = session.get(url)
    json_data = r.json()

    if not json_data.get("response", {}).get("data", []) == []:
        data = pd.DataFrame(json_data["response"]["data"])
        capacity_dict = format_capacity(data, target_datetime)
        logger.info(
            f"Fetched capacity data for {zone_key} at {target_datetime.strftime('%Y-%m')}: \n{capacity_dict}"
        )
        return capacity_dict
    else:
        logger.warning(
            f"Failed to fetch capacity data for {zone_key} at {target_datetime.strftime('%Y-%m')}"
        )


def fetch_production_capacity_for_all_zones(
    target_datetime: datetime, session: Session | None = None
) -> dict[str, Any]:
    eia_capacity = {}
    if session is None:
        session = Session()
    for zone in US_ZONES:
        zone_capacity = fetch_production_capacity(zone, target_datetime, session)
        if zone_capacity:
            eia_capacity[zone] = zone_capacity
    return eia_capacity
