"""Ireland (IE) production: picks the source for the requested dates.

SEM-O's BM-086, which ``SEMOxSMARTGRID`` uses, only keeps ~2 months, so a
refetch of older dates gets nothing from it. IE is therefore served from a
different source per period, each the best measured breakdown available for it:

=============================  ==========================================
Period (UTC)                   Source
=============================  ==========================================
2020-01-01 -> 2023-12-31       ``CSO.py``: CSO's metered generation by fuel
2024-01-01 -> ``SEMO_FROM``    ``ENTSOExEIRGRID.py``: ENTSO-E per unit +
                               EirGrid 15-minute system data
``SEMO_FROM`` (2026-08-20      ``SEMOxSMARTGRID.py``: SEM-O BM-086 +
23:00) onwards                 SmartGridDashboard
=============================  ==========================================

Why this split
--------------
- **Live: SEM-O, not ENTSO-E per unit.** ENTSO-E's per-unit data is BM-086
  republished for the large units only (identical values, labelled 30 minutes
  late), with the same ~1.5-day lag. It lacks waste-to-energy plants, small
  flexible units and every battery (~6% of thermal in Nov 2026), and misses
  whole days more often. BM-086 is complete, so it is the source wherever it
  exists.
- **A fixed cut-over, not BM-086's rolling retention.** ``SEMO_FROM`` is the
  first IE timestamp stored from BM-086. Later dates only ever come from
  SEM-O (and return nothing once beyond its retention), so a backfill never
  overwrites stored BM-086 rows with ENTSO-E's, which miss units.
- **2020-2023: CSO, not ENTSO-E per unit.** For large units the two agree
  within ~1% (same meters), but CSO is more complete: it splits waste and
  other small generators by fuel (ENTSO-E would leave them as unknown), and
  its wind and solar are metered settlement data including
  distribution-connected generation, closer to EirGrid's annual metered
  figures. CSO only covers 2020-2023 at half-hourly resolution (its 2025 table
  is hourly, and there is none for 2024).
- **2024 -> SEMO_FROM: ENTSO-E per unit + EirGrid.** No better measured source
  exists: CSO has no half-hourly table, BM-086 has expired, and ENTSO-E's
  generation per *type* (A75) for the IE control area is not usable (its
  thermal is only 57-75% of EirGrid's).

Expect small level steps at the boundaries: wind and solar move from CSO's
metered scope to EirGrid's SCADA scope at 2024-01-01 (~-3% on wind in 2023),
and storage gains pumping/charging from 2024 (CSO only reports discharge).

Each call covers ``SEMOxSMARTGRID.window``. A window crossing a boundary only
returns the older source's part; the calls for the following days cover the
rest.
"""

from datetime import UTC, datetime, timedelta
from logging import Logger, getLogger

from requests import Session

from electricitymap.contrib.parsers import CSO, ENTSOExEIRGRID, SEMOxSMARTGRID
from electricitymap.contrib.parsers.lib.config import refetch_frequency
from electricitymap.contrib.types import ZoneKey

HALF_HOUR = timedelta(minutes=30)
# First IE timestamp stored from SEM-O (midnight Irish time on 2026-08-21).
SEMO_FROM = datetime(2026, 8, 20, 23, tzinfo=UTC)


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

    if start >= SEMO_FROM:
        return SEMOxSMARTGRID.fetch_production(
            zone_key, session, target_datetime, logger
        )
    if start >= CSO.MEG01_END:
        return ENTSOExEIRGRID.fetch_production_range(
            zone_key, session, start, min(end, SEMO_FROM - HALF_HOUR), logger
        )
    return CSO.fetch_production_range(
        zone_key, session, start, min(end, CSO.MEG01_END - HALF_HOUR), logger
    )
