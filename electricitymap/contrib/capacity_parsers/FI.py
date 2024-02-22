from datetime import datetime, timedelta
from typing import Any

from requests import Response, Session

from electricitymap.contrib.capacity_parsers.ENTSOE import (
    fetch_production_capacity as fetch_entsoe_production_capacity,
)
from electricitymap.contrib.config import ZoneKey

API_KEY = "a411d83c96bb4abb8812dba80bdaed64"
SOURCE = "fingrid.fi"

FINGRID_URL = "https://data.fingrid.fi/api/datasets/267/data"

def get_solar_capacity(session: Session, target_datetime: datetime) -> dict[str, Any] | None:
    params = {
        "format": "json",
        "locale": "en",
        "pageSize":24,
        "startTime": (target_datetime - timedelta(days=1)).strftime("%Y-%m-%dT23:00:00"),
        "endTime": (target_datetime + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00"),
    }
    headers = {"x-api-key": API_KEY}
    r: Response = session.get(FINGRID_URL, params=params, headers=headers)

    if not r.ok or "data" not in r.json():
        raise ValueError(f"Failed to fetch solar capacity from {FINGRID_URL} for {target_datetime.date()}")
    data = r.json()["data"]
    solar_capacity = {"solar": parse_solar_capacity(data, target_datetime)}
    return solar_capacity


def parse_solar_capacity(
    data: dict[str, Any], target_datetime: datetime
) -> list[dict[str, Any]]:
    target_data=  [x for x in data if x["startTime"] == target_datetime.strftime("%Y-%m-%dT00:00:00.000Z")]
    if len(target_data) == 0:
        raise ValueError(f"No solar capacity data found for {target_datetime.date()}")
    solar_capacity = {
            "value": target_data[0]["value"],
            "datetime": target_datetime.strftime("%Y-%m-%d"),
            "source": SOURCE,
        }
    return solar_capacity

def fetch_production_capacity(
zone_key: ZoneKey, target_datetime: datetime, session: Session
) -> dict[str, Any] | None:
    solar_capacity = get_solar_capacity(session, target_datetime)
    entsoe_capacity = fetch_entsoe_production_capacity(zone_key, target_datetime, session)
    return {**entsoe_capacity,**solar_capacity}


if __name__ == "__main__":
    session = Session()
    target_datetime = datetime(2023,12,31)
    fetch_production_capacity("FI", target_datetime, session)

