"""Ireland's production by fuel for dates SEM-O's BM-086 no longer serves, from
ENTSO-E's actual generation per unit and EirGrid's 15-minute system data.

Used by ``IE.py`` for IE between 2024-01-01 (before that, ``CSO.py``) and the
moment the live SEM-O parser took over (``IE.SEMO_FROM``, 2026-08-20 23:00 UTC).
It is never used for later dates, so measured BM-086 rows are never
overwritten. See ``IE.py`` for why each period uses its source.

Sources
-------
- **ENTSO-E A73, actual generation per generation unit** (IE control area): the
  half-hourly metered output of each large unit, with its fuel type. These are
  the same values as SEM-O's BM-086 for the units both publish (identical to
  the MWh on Aghada, Poolbeg, Edenderry, Turlough Hill, ...), but ENTSO-E only
  publishes large units: no waste-to-energy, small flexible units or batteries
  (~6% of thermal in 2026). It keeps years of history, while BM-086 only keeps
  ~2 months. One request per day.
- **EirGrid System Data, 15-minute** (``System-Data-Qtr-Hourly-<year>.xlsx``,
  linked from ``EIRGRID_REPORTS_URL``): average SCADA readings of IE total
  generation, wind, solar and batteries, the same scope as SmartGridDashboard.
  One file per year, republished about monthly with a new version suffix
  (``-v13``), so the current file name is read from the reports page.

Per half-hour (UTC, labelled at the start):

- wind, solar, batteries: EirGrid, averaged from its two 15-minute readings.
- gas, coal, oil, biomass, hydro and pumped storage (generation and pumping):
  ENTSO-E per unit.
- unknown: EirGrid's total minus everything above. It is mostly the units
  ENTSO-E does not publish (~64 MW on average in 2024), and slightly negative
  readings are set to 0. It is left out where EirGrid's total is frozen.

Half-hours missing from either source are not emitted.

Time convention
---------------
EirGrid labels each reading with the start of its period, in Irish local time,
with the UTC offset in its ``GMT Offset`` column. ENTSO-E's IE per-unit series
are labelled 30 minutes later than the period they measure: shifting them back
by 30 minutes makes biomass, hydro and pumped storage identical to BM-086
(correlation 1.0000) and to EirGrid's hydro. They are shifted here.
"""

from datetime import UTC, datetime, timedelta
from io import BytesIO
from itertools import groupby
from logging import Logger, getLogger
from re import findall
from threading import Lock

import openpyxl
from bs4 import BeautifulSoup
from requests import Session

from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
from electricitymap.contrib.lib.models.events import ProductionMix, StorageMix
from electricitymap.contrib.parsers import ENTSOE
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.types import ZoneKey

SOURCE = "eirgrid.ie,entsoe.eu"
EIRGRID_REPORTS_URL = "https://www.eirgrid.ie/grid/system-and-renewable-data-reports"
EIRGRID_FILES_URL = "https://www.eirgrid.ie/sites/default/files/publications/"
IE_DOMAIN = ENTSOE.ENTSOE_DOMAIN_MAPPINGS["IE"]
# ENTSO-E's IE per-unit series are labelled 30 minutes late (see module docstring).
ENTSOE_LABEL_SHIFT = timedelta(minutes=30)

# ENTSO-E production type -> mode. Storage (B10) is handled separately.
PSR_TO_MODE = {
    "B01": "biomass",
    "B04": "gas",
    "B05": "coal",
    "B06": "oil",
    # Peat, counted as coal as in SEMO.py.
    "B08": "coal",
    "B11": "hydro",
    "B12": "hydro",
    # Waste, as in ENTSOE.py.
    "B17": "biomass",
}
PUMPED_STORAGE = "B10"
EDENDERRY = "47W000000000086D"
MONEYPOINT = {"47W0000000000889", "47W0000000000897", "47W000000000090M"}
# Moneypoint, registered as coal, stopped burning coal on 2025-06-20 and has run
# as an oil-fired reserve since (contrib issue #8236).
MONEYPOINT_OIL_FROM = datetime(2025, 6, 20, tzinfo=UTC)
# A total identical for 2 hours is a frozen reading (see _drop_stuck_totals).
STUCK_TOTAL_HALF_HOURS = 4

