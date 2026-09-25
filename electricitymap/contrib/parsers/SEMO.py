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
from electricitymap.contrib.parsers.lib.config import refetch_frequency
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


def _fetch_bm086(session: Session, target_datetime: datetime) -> list[dict]:
    """Fetches all BM-086 rows in a window around ``target_datetime``.

    A window reaching two days back covers the report's publication lag when
    fetching live data.
    """
    date_from = (target_datetime - timedelta(days=2)).strftime("%Y-%m-%dT00:00:00")
    date_to = (target_datetime + timedelta(days=1)).strftime("%Y-%m-%dT23:59:59")

    items: list[dict] = []
    page = 1
    while True:
        response = session.get(
            API_URL,
            params={
                "StartTime": f">={date_from}<={date_to}",
                "sort_by": "StartTime",
                "order_by": "ASC",
                "ParticipantName": "",
                "ResourceName": "",
                "page": page,
                "page_size": PAGE_SIZE,
            },
        )
        response.raise_for_status()
        batch = response.json().get("items", [])
        items.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
        page += 1
    return items


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: ZoneKey,
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Fetches a per-fuel production breakdown for IE or GB-NIR from SEM-O."""
    if target_datetime is None:
        target_datetime = datetime.now(tz=SEMO_TZ)

    unit_fuel = get_unit_fuel_mapping(session=session, logger=logger)
    rows = _fetch_bm086(session, target_datetime)

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
        fuel = unit_fuel.get(resource)
        if fuel is None:
            # Unit not (yet) in the registered-units list: keep it in the
            # totals as unknown rather than dropping it.
            print(
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
    for zone in (ZoneKey("IE"), ZoneKey("GB-NIR")):
        production = fetch_production(zone)
        print(f"{zone}: {production[-1] if production else 'No data'}")


if __name__ == "__main__":
    main()
