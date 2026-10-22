import calendar
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from logging import getLogger
from typing import Any

import pandas as pd
from requests import Response, Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.config.capacity import CAPACITY_PARSER_SOURCE_TO_ZONES
from electricitymap.contrib.config.constants import PRODUCTION_MODES
from electricitymap.contrib.parsers.EIA import REGIONS
from electricitymap.contrib.parsers.lib.session import mount_retry
from electricitymap.contrib.parsers.lib.utils import get_token

logger = getLogger(__name__)

CAPACITY_URL = "https://api.eia.gov/v2/electricity/operating-generator-capacity/data/?frequency=monthly&data[0]=nameplate-capacity-mw&facets[balancing_authority_code][]={}"
SOURCE = "EIA.gov"
PAGE_SIZE = 5000
TIMEOUT_SECONDS = 120
# Responses take tens of seconds each, so zones are fetched concurrently.
MAX_WORKERS = 8
US_ZONES = CAPACITY_PARSER_SOURCE_TO_ZONES["EIA"]
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
    "Other Gases": "gas",
    "Other Natural Gas": "gas",
    "Other Waste Biomass": "biomass",
    "Petroleum Coke": "oil",
    "Petroleum Liquids": "oil",
    "Solar Photovoltaic": "solar",
    "Solar Thermal with Energy Storage": "solar",
    "Solar Thermal without Energy Storage": "solar",
    "Wood/Wood Waste Biomass": "biomass",
}
CAPACITY_MODES = PRODUCTION_MODES + ["hydro storage", "battery storage"]


def format_capacity(df: pd.DataFrame, target_datetime: datetime) -> dict[str, Any]:
    df = df.copy()
    df = df.loc[df["statusDescription"] == "Operating"]
    df["mode"] = df["technology"].map(TECHNOLOGY_TO_MODE)
    df["nameplate-capacity-mw"] = pd.to_numeric(
        df["nameplate-capacity-mw"], errors="coerce"
    )
    df_aggregated = df.groupby(["mode"])[["nameplate-capacity-mw"]].sum().reset_index()
    capacity_dict = {}
    for mode in CAPACITY_MODES:
        mode_dict = {}
        mode_dict["value"] = round(
            float(
                df_aggregated.loc[df_aggregated["mode"] == mode][
                    "nameplate-capacity-mw"
                ].sum()
            ),
            1,
        )
        mode_dict["source"] = SOURCE
        mode_dict["datetime"] = target_datetime.strftime("%Y-%m-%d")
        capacity_dict[mode] = mode_dict
    return capacity_dict


def _fetch_all_pages(url: str, session: Session) -> list[dict[str, Any]]:
    """Fetch every page of an EIA v2 query.

    Raises on HTTP errors and on error payloads, so that a failed request is
    not mistaken for a month without data.
    """
    rows: list[dict[str, Any]] = []
    while True:
        r: Response = session.get(
            f"{url}&offset={len(rows)}&length={PAGE_SIZE}", timeout=TIMEOUT_SECONDS
        )
        r.raise_for_status()
        json_data = r.json()
        if "response" not in json_data:
            raise ValueError(f"Unexpected EIA response: {json_data}")
        page = json_data["response"].get("data", [])
        rows.extend(page)
        if not page or len(rows) >= int(json_data["response"].get("total", 0)):
            return rows


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
    url = f"{url_prefix}&api_key={API_KEY}&start={start_date}&end={end_date}&sort[0][column]=period&sort[0][direction]=desc"
    rows = _fetch_all_pages(url, session)

    if rows:
        data = pd.DataFrame(rows)
        capacity_dict = format_capacity(data, target_datetime)
        logger.info(
            f"Fetched capacity data for {zone_key} at {target_datetime.strftime('%Y-%m')}: \n{capacity_dict}"
        )
        return capacity_dict
    else:
        logger.warning(
            f"No capacity data for {zone_key} at {target_datetime.strftime('%Y-%m')}"
        )


def fetch_production_capacity_for_all_zones(
    target_datetime: datetime, session: Session | None = None
) -> dict[str, Any]:
    session = mount_retry(session or Session())

    def _fetch_zone(zone: ZoneKey) -> dict[str, Any] | None:
        try:
            return fetch_production_capacity(zone, target_datetime, session)
        except Exception as e:
            logger.error(
                f"Error fetching production capacity for {zone} at {target_datetime.strftime('%Y-%m')}: {e}"
            )

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        zone_capacities = executor.map(_fetch_zone, US_ZONES)
    return {
        zone: zone_capacity
        for zone, zone_capacity in zip(US_ZONES, zone_capacities, strict=True)
        if zone_capacity
    }
