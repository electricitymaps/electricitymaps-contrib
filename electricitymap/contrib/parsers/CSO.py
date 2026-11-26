"""Ireland's metered electricity generation by fuel, from the Central Statistics
Office (CSO), Ireland's national statistical office.

Table MEG01 "Metered Electricity Generation" gives half-hourly generation in MWh
by primary fuel for 2020-01-01 to 2023-12-31. The CSO built it from metered
microdata that EirGrid (the TSO) supplies under the Statistics Act 1993: the SEM
file (larger, transmission-connected units, 30-minute periods) and the DSO file
(smaller, distribution-connected units, 15-minute periods). Rooftop solar for
own consumption is not included. The table has not been updated since
February 2024.

- Release: https://www.cso.ie/en/statistics/energy/meteredelectricitygeneration/
- Background notes: https://www.cso.ie/en/releasesandpublications/ep/p-meg/meteredelectricitygenerationdecember2023/backgroundnotes/
- Licence: CC BY 4.0 (https://www.cso.ie/en/aboutus/whoweare/copyrightpolicy/)

The CSO does not document the time convention of the bands. The data shows it:

- 2020-2022: bands are in UTC. On spring clock-change days the DSO part is
  missing from the 01:00-02:00 bands, so those two bands are incomplete and are
  dropped.
- 2023: bands are in Irish local time. The spring 01:00-02:00 bands are empty,
  and the autumn ones hold both occurrences of the repeated hour, so each is
  split evenly across its two UTC half-hours.

Storage is discharge only: the table has no pumping or charging consumption.
"""

from datetime import UTC, datetime, timedelta
from logging import Logger, getLogger
from threading import Lock
from zoneinfo import ZoneInfo

from requests import Session

from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
from electricitymap.contrib.lib.models.events import ProductionMix, StorageMix
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.types import ZoneKey

SOURCE = "cso.ie"
MEG01_URL = "https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/MEG01/JSON-stat/2.0/en"
# First and last instants MEG01 covers (the last band of 2023-12-31, Irish winter
# time, ends at 2024-01-01 00:00 UTC).
MEG01_START = datetime(2020, 1, 1, tzinfo=UTC)
MEG01_END = datetime(2024, 1, 1, tzinfo=UTC)
# From 2023 the bands are in Irish local time instead of UTC.
LOCAL_TIME_FROM_YEAR = 2023
IE_TZ = ZoneInfo("Europe/Dublin")
# MWh per half-hour -> MW.
MWH_PER_HALF_HOUR_TO_MW = 2

FUEL_TO_MODE = {
    "Wind": "wind",
    "Solar": "solar",
    "Renewable Hydro": "hydro",
    "Gas": "gas",
    "Coal": "coal",
    "Oil": "oil",
    "Distillate": "oil",
    # Mostly Edenderry, which co-fires peat and biomass (SEMO.py also counts it
    # as biomass).
    "Biomass/Peat": "biomass",
    # Waste-to-energy plants, as in ENTSOE.py.
    "Waste": "biomass",
    # Landfill gas and biogas.
    "Other Renewable": "biomass",
    "Other Non-Renewable": "unknown",
}
FUEL_TO_STORAGE = {"Pumped Storage Hydro": "hydro", "Battery Storage": "battery"}
# Totals, not a fuel.
SKIPPED_FUELS = {"Net Generation"}

_cache: dict[str, dict[datetime, dict[str, float]]] = {}
_cache_lock = Lock()


def _band_starts_utc(day: datetime, band: str) -> list[tuple[datetime, float]]:
    """Returns ``[(utc_start, weight)]`` for the band starting at ``band``
    (``"HH:MM"``) on ``day``. An empty list drops the band; two entries split an
    ambiguous local band across both UTC half-hours."""
    naive = day + timedelta(hours=int(band[:2]), minutes=int(band[3:5]))
    roundtrip = (
        naive.replace(tzinfo=IE_TZ)
        .astimezone(UTC)
        .astimezone(IE_TZ)
        .replace(tzinfo=None)
    )
    if roundtrip != naive:
        # Inside the hour skipped by the spring clock change: missing (2023) or
        # incomplete (2020-2022).
        return []
    if day.year < LOCAL_TIME_FROM_YEAR:
        return [(naive.replace(tzinfo=UTC), 1.0)]
    first = naive.replace(tzinfo=IE_TZ, fold=0).astimezone(UTC)
    second = naive.replace(tzinfo=IE_TZ, fold=1).astimezone(UTC)
    if first == second:
        return [(first, 1.0)]
    return [(first, 0.5), (second, 0.5)]


def _parse_meg01(data: dict) -> dict[datetime, dict[str, float]]:
    """Flattens the MEG01 JSON-stat cube to ``{utc_start: {fuel: MW}}``."""
    ids, sizes, values = data["id"], data["size"], data["value"]
    if sizes[0] != 1:
        raise ValueError(f"MEG01: expected one statistic, got {sizes[0]}")
    days, bands, fuels = (
        list(data["dimension"][dim]["category"]["label"].values()) for dim in ids[1:]
    )

    parsed: dict[datetime, dict[str, float]] = {}
    for d, day_label in enumerate(days):
        day = datetime.strptime(day_label, "%Y %B %d")
        for b, band_label in enumerate(bands):
            if not band_label[:2].isdigit():  # "All time periods"
                continue
            starts = _band_starts_utc(day, band_label)
            for f, fuel in enumerate(fuels):
                value = values[(d * len(bands) + b) * len(fuels) + f]
                if value is None or fuel in SKIPPED_FUELS:
                    continue
                for dt, weight in starts:
                    mix = parsed.setdefault(dt, {})
                    mix[fuel] = (
                        mix.get(fuel, 0.0) + value * weight * MWH_PER_HALF_HOUR_TO_MW
                    )
    return parsed


def _fetch_meg01(session: Session) -> dict[datetime, dict[str, float]]:
    """Downloads and parses MEG01 once per process (~6.5 MB)."""
    with _cache_lock:
        if MEG01_URL not in _cache:
            response = session.get(MEG01_URL, timeout=120)
            response.raise_for_status()
            _cache[MEG01_URL] = _parse_meg01(response.json())
        return _cache[MEG01_URL]


def fetch_production_range(
    zone_key: ZoneKey,
    session: Session,
    start: datetime,
    end: datetime,
    logger: Logger = getLogger(__name__),
) -> list:
    """Half-hourly production and storage for IE between ``start`` and ``end``
    (inclusive), within MEG01's coverage."""
    if zone_key != "IE":
        raise ParserException("CSO.py", f"CSO only covers IE, not {zone_key}", zone_key)

    breakdowns = ProductionBreakdownList(logger=logger)
    for dt, fuels in sorted(_fetch_meg01(session).items()):
        if not start <= dt <= end:
            continue
        production = ProductionMix()
        storage = StorageMix()
        for fuel, value in fuels.items():
            if fuel in FUEL_TO_STORAGE:
                storage.add_value(FUEL_TO_STORAGE[fuel], -value)
            elif fuel in FUEL_TO_MODE:
                production.add_value(FUEL_TO_MODE[fuel], value)
            else:
                raise ParserException("CSO.py", f"Unknown MEG01 fuel: {fuel}", zone_key)
        breakdowns.append(
            zoneKey=zone_key,
            datetime=dt,
            production=production,
            storage=storage,
            source=SOURCE,
        )
    return breakdowns.to_list()
