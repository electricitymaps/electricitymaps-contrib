from datetime import UTC, datetime, timedelta
from io import BytesIO

import openpyxl
import pytest
from requests_mock import GET

from electricitymap.contrib.parsers import ENTSOExEIRGRID
from electricitymap.contrib.parsers.ENTSOE import ENTSOE_URL
from electricitymap.contrib.types import ZoneKey

FILE = "System-Data-Qtr-Hourly-2025-v13.xlsx"
GAS_UNIT = "47W000000000095C"
MONEYPOINT = "47W0000000000889"
TURLOUGH = "47W0000000001982"


def _system_data_xlsx(rows: list[tuple]) -> bytes:
    """``rows``: (local datetime, GMT offset, gen, wind, solar, batteries)."""
    book = openpyxl.Workbook()
    sheet = book.worksheets[0]
    sheet.append(
        ["DateTime", "GMT Offset", "IE Generation", "IE Wind Generation"]
        + ["IE Solar Generation", "IE Batteries"]
    )
    for row in rows:
        sheet.append(list(row))
    out = BytesIO()
    book.save(out)
    return out.getvalue()


def _series(unit: str, psr: str, values: list[float], generation: bool = True) -> str:
    domain = "inBiddingZone_Domain" if generation else "outBiddingZone_Domain"
    points = "".join(
        f"<Point><position>{i}</position><quantity>{v}</quantity></Point>"
        for i, v in enumerate(values, start=1)
    )
    return f"""<TimeSeries><curveType>A01</curveType>
      <{domain}.mRID>10YIE-1001A00010</{domain}.mRID>
      <MktPSRType><psrType>{psr}</psrType>
        <PowerSystemResources><mRID>{unit}</mRID></PowerSystemResources></MktPSRType>
      <Period><timeInterval><start>2025-07-01T00:00Z</start><end>2025-07-01T01:00Z</end></timeInterval>
        <resolution>PT30M</resolution>{points}</Period></TimeSeries>"""


@pytest.fixture(autouse=True)
def _setup(monkeypatch, requests_mock):
    monkeypatch.setenv("ENTSOE_TOKEN", "token")
    ENTSOExEIRGRID._system_data.clear()
    requests_mock.register_uri(
        GET, ENTSOExEIRGRID.EIRGRID_REPORTS_URL, text=f'<a href="/x/{FILE}">x</a>'
    )
    # Irish summer time: 01:00-01:45 local is 00:00-00:45 UTC.
    requests_mock.register_uri(
        GET,
        ENTSOExEIRGRID.EIRGRID_FILES_URL + FILE,
        content=_system_data_xlsx(
            [
                (datetime(2025, 7, 1, 1, 0), 1, 1000, 300, 50, 20),
                (datetime(2025, 7, 1, 1, 15), 1, 1100, 320, 70, 20),
                (datetime(2025, 7, 1, 1, 30), 1, 1200, 340, 90, -10),
                (datetime(2025, 7, 1, 1, 45), 1, 1200, 360, 110, -10),
            ]
        ),
    )
    # ENTSO-E labels the half-hour 00:00-00:30 as position 2 (00:30).
    requests_mock.register_uri(
        GET,
        ENTSOE_URL,
        text="<GL_MarketDocument>"
        + _series(GAS_UNIT, "B04", [999, 500, 600])
        + _series(MONEYPOINT, "B05", [999, 100, 100])
        + _series(TURLOUGH, "B10", [999, 40, 0])
        + _series(TURLOUGH, "B10", [999, 0, 60], generation=False)
        + "</GL_MarketDocument>",
    )


def _fetch(session):
    start = datetime(2025, 7, 1, tzinfo=UTC)
    events = ENTSOExEIRGRID.fetch_production_range(
        ZoneKey("IE"), session, start, start + timedelta(minutes=30)
    )
    return {e["datetime"]: e for e in events}


def test_merges_eirgrid_and_shifted_entsoe_units(session):
    events = _fetch(session)
    first = events[datetime(2025, 7, 1, tzinfo=UTC)]
    # EirGrid: mean of 00:00 and 00:15 UTC. ENTSO-E: point labelled 00:30.
    # Moneypoint after 2025-06-20 is oil. unknown = 1050 - 310 - 60 - 500 - 100
    # - 40 (pumped generation) - 20 (battery discharge) = 20.
    assert first["production"] == {
        "gas": 500.0,
        "oil": 100.0,
        "wind": 310.0,
        "solar": 60.0,
        "unknown": 20.0,
    }
    assert first["storage"] == {"hydro": -40.0, "battery": -20.0}
    assert first["source"] == "eirgrid.ie,entsoe.eu"


def test_pumping_and_battery_charging_are_storage(session):
    second = _fetch(session)[datetime(2025, 7, 1, 0, 30, tzinfo=UTC)]
    assert second["storage"] == {"hydro": 60.0, "battery": 10.0}
    # 1200 - 350 - 100 - 600 - 100 = 50: pumping and charging are not generation.
    assert second["production"]["unknown"] == 50.0


def test_half_hours_missing_from_entsoe_are_not_emitted(session, requests_mock):
    requests_mock.register_uri(
        GET,
        ENTSOE_URL,
        status_code=400,
        text="<Acknowledgement_MarketDocument><Reason><text>No matching data found</text></Reason></Acknowledgement_MarketDocument>",
    )
    assert _fetch(session) == {}


def test_frozen_eirgrid_total_leaves_unknown_out():
    t0 = datetime(2025, 4, 16, 10, tzinfo=UTC)
    data = {
        t0 + timedelta(minutes=30 * i): {"gen": 3623.6, "wind": 1.0} for i in range(4)
    }
    data[t0 + timedelta(hours=2)] = {"gen": 3000.0, "wind": 1.0}
    ENTSOExEIRGRID._drop_stuck_totals(data)
    assert [dt for dt, d in sorted(data.items()) if "gen" in d] == [
        t0 + timedelta(hours=2)
    ]
