#!/usr/bin/env python3


from datetime import datetime
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

import arrow
import requests
from requests import Session

GENERATION_URL = "https://sldcapi.pstcl.org/wsDataService.asmx/pbGenData2"
DATE_URL = "https://sldcapi.pstcl.org/wsDataService.asmx/dynamicData"

GENERATION_MAPPING = {
    "totalHydro": "hydro",
    "totalThermal": "coal",
    "totalIpp": "coal",
    "resSolar": "solar",
    "resNonSolar": "biomass",
}


def calculate_average_timestamp(timestamps):
    """Takes a list of string timestamps and returns the average as an arrow object."""
    arrow_timestamps = [
        arrow.get(ts, tzinfo="Asia/Kolkata") for ts in timestamps if ts is not None
    ]
    unix_timestamps = [ts.timestamp for ts in arrow_timestamps]
    average_timestamp = sum(unix_timestamps) / len(unix_timestamps)
    arr_average_timestamp = arrow.get(average_timestamp).to("Asia/Kolkata")

    return arr_average_timestamp


def fetch_production(
    zone_key: str = "IN-PB",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Requests the last known production mix (in MW) of a given zone."""
    if target_datetime:
        raise NotImplementedError(
            "The IN-PB production parser is not yet able to parse past dates"
        )

    s = session or Session()
    data_req = s.get(GENERATION_URL)
    timestamp_req = s.get(DATE_URL)

    raw_data = data_req.json()
    timestamp_data = timestamp_req.json()

    data = {
        "zoneKey": zone_key,
        "datetime": arrow.get(
            timestamp_data["updateDate"], "DD-MM-YYYY HH:mm:ss", tzinfo="Asia/Kolkata"
        ).datetime,
        "production": {
            "hydro": 0.0,
            "coal": 0.0,
            "biomass": 0.0,
            "solar": 0.0,
        },
        "storage": {},
        "source": "punjasldc.org",
    }

    for from_key, to_key in GENERATION_MAPPING.items():
        data["production"][to_key] += max(0, raw_data[from_key]["value"])

    return [data]


def fetch_consumption(
    zone_key: str = "IN-PB",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """Requests the last known consumption (in MW) of a given zone."""
    if target_datetime:
        raise NotImplementedError(
            "The IN-PB consumption parser is not yet able to parse past dates"
        )

    s = session or requests.Session()
    req = s.get(GENERATION_URL)
    raw_data = req.json()

    consumption = float(raw_data["grossGeneration"]["value"])

    data = {
        "zoneKey": zone_key,
        "datetime": datetime.now(tz=ZoneInfo("Asia/Kolkata")),
        "consumption": consumption,
        "source": "punjasldc.org",
    }

    return data


if __name__ == "__main__":
    print(fetch_production("IN-PB"))
    print(fetch_consumption("IN-PB"))
