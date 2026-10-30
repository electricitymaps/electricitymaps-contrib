import re
from collections import defaultdict
from datetime import date, datetime, timezone
from io import BytesIO
from logging import getLogger
from typing import Any
from urllib.parse import urljoin

import pdfplumber
from bs4 import BeautifulSoup
from requests import Session

from electricitymap.contrib.config.capacity import CAPACITY_PARSER_SOURCE_TO_ZONES
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.types import ZoneKey

logger = getLogger(__name__)
SOURCE = "cea.nic.in"
CEA_URL = "https://cea.nic.in"
# Monthly "Installed Capacity" reports (Reports > Monthly Reports > Installed Capacity)
REPORTS_URL = f"{CEA_URL}/reports/dashboardView"
REPORTS_PARAMS = {
    "headingId": 107,
    "subHeadingId": 1003,
    "subSubHeadingId": 10014,
    "lang": "en",
}
REGION_MAPPING = {
    "Northern Region": "IN-NO",
    "Western Region": "IN-WE",
    "Southern Region": "IN-SO",
    "Eastern Region": "IN-EA",
    "North Eastern Region": "IN-NE",
}
# Lignite is reported separately from coal by CEA. Renewables other than large
# hydro are only reported as a single "RES (MNRE)" total, so they come from MNRE.
MODE_MAPPING = {
    "Coal": "coal",
    "Lignite": "coal",
    "Gas": "gas",
    "Diesel": "oil",
    "Nuclear": "nuclear",
    "Hydro": "hydro",
}
IN_ZONES = CAPACITY_PARSER_SOURCE_TO_ZONES["CEA"]

MNRE_SOURCE = "mnre.gov.in"
# Only the latest state-wise report is published, there is no history
MNRE_URL = "https://mnre.gov.in/en/physical-progress/"
MNRE_REPORT_LABEL = "State wise RE Installed Capacity"
# Hydro combines CEA large hydro for the target month with MNRE small hydro from
# the latest report, which is only accurate when the two are close in time
MAX_HYDRO_MONTHS_APART = 2
MNRE_MODE_MAPPING = {
    "Small Hydro Power": "hydro",
    "Wind Power": "wind",
    "Bio Power Total": "biomass",
    "Solar Power Total": "solar",
}

IN_STATE_TO_ZONE_MAPPING = {
    "Andhra Pradesh": "IN-SO",
    "Arunachal Pradesh": "IN-NE",
    "Assam": "IN-NE",
    "Bihar": "IN-EA",
    "Chhattisgarh": "IN-WE",
    "Goa": "IN-WE",
    "Gujarat": "IN-WE",
    "Haryana": "IN-NO",
    "Himachal Pradesh": "IN-NO",
    "Jammu & Kashmir": "IN-NO",
    "Jharkhand": "IN-EA",
    "Karnataka": "IN-SO",
    "Kerala": "IN-SO",
    "Ladakh": "IN-NO",
    "Madhya Pradesh": "IN-WE",
    "Maharashtra": "IN-WE",
    "Manipur": "IN-NE",
    "Meghalaya": "IN-NE",
    "Mizoram": "IN-NE",
    "Nagaland": "IN-NE",
    "Odisha": "IN-EA",
    "Punjab": "IN-NO",
    "Rajasthan": "IN-NO",
    "Sikkim": "IN-EA",
    "Tamil Nadu": "IN-SO",
    "Telangana": "IN-SO",
    "Tripura": "IN-NE",
    "Uttar Pradesh": "IN-NO",
    "Uttarakhand": "IN-NO",
    "West Bengal": "IN-EA",
    "Delhi": "IN-NO",
    "Puducherry": "IN-SO",
    "Chandigarh": "IN-NO",
    "Dadra & Nagar Haveli and Daman & Diu": "IN-WE",
}
# The islands are not connected to the IN zones, "Others" has no location
STATES_OUTSIDE_ZONES = {"Andaman & Nicobar Islands", "Lakshadweep", "Others"}


