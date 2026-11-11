"""Parser for the Single Electricity Market (SEM) covering Ireland (IE) and
Northern Ireland (GB-NIR).

Production is derived from SEM-O's BM-086 "Aggregated Data Report" which
publishes metered generation (MW) per registered unit for every half-hour
settlement period, tagged with a ``Jurisdiction`` (``ROI`` -> IE, ``NI`` ->
GB-NIR). BM-086 does not carry a fuel type, so each ``ResourceName`` is joined
to SEM-O's "List of Registered Units" spreadsheet to obtain its fuel type,
which is then mapped to an Electricity Maps production mode.

The registered-units list is fetched live from sem-o.com (the file is
republished periodically at a dated URL, so we discover the latest one from the
"Joining the Balancing Market" page). If it cannot be accessed the parser
raises rather than producing an unlabelled breakdown.
"""

import re
from datetime import datetime, timedelta, timezone
from io import BytesIO
from logging import Logger, getLogger
from urllib.parse import urljoin

import openpyxl
from bs4 import BeautifulSoup
from requests import Session

from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
from electricitymap.contrib.lib.models.events import ProductionMix, StorageMix
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.types import ZoneKey

# BM-086 StartTime/EndTime are expressed in UTC (confirmed by aligning against
# EirGrid's SmartGridDashboard: SEM-O timestamps sit exactly UTC behind Dublin
# local time during Irish Summer Time).
SEMO_TZ = timezone.utc
SOURCE = "sem-o.com"

API_URL = "https://reports.sem-o.com/api/v1/dynamic/BM-086"
# Page that links the current "List of Registered Units" spreadsheet.
REGISTERED_UNITS_PAGE_URL = "https://www.sem-o.com/markets/balancing-market-overview/joining-the-balancing-market"
PAGE_SIZE = 5000

JURISDICTION_TO_ZONE = {"ROI": ZoneKey("IE"), "NI": ZoneKey("GB-NIR")}

# SEM-O fuel type -> Electricity Maps production mode.
FUEL_TO_MODE = {
    "WIND": "wind",
    "SOLAR": "solar",
    "HYDRO": "hydro",
    "GAS": "gas",
    "COAL": "coal",
    "PEAT": "coal",
    "OIL": "oil",
    "DISTILLATE": "oil",
    "BIOMASS": "biomass",
    # Multi-fuel units in SEM are overwhelmingly gas-fired CCGTs (distillate is
    # only a backup fuel), so they are counted as gas rather than unknown.
    "MULTI_FUEL": "gas",
}
# Per-unit fuel overrides for units whose registered fuel type no longer matches
# what they actually burn. Applied by ResourceName before the fuel -> mode step,
# which keeps FUEL_TO_MODE generic: COAL and PEAT should never be hit anymore, so
# if a unit ever does report as coal/peat it surfaces as coal (worth a look)
# rather than being hidden. Checked against the registered-units "Unit Name".
UNIT_FUEL_OVERRIDES = {
    # Moneypoint (Ireland's last coal station) ended coal generation and now runs
    # as an oil-fired strategic reserve.
    "GU_400270": "OIL",  # Moneypoint 1
    "GU_400271": "OIL",  # Moneypoint 2
    "GU_400272": "OIL",  # Moneypoint 3
    # Edenderry converted from peat to biomass.
    "GU_401860": "BIOMASS",
}
# SEM-O fuel type -> Electricity Maps storage mode.
FUEL_TO_STORAGE = {"BATTERY": "battery", "PUMP_STORAGE": "hydro"}
# Fuels that represent no real energy output (or interconnector rows with no
# fuel) and should be ignored.
SKIPPED_FUELS = {"SYNC CONDENSER", ""}

# A registered-units file link looks like
# /sites/semo/files/2026-09/List%20of%20Registered%20Units%2023092026.xlsx
# Word separators may be spaces, %20 (URL-encoded space) or dashes.
_MAPPING_NAME_RE = re.compile(r"registered.{0,3}units", re.IGNORECASE)
_FILE_DATE_RE = re.compile(r"(\d{2})(\d{2})(\d{4})\.xlsx", re.IGNORECASE)
_MONTH_RE = re.compile(r"/files/(\d{4})-(\d{2})/")


