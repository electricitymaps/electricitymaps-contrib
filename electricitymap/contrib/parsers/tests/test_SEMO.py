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
    fetch_production_range,
    get_unit_fuel_mapping,
)
from electricitymap.contrib.types import ZoneKey

DUBLIN = ZoneInfo("Europe/Dublin")
# A window covering the BM-086 fixture (events at 2026-09-20 00:00 and 00:30 UTC).
START = datetime(2026, 9, 18, tzinfo=DUBLIN)
END = datetime(2026, 9, 21, 23, 59, 59, tzinfo=DUBLIN)

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


def test_fetch_production_range_queries_the_given_window(requests_mock, session):
    # The window passed in is honoured verbatim in the BM-086 StartTime filter,
    # so the caller (SEMOxSMARTGRID) controls the range for both sources.
    _register_mapping(requests_mock, {"GU_400020": "WIND"})
    requests_mock.register_uri(
        GET, API_URL, json=_bm086_rows([("GU_400020", "2026-09-20T00:00:00", 10.0)])
    )
    fetch_production_range(
        ZoneKey("IE"),
        session,
        datetime(2026, 9, 18, tzinfo=timezone.utc),
        datetime(2026, 9, 21, 23, 59, 59, tzinfo=timezone.utc),
    )
    bm086_request = next(
        r for r in reversed(requests_mock.request_history) if "BM-086" in r.url
    )
    start_time_filter = bm086_request.qs["starttime"][0]
    assert "2026-09-18t00:00:00" in start_time_filter
    assert "2026-09-21t23:59:59" in start_time_filter


def test_fetch_production_ie(requests_mock, session, snapshot):
    _register_mapping(requests_mock)
    requests_mock.register_uri(GET, API_URL, json=_bm086())
    assert snapshot == fetch_production_range(
        zone_key=ZoneKey("IE"),
        session=session,
        start_datetime=START,
        end_datetime=END,
    )


def test_fetch_production_gb_nir(requests_mock, session, snapshot):
    _register_mapping(requests_mock)
    requests_mock.register_uri(GET, API_URL, json=_bm086())
    assert snapshot == fetch_production_range(
        zone_key=ZoneKey("GB-NIR"),
        session=session,
        start_datetime=START,
        end_datetime=END,
    )


def test_start_time_is_interpreted_as_utc(requests_mock, session):
    # BM-086 StartTime "2026-09-20T00:00:00" is UTC, not Dublin local time.
    _register_mapping(requests_mock)
    requests_mock.register_uri(GET, API_URL, json=_bm086())
    events = fetch_production_range(
        zone_key=ZoneKey("IE"),
        session=session,
        start_datetime=START,
        end_datetime=END,
    )
    assert events[0]["datetime"] == datetime(2026, 9, 20, 0, 0, tzinfo=timezone.utc)


def _bm086_rows(rows):
    """Builds a BM-086 response from ``(resource, start_time, metered_mw)`` tuples."""
    items = [
        {
            "TradeDate": "2026-09-20",
            "ParticipantName": "PT",
            "ResourceName": rn,
            "ResourceType": "GEN",
            "StartTime": st,
            "EndTime": st,
            "Jurisdiction": "ROI",
            "MeteredMW": mw,
        }
        for rn, st, mw in rows
    ]
    return {"pagination": {"totalItems": len(items)}, "items": items}


def test_fetch_production_deduplicates_settlement_runs(requests_mock, session):
    # BM-086 returns one row per settlement run for a unit/half-hour, latest last.
    # They must be deduplicated (keep last), not summed.
    _register_mapping(
        requests_mock, {"GU_400020": "WIND", "GU_405850": "GAS", "GU_400180": "GAS"}
    )
    st = "2026-09-20T00:00:00"
    requests_mock.register_uri(
        GET,
        API_URL,
        json=_bm086_rows(
            [
                ("GU_400020", st, 100.0),
                ("GU_400020", st, 100.0),  # identical copy
                ("GU_405850", st, 0.0),
                ("GU_405850", st, 200.0),  # early run 0, settled value last
                ("GU_400180", st, 50.0),
                ("GU_400180", st, 50.0),
                ("GU_400180", st, 49.0),  # small correction, latest run last
            ]
        ),
    )
    events = fetch_production_range(
        zone_key=ZoneKey("IE"),
        session=session,
        start_datetime=START,
        end_datetime=END,
    )
    production = events[0]["production"]
    assert production["wind"] == 100  # not 200
    assert production["gas"] == 249  # 200 + 49 (last of each), not 349


def test_coal_peat_units_overridden_by_resource_name(requests_mock, session):
    # Moneypoint (registered COAL) now runs on oil, and Edenderry (registered
    # PEAT) on biomass. Per-unit overrides correct these by ResourceName.
    _register_mapping(requests_mock, {"GU_400270": "COAL", "GU_401860": "PEAT"})
    st = "2026-09-20T00:00:00"
    requests_mock.register_uri(
        GET,
        API_URL,
        json=_bm086_rows([("GU_400270", st, 250.0), ("GU_401860", st, 60.0)]),
    )
    events = fetch_production_range(
        zone_key=ZoneKey("IE"),
        session=session,
        start_datetime=START,
        end_datetime=END,
    )
    production = events[0]["production"]
    assert production["oil"] == 250  # Moneypoint COAL -> oil
    assert production["biomass"] == 60  # Edenderry PEAT -> biomass
    assert production.get("coal") is None
    assert production.get("unknown") is None


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
