#!/usr/bin/env python3

"""Parser for the electricity grid of Iraq"""

from datetime import datetime
from logging import Logger, getLogger

import arrow
import requests
from dateutil.tz import tz
from requests import Session

LIVE_PRODUCTION_API_URL = "https://www.gdoco.org/vueips.php"
DATA_SOURCE = "www.gdoco.org"
CELL_MAPPING = {
    "hydro": ["1220"],
    "gas": ["1219"],
    "oil": ["1218", "1221"],  # Thermal  # Diesel
}


def template_response(zone_key: str, datetime: datetime, source: str) -> dict:
    return {
        "zoneKey": zone_key,
        "datetime": datetime,
        "production": {
            "gas": 0.0,
            "hydro": 0.0,
            "oil": 0.0,
            "solar": None,  # IEA has a count, but no data is available
        },
        "storage": {},
        "source": source,
    }


def fetch_data(r: Session):
    resp = r.get(LIVE_PRODUCTION_API_URL)
    data = resp.json()

    timestamp = arrow.get(
        data["lastmodified"], "HH:mm:ss A DD-MM-YYYY", tzinfo=tz.gettz("Asia/Baghdad")
    )

    return data["d"], timestamp.datetime


def fetch_production(
    zone_key: str,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Requests the last known production mix (in MW) of a given zone."""
    if target_datetime is not None:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    r = session or requests.session()
    data, timestamp = fetch_data(r)

    result = template_response(zone_key, timestamp, DATA_SOURCE)

    for production_type, ids in CELL_MAPPING.items():
        for data_id in ids:
            result["production"][production_type] += data["d_" + data_id]

    return [result]


def fetch_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    r = session or requests.session()
    data, timestamp = fetch_data(r)

    sortedZoneKeys = "->".join(sorted([zone_key1, zone_key2]))

    if sortedZoneKeys == "IQ->IR":
        netflow = -1 * (
            data["d_1226"] + data["d_1227"] + data["d_1228"] + data["d_1229"]
        )
    elif sortedZoneKeys == "IQ->IQ-KUR":
        netflow = -1 * data["d_1230"]
    else:
        raise NotImplementedError("This exchange pair is not implemented")

    exchange = {
        "sortedZoneKeys": sortedZoneKeys,
        "datetime": timestamp,
        "netFlow": netflow,
        "source": DATA_SOURCE,
    }

    return exchange


def fetch_consumption(
    zone_key: str = "IQ",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    r = session or requests.session()

    data, timestamp = fetch_data(r)

    consumption = {
        "zoneKey": zone_key,
        "datetime": timestamp,
        "consumption": data["d_1234"],
        "source": DATA_SOURCE,
    }

    return consumption


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""
    r = requests.session()
    print(fetch_production(session=r))
    # print(fetch_production(target_datetime=arrow.get("20200220", "YYYYMMDD")))
    print(fetch_exchange("IQ", "IR", session=r))
    print(fetch_exchange("IQ", "IQ-KUR", session=r))
    print(fetch_consumption(session=r))
