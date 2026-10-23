import json
from datetime import datetime, timezone
from importlib import resources
from io import BytesIO
from zoneinfo import ZoneInfo

import openpyxl
import pytest
from requests_mock import GET

from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.parsers.SEMO import (
    API_URL,
    REGISTERED_UNITS_PAGE_URL,
    _select_latest_mapping_url,
    fetch_production,
    get_unit_fuel_mapping,
)
from electricitymap.contrib.types import ZoneKey

DUBLIN = ZoneInfo("Europe/Dublin")

# Fuel types for the units referenced by the BM-086 fixture. GU_999999 is left
# out on purpose so it exercises the "unit missing from the list" path.
FIXTURE_UNITS = {
    "GU_400020": "WIND",
    "GU_400030": "WIND",
    "GU_400050": "WIND",
    "GU_501690": "SOLAR",
    "GU_501650": "SOLAR",
    "GU_405850": "GAS",
    "GU_400180": "GAS",
    "GU_400270": "COAL",
    "GU_500041": "DISTILLATE",
    "GU_400750": "OIL",
    "GU_400200": "HYDRO",
    "GU_400570": "BIOMASS",
    "GU_400120": "MULTI_FUEL",
    "GU_403560": "BATTERY",
    "GU_400360": "PUMP_STORAGE",
    "GU_405170": "SYNC CONDENSER",
}

XLSX_URL = (
    "https://www.sem-o.com/sites/semo/files/2026-09/"
    "List%20of%20Registered%20Units%2023092026.xlsx"
)


def _bm086():
    return json.loads(
        resources.files("electricitymap.contrib.parsers.tests.mocks.SEMO")
        .joinpath("BM-086.json")
        .read_text()
    )


def _units_xlsx(units: dict[str, str]) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["List of Registered Units title row"])
    ws.append(
        [
            "Party ID",
            "Party Name",
            "Participant Name",
            "Resource Name",
            "Resource Type",
            "Fuel Type",
            "Intermediary",
            "Registered",
            "Effective Date",
            "Unit Name",
        ]
    )
    for name, fuel in units.items():
        ws.append(["PY", "Co", "PT", name, "GENERATOR", fuel, "", "Registered", "", ""])
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _register_mapping(requests_mock, units=FIXTURE_UNITS):
    """Mocks the registered-units page and the xlsx it links to."""
    requests_mock.register_uri(
        GET,
        REGISTERED_UNITS_PAGE_URL,
        text=(
            '<a href="/sites/semo/files/2026-09/List%20of%20Registered%20Parties.xlsx">Parties</a>'
            f'<a href="{XLSX_URL}">List of Registered Units 23092026.xlsx</a>'
        ),
    )
    requests_mock.register_uri(GET, XLSX_URL, content=_units_xlsx(units))


def test_fetch_production_ie(requests_mock, session, snapshot):
    _register_mapping(requests_mock)
    requests_mock.register_uri(GET, API_URL, json=_bm086())
    assert snapshot == fetch_production(
        zone_key=ZoneKey("IE"),
        session=session,
        target_datetime=datetime(2026, 9, 20, tzinfo=DUBLIN),
    )


def test_fetch_production_gb_nir(requests_mock, session, snapshot):
    _register_mapping(requests_mock)
    requests_mock.register_uri(GET, API_URL, json=_bm086())
    assert snapshot == fetch_production(
        zone_key=ZoneKey("GB-NIR"),
        session=session,
        target_datetime=datetime(2026, 9, 20, tzinfo=DUBLIN),
    )


def test_start_time_is_interpreted_as_utc(requests_mock, session):
    # BM-086 StartTime "2026-09-20T00:00:00" is UTC, not Dublin local time.
    _register_mapping(requests_mock)
    requests_mock.register_uri(GET, API_URL, json=_bm086())
    events = fetch_production(
        zone_key=ZoneKey("IE"),
        session=session,
        target_datetime=datetime(2026, 9, 20, tzinfo=DUBLIN),
    )
    assert events[0]["datetime"] == datetime(2026, 9, 20, 0, 0, tzinfo=timezone.utc)


def test_mapping_raises_when_unavailable(requests_mock, session):
    # The registered-units page is not registered, so discovery must raise
    # rather than silently producing an unlabelled breakdown.
    with pytest.raises(ParserException):
        get_unit_fuel_mapping(session=session)


def test_mapping_normalises_casing_and_typo(requests_mock, session):
    _register_mapping(requests_mock, {"GU_A": "Wind", "GU_B": "DISTIILLATE"})
    mapping = get_unit_fuel_mapping(session=session)
    assert mapping == {"GU_A": "WIND", "GU_B": "DISTILLATE"}


def test_mapping_uses_latest_live_xlsx(requests_mock, session):
    _register_mapping(requests_mock, {"GU_LIVE01": "GAS"})
    mapping = get_unit_fuel_mapping(session=session)
    assert mapping["GU_LIVE01"] == "GAS"


def test_select_latest_mapping_url_picks_newest_date():
    hrefs = [
        "/sites/semo/files/2026-08/List%20of%20Registered%20Units%2026082026.xlsx",
        "/sites/semo/files/2026-09/List%20of%20Registered%20Units%2016092026.xlsx",
        "/sites/semo/files/2026-09/List%20of%20Registered%20Units%2023092026.xlsx",
        "/sites/semo/files/2026-02/List%20of%20Registered%20Units.xlsx",
    ]
    assert _select_latest_mapping_url(hrefs).endswith(
        "2026-09/List%20of%20Registered%20Units%2023092026.xlsx"
    )
