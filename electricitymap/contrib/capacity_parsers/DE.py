from datetime import datetime
from logging import INFO, basicConfig, getLogger
from typing import Any

from requests import Response, Session

from electricitymap.contrib.config import ZoneKey

logger = getLogger(__name__)
basicConfig(level=INFO)

MODE_MAPPING = {
    "Nuclear": "nuclear",
    "Fossil brown coal / lignite": "coal",
    "Fossil hard coal": "coal",
    "Fossil gas": "gas",
    "Fossil oil": "oil",
    "Other, non-renewable": "unknown",
    "Hydro Run-of-River": "hydro",
    "Hydro pumped storage": "hydro storage",
    "Battery Storage (Power)": "battery storage",
    "Biomass": "biomass",
    "Wind onshore": "wind",
    "Wind offshore": "wind",
    "Solar": "solar",
}

SOURCE = "Fraunhofer ISE"

REQUEST_URL = "https://api.energy-charts.info/installed_power?country=de&time_step=yearly&installation_decommission=false"
CONVERT_GW_TO_MW = 1000


def convert_to_mw(value: float | int | None) -> float:
    if isinstance(value, int | float):
        return float(value) * CONVERT_GW_TO_MW
    else:
        return None


def fetch_production_capacity(
    zone_key: ZoneKey, target_datetime: datetime, session: Session
) -> dict[str, Any] | None:
    r: Response = session.get(REQUEST_URL)
    if not r.ok:
        raise ValueError(
            f"Failed to fetch capacity data for DE at {target_datetime.date()}"
        )
    data = r.json()
    all_capacity = {}
    for i in range(len(data["production_types"])):
        capacity_mode = {}
        mode = data["production_types"][i]["name"]
        for j in range(len(data["time"])):
            capacity_mode[int(data["time"][j])] = convert_to_mw(
                data["production_types"][i]["data"][j]
            )

        all_capacity[mode] = capacity_mode

    capacity = update_capacity_breakdown(all_capacity, target_datetime)

    logger.info(
        f"Fetched capacity for {zone_key} on {target_datetime.date()}: \n {capacity}"
    )
    return capacity


def update_capacity_breakdown(
    all_capacity: dict[str, Any], target_datetime: datetime
) -> dict[str, Any]:
    capacity = {}

    for mode, capacity_data in all_capacity.items():
        mapped_mode = MODE_MAPPING.get(mode)
        if mode not in MODE_MAPPING:
            continue
        if mapped_mode in capacity:
            capacity[mapped_mode]["value"] += round(
                capacity_data[target_datetime.year], 0
            )
        else:
            capacity[mapped_mode] = {
                "datetime": target_datetime.strftime("%Y-%m-%d"),
                "value": round(capacity_data[target_datetime.year], 0),
                "source": SOURCE,
            }

    return capacity


if __name__ == "__main__":
    fetch_production_capacity(ZoneKey("DE"), datetime(2023, 1, 1), Session())
