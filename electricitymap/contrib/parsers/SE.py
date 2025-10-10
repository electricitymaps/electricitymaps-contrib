"""
Poor mans parser timeboxing for Sweden subzones.
"""

from datetime import datetime, timedelta, timezone
from logging import Logger, getLogger

from requests import Session

from electricitymap.contrib.lib.types import ZoneKey
from electricitymap.contrib.parsers.ENTSOE import (
    fetch_production as fetch_production_enstoe,
)
from electricitymap.contrib.parsers.eSett import (
    fetch_production as fetch_production_esett,
)
from electricitymap.contrib.parsers.lib.config import refetch_frequency


@refetch_frequency(timedelta(days=3))
def fetch_production(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    assert zone_key in {
        ZoneKey("SE-SE1"),
        ZoneKey("SE-SE2"),
        ZoneKey("SE-SE3"),
        ZoneKey("SE-SE4"),
    }, f"Zone {zone_key} is not supported by the SE parser."
    target_datetime = (target_datetime or datetime.now(timezone.utc)).astimezone(
        timezone.utc
    )

    if target_datetime < datetime(2022, 1, 1, tzinfo=timezone.utc):
        return fetch_production_esett(zone_key, session, target_datetime, logger)
    else:
        return fetch_production_enstoe(zone_key, session, target_datetime, logger)
