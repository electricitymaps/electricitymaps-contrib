from datetime import datetime, timedelta, timezone
from logging import Logger, getLogger

from requests import Session

from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
from electricitymap.contrib.lib.models.events import ProductionMix, StorageMix
from electricitymap.contrib.parsers.ENTSOE import ENTSOE_DOMAIN_MAPPINGS
from electricitymap.contrib.parsers.lib.config import refetch_frequency
from electricitymap.types import ZoneKey

BASE_URL = "https://api.opendata.esett.com"
PRODUCTION_URL = f"{BASE_URL}/EXP16/Aggregate"

IGNORED_PRODUCTION_KEYS = {"timestamp", "timestampUTC", "mba", "total"}

PRODUCTION_MAPPINGS = {
    "hydro": "hydro",
    "wind": "wind",
    "windOffshore": "wind",
    "nuclear": "nuclear",
    "solar": "solar",
    "thermal": "unknown",
    "other": "unknown",
}

STORAGE_MAPPINGS = {"energyStorage": "battery"}


@refetch_frequency(timedelta(days=3))
def fetch_production(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    session = session or Session()
    target_datetime = (target_datetime or datetime.now(timezone.utc)).astimezone(
        timezone.utc
    )

    start_time = target_datetime - timedelta(days=3)

    query_params = {
        "start": start_time.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "end": target_datetime.isoformat(timespec="milliseconds").replace(
            "+00:00", "Z"
        ),
        "resolution": "hour",
        "mba": ENTSOE_DOMAIN_MAPPINGS[zone_key],
    }

    response = session.get(PRODUCTION_URL, params=query_params)
    response.raise_for_status()

    json: list = response.json()
    production_breakdown_list = ProductionBreakdownList(logger)
    for entry in json or []:
        production_mix = ProductionMix()
        storage_mix = StorageMix()
        timestamp = datetime.fromisoformat(entry["timestampUTC"].replace("Z", "+00:00"))
        for key, value in entry.items():
            if key in IGNORED_PRODUCTION_KEYS:
                continue
            elif key in PRODUCTION_MAPPINGS:
                production_mix.add_value(PRODUCTION_MAPPINGS[key], value)
            elif key in STORAGE_MAPPINGS:
                storage_mix.add_value(STORAGE_MAPPINGS[key], value)
            else:
                logger.warning(f"Unknown production key: {key}")

        production_breakdown_list.append(
            zoneKey=zone_key,
            datetime=timestamp,
            production=production_mix,
            source="eSett",
        )
    return production_breakdown_list.to_list()


if __name__ == "__main__":
    print(fetch_production(ZoneKey("SE-SE4")))