def _normalise_fuel(fuel: str | None) -> str:
    """Upper-cases and repairs the known SEM-O ``DISTIILLATE`` typo."""
    fuel = (fuel or "").strip().upper()
    return "DISTILLATE" if fuel == "DISTIILLATE" else fuel


def parse_registered_units(rows) -> dict[str, str]:
    """Builds a ``{ResourceName: fuel_type}`` mapping from tabular rows.

    Works for both the SEM-O xlsx (via ``openpyxl``) and the bundled CSV: it
    locates the header row containing ``Resource Name`` and ``Fuel Type`` and
    reads those columns, ignoring the title/metadata rows above the header.
    """
    normalised_rows = [
        [("" if cell is None else str(cell)).strip() for cell in row] for row in rows
    ]
    header_index = next(
        (
            i
            for i, row in enumerate(normalised_rows)
            if "Resource Name" in row and "Fuel Type" in row
        ),
        None,
    )
    if header_index is None:
        raise ValueError("Could not find header row in registered units data")

    header = normalised_rows[header_index]
    name_col = header.index("Resource Name")
    fuel_col = header.index("Fuel Type")

    mapping: dict[str, str] = {}
    for row in normalised_rows[header_index + 1 :]:
        if len(row) <= max(name_col, fuel_col):
            continue
        name = row[name_col]
        if name:
            mapping[name] = _normalise_fuel(row[fuel_col])
    return mapping


def _select_latest_mapping_url(hrefs: list[str]) -> str | None:
    """Picks the most recent registered-units xlsx link from a list of hrefs.

    Links are ranked by the ``DDMMYYYY`` date embedded in the filename when
    present, falling back to the ``YYYY-MM`` folder in the path.
    """
    candidates = [
        href
        for href in hrefs
        if href.lower().endswith(".xlsx") and _MAPPING_NAME_RE.search(href)
    ]
    if not candidates:
        return None

    def sort_key(href: str) -> tuple:
        file_match = _FILE_DATE_RE.search(href)
        file_date = (
            (
                int(file_match.group(3)),
                int(file_match.group(2)),
                int(file_match.group(1)),
            )
            if file_match
            else (0, 0, 0)
        )
        month_match = _MONTH_RE.search(href)
        month = (
            (int(month_match.group(1)), int(month_match.group(2)))
            if month_match
            else (0, 0)
        )
        return (file_date, month)

    return max(candidates, key=sort_key)


def _get_latest_mapping_url(session: Session) -> str:
    response = session.get(REGISTERED_UNITS_PAGE_URL)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    hrefs = [anchor.get("href", "") for anchor in soup.find_all("a")]
    href = _select_latest_mapping_url(hrefs)
    if href is None:
        raise ValueError("No registered units file found on SEM-O page")
    return urljoin(REGISTERED_UNITS_PAGE_URL, href)


def _fetch_live_mapping(session: Session) -> dict[str, str]:
    url = _get_latest_mapping_url(session)
    response = session.get(url)
    response.raise_for_status()
    workbook = openpyxl.load_workbook(
        BytesIO(response.content), read_only=True, data_only=True
    )
    for sheet in workbook.worksheets:
        rows = list(sheet.iter_rows(values_only=True))
        if any(
            row and "Resource Name" in [str(c).strip() for c in row if c is not None]
            for row in rows
        ):
            return parse_registered_units(rows)
    raise ValueError("No registered units sheet found in xlsx")


def get_unit_fuel_mapping(
    session: Session, logger: Logger = getLogger(__name__)
) -> dict[str, str]:
    """Returns ``{ResourceName: fuel_type}`` from the live SEM-O registered
    units list, raising if it cannot be accessed."""
    try:
        return _fetch_live_mapping(session)
    except Exception as error:
        raise ParserException(
            parser="SEMO.py",
            message=f"Could not fetch the SEM-O registered units list: {error}",
        ) from error