def _normalise(cell: str | None) -> str:
    return " ".join((cell or "").split())


def _download_pdf(url: str, session: Session) -> bytes:
    r = session.get(url)
    r.raise_for_status()
    if not r.content.startswith(b"%PDF"):
        raise ParserException("CEA.py", f"Report at {url} is not a PDF")
    return r.content


def _find_table(pdf: bytes, first_cell: str) -> list[list[str | None]]:
    """Return the first table in the PDF with a row starting with first_cell."""
    with pdfplumber.open(BytesIO(pdf)) as document:
        for page in document.pages:
            for table in page.extract_tables():
                if any(row[0] == first_cell for row in table):
                    return table
    raise ParserException("CEA.py", f"No table with a {first_cell!r} row in report")


def get_report_url(target_datetime: datetime, session: Session) -> str:
    """Find the PDF report for the month of target_datetime on the CEA reports page."""
    r = session.get(REPORTS_URL, params=REPORTS_PARAMS)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    month = target_datetime.strftime("%Y-%m")
    row = soup.find("tr", attrs={"data-date": month})
    link = row and row.find("a", href=re.compile("/download-pdf/"))
    if not link:
        raise ParserException(
            "CEA.py", f"No installed capacity report for IN zones in {month}"
        )
    return urljoin(CEA_URL, link["href"])


def parse_regional_capacity(pdf: bytes) -> dict[str, dict[str, float]]:
    """
    Parse the "All India installed capacity of power stations" table from a CEA
    monthly report and return the capacity per region and CEA mode in MW.
    """
    table = _find_table(pdf, "Region")

    # The mode names are spread over several header rows
    header_end = next(i for i, row in enumerate(table) if row[1] == "State")
    columns = {
        cell: idx
        for row in table[:header_end]
        for idx, cell in enumerate(row)
        if cell in MODE_MAPPING
    }

    # The region name spans several rows of its block, which ends with "Sub Total"
    capacity = {}
    region_parts = []
    for row in table[header_end:]:
        if row[0]:
            region_parts.append(row[0])
        if row[1] == "Sub Total":
            capacity[" ".join(region_parts)] = {
                mode: float(row[idx].replace(",", "")) for mode, idx in columns.items()
            }
            region_parts = []
    return capacity


def fetch_cea_capacity(
    target_datetime: datetime, session: Session
) -> dict[ZoneKey, dict[str, float]]:
    """Fetch conventional and large hydro capacity per zone and mode in MW."""
    pdf = _download_pdf(get_report_url(target_datetime, session), session)
    regional_capacity = parse_regional_capacity(pdf)

    missing_regions = set(REGION_MAPPING) - set(regional_capacity)
    if missing_regions:
        raise ParserException(
            "CEA.py", f"Regions missing from capacity report: {missing_regions}"
        )

    capacity = {}
    for region, zone_key in REGION_MAPPING.items():
        zone_capacity = defaultdict(float)
        for cea_mode, value in regional_capacity[region].items():
            zone_capacity[MODE_MAPPING[cea_mode]] += value
        capacity[ZoneKey(zone_key)] = dict(zone_capacity)
    return capacity


