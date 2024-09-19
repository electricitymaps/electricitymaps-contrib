from datetime import datetime, timedelta
from typing import Any

from requests import Response, Session

from electricitymap.contrib.capacity_parsers.ENTSOE import (
    fetch_production_capacity as fetch_entsoe_production_capacity,
)
from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.parsers.lib.utils import get_token

SOURCE = "fingrid.fi"

FINGRID_URL = "https://data.fingrid.fi/api/datasets/{data_set}/data"
MODE_TO_DATASET = {"solar": 267, "wind": 268}


def get_fingrid_capacity(
    session: Session, target_datetime: datetime, mode: str
) -> dict[str, Any] | None:
    params = {
        "format": "json",
        "locale": "en",
        "pageSize": 24,
        "startTime": (target_datetime - timedelta(days=1)).strftime(
            "%Y-%m-%dT23:00:00"
        ),
        "endTime": (target_datetime + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00"),
    }
    headers = {"x-api-key": get_token("FINGRID_TOKEN")}
    r: Response = session.get(
        FINGRID_URL.format(data_set=MODE_TO_DATASET[mode]),
        params=params,
        headers=headers,
    )
    data = r.json()
    if not r.ok or "data" not in r.json():
        raise ValueError(
            f"Failed to fetch solar capacity from {FINGRID_URL} for {target_datetime.date()}"
        )
    data = r.json()["data"]
    capacity = {mode: parse_fingrid_capacity(data, target_datetime)}
    return capacity


def parse_fingrid_capacity(
    data: dict[str, Any], target_datetime: datetime
) -> list[dict[str, Any]]:
    target_data = [
        x
        for x in data
        if x["startTime"] == target_datetime.strftime("%Y-%m-%dT00:00:00.000Z")
    ]
    if len(target_data) == 0:
        raise ValueError(f"No solar capacity data found for {target_datetime.date()}")
    capacity = {
        "value": target_data[0]["value"],
        "datetime": target_datetime.strftime("%Y-%m-%d"),
        "source": SOURCE,
    }
    return capacity


def fetch_production_capacity(
    zone_key: ZoneKey, target_datetime: datetime, session: Session
) -> dict[str, Any] | None:
    solar_capacity = get_fingrid_capacity(session, target_datetime, "solar")
    wind_capacity = get_fingrid_capacity(session, target_datetime, "wind")
    entsoe_capacity = fetch_entsoe_production_capacity(
        zone_key, target_datetime, session
    )
    return {**entsoe_capacity, **solar_capacity, **wind_capacity}


if __name__ == "__main__":
    session = Session()
    target_datetime = datetime(2023, 12, 31)
    fetch_production_capacity("FI", target_datetime, session)