_system_data: dict[int, dict[datetime, dict[str, float]]] = {}
_system_data_lock = Lock()


def _unit_mode(unit: str, psr: str, dt: datetime) -> str:
    if unit == EDENDERRY:  # Converted from peat to biomass, as in SEMO.py.
        return "biomass"
    if unit in MONEYPOINT and dt >= MONEYPOINT_OIL_FROM:
        return "oil"
    return PSR_TO_MODE.get(psr, "unknown")


def _system_data_file_name(session: Session, year: int) -> str:
    """Returns the current name of the EirGrid 15-minute file covering ``year``
    (yearly files are ``...-2025-v13.xlsx``, older ones span two years)."""
    response = session.get(EIRGRID_REPORTS_URL, timeout=60)
    response.raise_for_status()
    for name in sorted(
        set(findall(r'System-Data-Qtr-Hourly-[0-9][^"\\/<> ]*?\.xlsx', response.text))
    ):
        years = [int(y) for y in findall(r"(?<![0-9])(20[0-9]{2})(?![0-9])", name)]
        if years and min(years) <= year <= max(years):
            return name
    raise ParserException(
        "ENTSOExEIRGRID.py", f"No EirGrid 15-minute system data file for {year}"
    )


def _parse_system_data(content: bytes) -> dict[datetime, dict[str, float]]:
    """Averages the IE 15-minute readings to ``{utc_half_hour: {field: MW}}``."""
    columns = {
        "gen": "IE Generation",
        "wind": "IE Wind Generation",
        "solar": "IE Solar Generation",
        "battery": "IE Batteries",
    }
    sheet = openpyxl.load_workbook(BytesIO(content), read_only=True, data_only=True)
    rows = sheet.worksheets[0].iter_rows(values_only=True)
    header = [str(cell).strip() if cell is not None else "" for cell in next(rows)]
    index = {
        field: header.index(name) for field, name in columns.items() if name in header
    }
    time_col, offset_col = header.index("DateTime"), header.index("GMT Offset")

    readings: dict[datetime, dict[str, list[float]]] = {}
    for row in rows:
        local, offset = row[time_col], row[offset_col]
        if not isinstance(local, datetime) or not isinstance(offset, int | float):
            continue
        dt = (local - timedelta(hours=offset)).replace(tzinfo=UTC)
        half_hour = dt.replace(minute=dt.minute // 30 * 30)
        bucket = readings.setdefault(half_hour, {})
        for field, col in index.items():
            value = row[col]
            if isinstance(value, int | float):
                bucket.setdefault(field, []).append(float(value))
    data = {
        dt: {field: sum(values) / len(values) for field, values in fields.items()}
        for dt, fields in readings.items()
    }
    _drop_stuck_totals(data)
    return data


def _drop_stuck_totals(data: dict[datetime, dict[str, float]]) -> None:
    """Removes EirGrid's total where it is frozen: the same value for at least
    ``STUCK_TOTAL_HALF_HOURS`` in a row, which a real total never does (it read
    3,623.6 MW from 2025-04-16 10:00 to 2025-05-01 10:00 UTC). Those half-hours
    are still emitted, without unknown."""
    times = sorted(dt for dt in data if "gen" in data[dt])
    for _, run in groupby(times, key=lambda dt: data[dt]["gen"]):
        run = list(run)
        if len(run) >= STUCK_TOTAL_HALF_HOURS:
            for dt in run:
                del data[dt]["gen"]


def _fetch_system_data(session: Session, year: int) -> dict[datetime, dict[str, float]]:
    """Downloads and parses the EirGrid file for ``year`` once per process
    (~13 MB, ~20 s to parse)."""
    with _system_data_lock:
        if year not in _system_data:
            name = _system_data_file_name(session, year)
            response = session.get(EIRGRID_FILES_URL + name, timeout=300)
            response.raise_for_status()
            _system_data[year] = _parse_system_data(response.content)
        return _system_data[year]


def _fetch_units(session: Session, day: datetime) -> dict[datetime, dict[str, float]]:
    """ENTSO-E per-unit generation for one UTC day, summed per mode at the
    corrected (start-of-period) time. ``"pumped_storage"`` is net generation
    (negative when pumping). Returns ``{}`` when ENTSO-E has no data."""
    try:
        xml = ENTSOE.query_ENTSOE(
            session,
            {"documentType": "A73", "processType": "A16", "in_Domain": IE_DOMAIN},
            span=(timedelta(0), timedelta(days=1)),
            target_datetime=day,
        )
    except ParserException as error:
        if "No matching data found" in str(error):
            return {}
        raise

    units: dict[datetime, dict[str, float]] = {}
    soup = BeautifulSoup(xml, "html.parser", parse_only=ENTSOE.STRAINER_TIMESERIES)
    for series in soup.find_all("timeseries"):
        psr = series.find("mktpsrtype").find("psrtype").text
        unit = series.find("powersystemresources").find("mrid").text
        for point in ENTSOE._get_datetime_value_from_timeseries(
            series, "quantity", production_parsing=True
        ):
            dt = point.dt - ENTSOE_LABEL_SHIFT
            key = (
                "pumped_storage" if psr == PUMPED_STORAGE else _unit_mode(unit, psr, dt)
            )
            mix = units.setdefault(dt, {})
            mix[key] = mix.get(key, 0.0) + point.value
    return units


def fetch_production_range(
    zone_key: ZoneKey,
    session: Session,
    start: datetime,
    end: datetime,
    logger: Logger = getLogger(__name__),
) -> list:
    """Half-hourly IE production and storage between ``start`` and ``end``
    (inclusive)."""
    if zone_key != "IE":
        raise ParserException(
            "ENTSOExEIRGRID.py", f"Only IE is supported, not {zone_key}", zone_key
        )

    system: dict[datetime, dict[str, float]] = {}
    for year in range(start.year, end.year + 1):
        system |= _fetch_system_data(session, year)

    units: dict[datetime, dict[str, float]] = {}
    day = (start + ENTSOE_LABEL_SHIFT).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    while day <= end + ENTSOE_LABEL_SHIFT:
        units |= _fetch_units(session, day)
        day += timedelta(days=1)

    breakdowns = ProductionBreakdownList(logger=logger)
    for dt in sorted(set(system) & set(units)):
        if not start <= dt <= end:
            continue
        grid, plants = system[dt], dict(units[dt])
        if "wind" not in grid:
            continue
        pumped = plants.pop("pumped_storage", 0.0)
        battery = grid.get("battery") or 0.0

        production = ProductionMix()
        for mode, value in plants.items():
            production.add_value(mode, value, correct_negative_with_zero=True)
        production.add_value("wind", grid["wind"], correct_negative_with_zero=True)
        if grid.get("solar") is not None:
            production.add_value(
                "solar", grid["solar"], correct_negative_with_zero=True
            )
        measured = (
            grid["wind"]
            + (grid.get("solar") or 0.0)
            + sum(plants.values())
            + max(pumped, 0.0)
            + max(battery, 0.0)
        )
        if "gen" in grid:
            production.add_value(
                "unknown", grid["gen"] - measured, correct_negative_with_zero=True
            )

        storage = StorageMix()
        storage.add_value("hydro", -pumped)
        if grid.get("battery") is not None:
            storage.add_value("battery", -battery)

        breakdowns.append(
            zoneKey=zone_key,
            datetime=dt,
            production=production,
            storage=storage,
            source=SOURCE,
        )
    return breakdowns.to_list()