def parse_state_capacity(pdf: bytes) -> tuple[date, dict[ZoneKey, dict[str, float]]]:
    """
    Parse the MNRE state-wise renewable capacity table and return its "as on"
    date and the capacity per zone and mode in MW.
    """
    table = _find_table(pdf, "S. No.")

    title = next(
        match
        for row in table
        if (match := re.search(r"as on (\d{2}\.\d{2}\.\d{4})", _normalise(row[0])))
    )
    as_on = datetime.strptime(title.group(1), "%d.%m.%Y").date()

    columns = {
        _normalise(cell): idx
        for row in table
        if not _normalise(row[0]).isdigit()
        for idx, cell in enumerate(row)
        if _normalise(cell) in MNRE_MODE_MAPPING
    }
    missing_columns = set(MNRE_MODE_MAPPING) - set(columns)
    if missing_columns:
        raise ParserException(
            "CEA.py", f"Columns missing from MNRE report: {missing_columns}"
        )

    capacity = defaultdict(lambda: defaultdict(float))
    for row in table:
        if not _normalise(row[0]).isdigit():
            continue
        state = _normalise(row[2])
        # Long names can be cut off at the cell border, e.g. "Andaman & Nicobar I"
        if state and any(name.startswith(state) for name in STATES_OUTSIDE_ZONES):
            continue
        if state not in IN_STATE_TO_ZONE_MAPPING:
            raise ParserException("CEA.py", f"Unknown state in MNRE report: {state}")
        zone_key = ZoneKey(IN_STATE_TO_ZONE_MAPPING[state])
        for mnre_mode, idx in columns.items():
            value = _normalise(row[idx]).replace(",", "")
            capacity[zone_key][MNRE_MODE_MAPPING[mnre_mode]] += float(value or 0)
    return as_on, {zone_key: dict(modes) for zone_key, modes in capacity.items()}


def fetch_mnre_capacity(
    session: Session,
) -> tuple[date, dict[ZoneKey, dict[str, float]]]:
    """Fetch the latest renewable and small hydro capacity per zone and mode in MW."""
    r = session.get(MNRE_URL)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    link = soup.find("a", attrs={"aria-label": re.compile(MNRE_REPORT_LABEL)})
    if not link:
        raise ParserException("CEA.py", f"No state-wise RE report on {MNRE_URL}")
    return parse_state_capacity(_download_pdf(link["href"], session))


def _capacity_entry(day: date, value: float, source: str) -> dict[str, Any]:
    return {
        "datetime": day.strftime("%Y-%m-%d"),
        "value": round(value, 2),
        "source": source,
    }


def fetch_production_capacity_for_all_zones(
    target_datetime: datetime, session: Session
) -> dict[str, Any] | None:
    cea_capacity = fetch_cea_capacity(target_datetime, session)
    month_start = target_datetime.date().replace(day=1)

    # MNRE only publishes its latest report, so it cannot be fetched for a given date
    mnre_as_on, mnre_capacity = fetch_mnre_capacity(session)
    logger.warning(
        f"MNRE does not use target_datetime {target_datetime:%Y-%m-%d}, using the "
        f"latest MNRE report as on {mnre_as_on} for renewable and small hydro capacity"
    )
    months_apart = abs(
        (mnre_as_on.year - month_start.year) * 12 + mnre_as_on.month - month_start.month
    )
    include_hydro = months_apart <= MAX_HYDRO_MONTHS_APART
    if not include_hydro:
        logger.warning(
            f"Latest MNRE report is {months_apart} months from {month_start:%Y-%m}, "
            "skipping hydro capacity as small hydro would not match large hydro"
        )

    all_capacity = {}
    for zone_key, cea_modes in cea_capacity.items():
        mnre_modes = mnre_capacity.get(zone_key, {})
        capacity = {
            mode: _capacity_entry(month_start, value, SOURCE)
            for mode, value in cea_modes.items()
            if mode != "hydro"
        }
        for mode in ("biomass", "solar", "wind"):
            capacity[mode] = _capacity_entry(
                mnre_as_on, mnre_modes.get(mode, 0.0), MNRE_SOURCE
            )
        # CEA reports large hydro, MNRE small hydro (<= 25 MW)
        if include_hydro:
            capacity["hydro"] = _capacity_entry(
                month_start,
                cea_modes["hydro"] + mnre_modes.get("hydro", 0.0),
                f"{SOURCE}, {MNRE_SOURCE}",
            )
        all_capacity[zone_key] = capacity
    return all_capacity


def fetch_production_capacity(
    target_datetime: datetime, zone_key: ZoneKey, session: Session
) -> dict[str, Any] | None:
    all_capacities = fetch_production_capacity_for_all_zones(target_datetime, session)
    return all_capacities[zone_key]


if __name__ == "__main__":
    print(
        fetch_production_capacity_for_all_zones(
            datetime(2026, 8, 1, tzinfo=timezone.utc), Session()
        )
    )
