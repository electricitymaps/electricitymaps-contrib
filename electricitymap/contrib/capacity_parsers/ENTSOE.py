from datetime import datetime
from logging import getLogger
from typing import Any

from bs4 import BeautifulSoup
from requests import Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.config.capacity import CAPACITY_PARSER_SOURCE_TO_ZONES
from electricitymap.contrib.parsers.ENTSOE import (
    ENTSOE_DOMAIN_MAPPINGS,
    ENTSOE_PARAMETER_BY_GROUP,
    query_ENTSOE,
)

"""
Update capacity configurations for ENTOS-E zones for a chosen year.
"""
logger = getLogger(__name__)
SOURCE = "entsoe.eu"

ENDPOINT = "/api"
ENTSOE_HOST = "https://web-api.tp.entsoe.eu"


EU_PROXY = "https://eu-proxy-jfnx5klx2a-ew.a.run.app{endpoint}?host={host}"

ENTSOE_ENDPOINT = ENTSOE_HOST + ENDPOINT
ENTSOE_EU_PROXY_ENDPOINT = EU_PROXY.format(endpoint=ENDPOINT, host=ENTSOE_HOST)


ENTSOE_ZONES = CAPACITY_PARSER_SOURCE_TO_ZONES["ENTSOE"]

# ENTSOE does not have battery storage capacity and the data needs to be collected from other sources for the following zones
# TODO monitor this list and update if necessary
ZONES_WITH_BATTERY_STORAGE = ["FR"]


# reallocate B10 to hydro storage
ENTSOE_CODE_TO_EM_MAPPING = ENTSOE_PARAMETER_BY_GROUP.copy()
ENTSOE_CODE_TO_EM_MAPPING.update({"B10": "hydro storage", "B25": "battery storage"})


def query_capacity(
    in_domain: str, session: Session, target_datetime: datetime
) -> str | None:
    params = {
        "documentType": "A68",
        "processType": "A33",
        "in_Domain": in_domain,
    }
    return query_ENTSOE(
        session,
        params,
        target_datetime=target_datetime,
        span=(0, 72),  # DO NOT USE A NEGATIVE LOOKBACK
        function_name=query_capacity.__name__,
    )


def fetch_production_capacity(
    zone_key: ZoneKey, target_datetime: datetime, session: Session
) -> dict[str, Any] | None:
    xml_str = query_capacity(ENTSOE_DOMAIN_MAPPINGS[zone_key], session, target_datetime)
    soup = BeautifulSoup(xml_str, "html.parser")
    # Each time series is dedicated to a different fuel type.
    capacity_dict = {}
    for timeseries in soup.find_all("timeseries"):
        fuel_code = str(
            timeseries.find_all("mktpsrtype")[0].find_all("psrtype")[0].contents[0]
        )
        point = timeseries.find_all("point")
        value = float(point[0].find_all("quantity")[0].contents[0])
        if ENTSOE_CODE_TO_EM_MAPPING[fuel_code] not in capacity_dict:
            capacity_dict[ENTSOE_CODE_TO_EM_MAPPING[fuel_code]] = {
                "value": 0,
                "datetime": f"{target_datetime.year}-01-01",
                "source": SOURCE,
            }
        capacity_dict[ENTSOE_CODE_TO_EM_MAPPING[fuel_code]]["value"] += value
    if capacity_dict:
        logger.info(
            f"Capacity data for {zone_key} on {target_datetime.date()}: \n{capacity_dict}"
        )
        if zone_key in ZONES_WITH_BATTERY_STORAGE:
            logger.info(
                f"\n\n Warning: {zone_key} has battery storage, data source can be found on the contrib wiki \n\n"
            )
        return capacity_dict
    else:
        logger.warning(
            f"Failed to fecth capacity data for {zone_key} on {target_datetime.date()}"
        )


def fetch_production_capacity_for_all_zones(
    target_datetime: datetime, session: Session | None = None
) -> dict[str, Any]:
    capacity_dict = {}
    if session is None:
        session = Session()

    for zone in ENTSOE_ZONES:
        try:
            zone_capacity = fetch_production_capacity(zone, target_datetime, session)
            capacity_dict[zone] = zone_capacity
        except Exception:
            logger.warning(
                f"Failed to update capacity for {zone} on {target_datetime.date()}"
            )
            continue
    return capacity_dict


if __name__ == "__main__":
    fetch_production_capacity("FR", datetime(2023, 1, 1), Session())