def _fetch_bm086(
    session: Session, start_datetime: datetime, end_datetime: datetime
) -> list[dict]:
    """Fetches all BM-086 rows with a StartTime in ``[start, end]``.

    BM-086 returns one row per settlement run for each unit/half-hour (early
    runs often report 0, later runs the actual metered value, with occasional
    small corrections), in chronological order with the latest run last and no
    field distinguishing them. We keep the last row per ``(ResourceName,
    StartTime)`` so each unit is counted once at its most recent value, rather
    than summing the duplicates.
    """
    date_from = start_datetime.strftime("%Y-%m-%dT%H:%M:%S")
    date_to = end_datetime.strftime("%Y-%m-%dT%H:%M:%S")

    latest_by_unit: dict[tuple[str, str], dict] = {}
    page = 1
    while True:
        response = session.get(
            API_URL,
            params={
                "StartTime": f">={date_from}<={date_to}",
                "sort_by": "StartTime",
                "order_by": "ASC",
                "page": page,
                "page_size": PAGE_SIZE,
            },
        )
        response.raise_for_status()
        batch = response.json().get("items", [])
        for item in batch:
            latest_by_unit[item["ResourceName"], item["StartTime"]] = item
        if len(batch) < PAGE_SIZE:
            break
        page += 1
    return list(latest_by_unit.values())


def fetch_production_range(
    zone_key: ZoneKey,
    session: Session,
    start_datetime: datetime,
    end_datetime: datetime,
    logger: Logger = getLogger(__name__),
) -> list:
    """Per-fuel production breakdown for IE or GB-NIR, for every half-hour whose
    StartTime is within ``[start_datetime, end_datetime]``.

    SEM-O is only consumed by the SEMOxSMARTGRID parser, which owns the query
    window and passes it here (and to SmartGridDashboard) so the two sources
    always cover the same range. The range is explicit rather than derived from
    a target datetime so the window lives in one place and cannot drift.
    """
    unit_fuel = get_unit_fuel_mapping(session=session, logger=logger)
    rows = _fetch_bm086(session, start_datetime, end_datetime)

    production_mixes: dict[datetime, ProductionMix] = {}
    storage_mixes: dict[datetime, StorageMix] = {}
    unmapped_units: set[str] = set()

    for item in rows:
        # Interconnector units are exchanges, not production.
        if item.get("ResourceType") == "IU":
            continue
        if JURISDICTION_TO_ZONE.get(item.get("Jurisdiction")) != zone_key:
            continue
        value = item.get("MeteredMW")
        if value is None:
            continue

        resource = item.get("ResourceName")
        fuel = UNIT_FUEL_OVERRIDES.get(resource) or unit_fuel.get(resource)
        if fuel is None:
            # Unit not (yet) in the registered-units list: keep it in the
            # totals as unknown rather than dropping it.
            logger.warning(
                f"Resource {resource} not found in registered units list, value {value}"
            )
            unmapped_units.add(resource)
        elif fuel in SKIPPED_FUELS:
            continue

        dt = datetime.strptime(item["StartTime"], "%Y-%m-%dT%H:%M:%S").replace(
            tzinfo=SEMO_TZ
        )

        if fuel in FUEL_TO_STORAGE:
            storage = storage_mixes.setdefault(dt, StorageMix())
            # BM-086 MeteredMW is positive when generating (discharging) and
            # negative when charging; StorageMix uses the opposite sign.
            storage.add_value(FUEL_TO_STORAGE[fuel], -value)
        else:
            # Unmapped units (fuel is None) and fuels without an explicit
            # production mode both fall through to unknown.
            mode = FUEL_TO_MODE.get(fuel, "unknown")
            mix = production_mixes.setdefault(dt, ProductionMix())
            mix.add_value(mode, value, correct_negative_with_zero=True)

    if unmapped_units:
        logger.warning(
            f"SEMO: {len(unmapped_units)} unit(s) missing from the registered "
            f"units list were counted as unknown: {sorted(unmapped_units)}"
        )

    production = ProductionBreakdownList(logger=logger)
    for dt in sorted(set(production_mixes) | set(storage_mixes)):
        production.append(
            zoneKey=zone_key,
            production=production_mixes.get(dt, ProductionMix()),
            storage=storage_mixes.get(dt),
            datetime=dt,
            source=SOURCE,
        )
    return production.to_list()


def main():
    """Fetches and prints the latest production breakdown for IE and GB-NIR."""
    now = datetime.now(tz=SEMO_TZ)
    start = (now - timedelta(days=2)).replace(hour=0, minute=0, second=0, microsecond=0)
    end = now
    for zone in (ZoneKey("IE"), ZoneKey("GB-NIR")):
        production = fetch_production_range(zone, Session(), start, end)
        print(f"{zone}: {production[-1] if production else 'No data'}")


if __name__ == "__main__":
    main()
