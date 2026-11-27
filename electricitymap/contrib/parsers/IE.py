"""Ireland (IE) production: picks the source for the requested dates.

SEM-O's BM-086, which ``SEMOxSMARTGRID`` uses, only keeps ~2 months, so a
refetch of older dates gets nothing from it. Older dates come from another
measured source instead:

=============================  ==========================================
Period (UTC)                   Source
=============================  ==========================================
2020-01-01 -> 2023-12-31       ``CSO.py``: CSO's metered generation by fuel
2024-01-01 onwards             ``SEMOxSMARTGRID.py``: SEM-O BM-086 +
                               SmartGridDashboard
=============================  ==========================================
"""

from datetime import UTC, datetime, timedelta
from logging import Logger, getLogger

from requests import Session

from electricitymap.contrib.parsers import CSO, SEMOxSMARTGRID
from electricitymap.contrib.parsers.lib.config import refetch_frequency
from electricitymap.contrib.types import ZoneKey

HALF_HOUR = timedelta(minutes=30)


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: ZoneKey = ZoneKey("IE"),
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    if target_datetime is None:
        target_datetime = datetime.now(tz=UTC)
    start, end = SEMOxSMARTGRID.window(target_datetime)

    if start >= CSO.MEG01_END:
        return SEMOxSMARTGRID.fetch_production(
            zone_key, session, target_datetime, logger
        )
    # A window crossing a boundary only returns the older source's part; the
    # calls for the following days cover the rest.
    return CSO.fetch_production_range(
        zone_key, session, start, min(end, CSO.MEG01_END - HALF_HOUR), logger
    )
