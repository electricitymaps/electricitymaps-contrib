"""Tests for AEMO.py"""

import io
import logging
import re
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from requests_mock import GET
from syrupy.extensions.single_file import SingleFileAmberSnapshotExtension

from electricitymap.contrib.parsers.AEMO import (
    CURRENT_DISPATCH_URL,
    EXCHANGE_KEY_TO_INTERCONNECTORS,
    FORECAST_DEMAND_URL,
    INTERCONNECTOR_RES,
    REGION_SUM,
    REGION_TO_ZONE_KEY,
    ReportTable,
    _rows_from_zip,
    fetch_consumption,
    fetch_consumption_forecast,
    fetch_exchange,
)
from electricitymap.contrib.parsers.lib.exceptions import ParserException

BASE_PATH_TO_MOCK = Path("electricitymap/contrib/parsers/tests/mocks/AEMO")
NEM_ZONES = sorted(REGION_TO_ZONE_KEY.values())
FORECAST_FILE = "PUBLIC_FORECAST_OPERATIONAL_DEMAND_HH_202504011800_20250401173353.zip"


@pytest.fixture
def forecast_demand_mock(requests_mock):
    """The demand forecast report, as AEMO serves it."""
    requests_mock.register_uri(
        GET, FORECAST_DEMAND_URL, text=f'<a href="{FORECAST_FILE}">x</a>'
    )
    requests_mock.register_uri(
        GET,
        FORECAST_DEMAND_URL + FORECAST_FILE,
        content=Path(BASE_PATH_TO_MOCK, FORECAST_FILE).read_bytes(),
    )
    return requests_mock


@pytest.mark.parametrize("zone_key", NEM_ZONES)
def test_snapshot_fetch_consumption_forecast(
    forecast_demand_mock, session, snapshot, zone_key
):
    assert snapshot(
        extension_class=SingleFileAmberSnapshotExtension
    ) == fetch_consumption_forecast(
        zone_key=zone_key,
        session=session,
        target_datetime=datetime(2025, 4, 1, 18, 0),  # the mock file's date
    )


LIVE_DISPATCH_FILES = (
    "PUBLIC_DISPATCHIS_202608260245_0000000534470301.zip",
    "PUBLIC_DISPATCHIS_202608260250_0000000534470840.zip",
)
# The fixtures above hold the dispatch intervals ending 02:45 and 02:50 AEST.
AEST = timezone(timedelta(hours=10))
EXCHANGE_PAIRS = [
    ("AU-NSW", "AU-QLD"),
    ("AU-NSW", "AU-VIC"),
    ("AU-SA", "AU-VIC"),
    ("AU-TAS", "AU-VIC"),
]


def _dispatch_zip(rows: list[str]) -> bytes:
    """A dispatch report holding just the interconnector rows given."""
    header = (
        "I,DISPATCH,INTERCONNECTORRES,3,SETTLEMENTDATE,RUNNO,INTERCONNECTORID,"
        "DISPATCHINTERVAL,INTERVENTION,METEREDMWFLOW,MWFLOW,MWLOSSES"
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("PUBLIC_DISPATCHIS_TEST.CSV", "\n".join([header, *rows]))
    return buffer.getvalue()


def _rows(fixture: str, table: ReportTable) -> list[dict[str, str]]:
    """Rows of one report table, read straight from a fixture."""
    return list(_rows_from_zip(Path(BASE_PATH_TO_MOCK, fixture).read_bytes(), table))


def _interconnector_flows(fixture: str) -> dict[tuple[str, str], float]:
    """(settlement, interconnector) -> metered flow, read straight from a fixture."""
    return {
        (row["SETTLEMENTDATE"], row["INTERCONNECTORID"]): float(row["METEREDMWFLOW"])
        for row in _rows(fixture, INTERCONNECTOR_RES)
        if row["INTERVENTION"] == "0"
    }


@pytest.fixture
def live_dispatch_mock(requests_mock):
    """The two most recent dispatch reports, as AEMO serves them."""
    requests_mock.register_uri(
        GET,
        CURRENT_DISPATCH_URL,
        text="".join(f'<a href="{name}">{name}</a>' for name in LIVE_DISPATCH_FILES),
    )
    for name in LIVE_DISPATCH_FILES:
        requests_mock.register_uri(
            GET,
            CURRENT_DISPATCH_URL + name,
            content=Path(BASE_PATH_TO_MOCK, name).read_bytes(),
        )
    return requests_mock


@pytest.mark.parametrize(("zone_key1", "zone_key2"), EXCHANGE_PAIRS)
def test_snapshot_fetch_exchange(
    live_dispatch_mock, session, snapshot, zone_key1, zone_key2
):
    assert snapshot(extension_class=SingleFileAmberSnapshotExtension) == fetch_exchange(
        zone_key1, zone_key2, session
    )


def test_exchange_stamps_the_start_of_the_dispatch_interval(
    live_dispatch_mock, session
):
    """The fixtures are the intervals ending 02:45 and 02:50 AEST."""
    events = fetch_exchange("AU-TAS", "AU-VIC", session)

    assert [event["datetime"] for event in events] == [
        datetime(2026, 8, 26, 2, 40, tzinfo=AEST),
        datetime(2026, 8, 26, 2, 45, tzinfo=AEST),
    ]
    assert [event["end_datetime"] for event in events] == [
        datetime(2026, 8, 26, 2, 45, tzinfo=AEST),
        datetime(2026, 8, 26, 2, 50, tzinfo=AEST),
    ]


@pytest.mark.parametrize(("zone_key1", "zone_key2"), EXCHANGE_PAIRS)
def test_exchange_sums_every_interconnector_on_the_border(
    live_dispatch_mock, session, zone_key1, zone_key2
):
    """QNI + Terranora for NSW-QLD, Heywood + Murraylink for SA-VIC, one line each
    for the other two, signed by AEMO's REGIONFROM -> REGIONTO."""
    events = fetch_exchange(zone_key1, zone_key2, session)
    flows = _interconnector_flows(LIVE_DISPATCH_FILES[0])
    settlement = "2026/08/26 02:45:00"
    expected = sum(
        direction * flows[settlement, interconnector]
        for interconnector, direction in EXCHANGE_KEY_TO_INTERCONNECTORS[
            f"{zone_key1}->{zone_key2}"
        ].items()
    )

    first = events[0]
    assert first["end_datetime"] == datetime(2026, 8, 26, 2, 45, tzinfo=AEST)
    assert first["netFlow"] == pytest.approx(expected)


def test_exchange_skips_an_interval_missing_an_interconnector(requests_mock, session):
    """An interval one line of the border did not report yields no event."""
    name = "PUBLIC_DISPATCHIS_202608260245_0000000000000001.zip"
    requests_mock.register_uri(
        GET, CURRENT_DISPATCH_URL, text=f'<a href="{name}">x</a>'
    )
    requests_mock.register_uri(
        GET,
        CURRENT_DISPATCH_URL + name,
        content=_dispatch_zip(
            [  # QNI reported, Terranora missing
                "D,DISPATCH,INTERCONNECTORRES,3,2026/08/26 02:45:00,1,NSW1-QLD1,1,0,-492.8,-490,1.2",
                "D,DISPATCH,INTERCONNECTORRES,3,2026/08/26 02:45:00,1,T-V-MNSP1,1,0,386.4,380,2.1",
            ]
        ),
    )

    assert fetch_exchange("AU-NSW", "AU-QLD", session) == []
    # the border that is complete still reports
    assert len(fetch_exchange("AU-TAS", "AU-VIC", session)) == 1


def test_republished_interval_is_not_counted_twice(requests_mock, session):
    """The same interval published twice, as AEMO does when revising it, is
    counted once."""
    rows = [
        "D,DISPATCH,INTERCONNECTORRES,3,2026/08/26 02:45:00,1,T-V-MNSP1,1,0,386.4,380,2.1"
    ]
    names = [
        "PUBLIC_DISPATCHIS_202608260245_0000000000000003.zip",
        "PUBLIC_DISPATCHIS_202608260245_0000000000000004.zip",  # same interval, revised
    ]
    requests_mock.register_uri(
        GET,
        CURRENT_DISPATCH_URL,
        text="".join(f'<a href="{name}">x</a>' for name in names),
    )
    for name in names:
        requests_mock.register_uri(
            GET, CURRENT_DISPATCH_URL + name, content=_dispatch_zip(rows)
        )

    events = fetch_exchange("AU-TAS", "AU-VIC", session)

    assert [event["netFlow"] for event in events] == [386.4]


def test_unmapped_interconnector_is_reported_but_not_fatal(
    requests_mock, session, caplog
):
    """An interconnector the parser does not map is logged, and the borders it
    does map still report."""
    name = "PUBLIC_DISPATCHIS_202608260245_0000000000000002.zip"
    requests_mock.register_uri(
        GET, CURRENT_DISPATCH_URL, text=f'<a href="{name}">x</a>'
    )
    requests_mock.register_uri(
        GET,
        CURRENT_DISPATCH_URL + name,
        content=_dispatch_zip(
            [
                "D,DISPATCH,INTERCONNECTORRES,3,2026/08/26 02:45:00,1,T-V-MNSP1,1,0,386.4,380,2.1",
                "D,DISPATCH,INTERCONNECTORRES,3,2026/08/26 02:45:00,1,S-N-PEC,1,0,150,150,1",
            ]
        ),
    )

    with caplog.at_level(logging.WARNING):
        events = fetch_exchange("AU-TAS", "AU-VIC", session)

    assert [event["netFlow"] for event in events] == [386.4]
    assert "S-N-PEC" in caplog.text


def test_backfill_reads_the_monthly_archive(requests_mock, session):
    """A target datetime is served from the monthly archive."""
    requests_mock.register_uri(
        GET,
        re.compile(r".*DISPATCHINTERCONNECTORRES.*"),
        content=Path(
            BASE_PATH_TO_MOCK,
            "PUBLIC_ARCHIVE_DISPATCHINTERCONNECTORRES_202607010000.zip",
        ).read_bytes(),
    )

    events = fetch_exchange(
        "AU-NSW",
        "AU-QLD",
        session,
        target_datetime=datetime(2026, 7, 8, tzinfo=AEST),
    )

    assert [event["datetime"] for event in events] == [
        datetime(2026, 7, 1, 0, 0, tzinfo=AEST),
        datetime(2026, 7, 1, 0, 5, tzinfo=AEST),
        datetime(2026, 7, 1, 0, 10, tzinfo=AEST),
    ]
    assert all(event["source"] == "aemo.com.au" for event in events)


@pytest.mark.parametrize("zone_key", NEM_ZONES)
def test_snapshot_fetch_consumption(live_dispatch_mock, session, snapshot, zone_key):
    assert snapshot(
        extension_class=SingleFileAmberSnapshotExtension
    ) == fetch_consumption(zone_key, session)


def test_consumption_reports_total_demand_over_the_dispatch_interval(
    live_dispatch_mock, session
):
    """The fixtures are the intervals ending 02:45 and 02:50 AEST."""
    events = fetch_consumption("AU-NSW", session)
    demand = next(
        float(row["TOTALDEMAND"])
        for row in _rows(LIVE_DISPATCH_FILES[0], REGION_SUM)
        if row["REGIONID"] == "NSW1" and row["INTERVENTION"] == "0"
    )

    assert [event["datetime"] for event in events] == [
        datetime(2026, 8, 26, 2, 40, tzinfo=AEST),
        datetime(2026, 8, 26, 2, 45, tzinfo=AEST),
    ]
    assert events[0]["end_datetime"] == datetime(2026, 8, 26, 2, 45, tzinfo=AEST)
    assert events[0]["consumption"] == pytest.approx(demand)
    assert all(event["source"] == "aemo.com.au" for event in events)


def test_consumption_backfill_reads_the_monthly_archive(requests_mock, session):
    requests_mock.register_uri(
        GET,
        re.compile(r".*DISPATCHREGIONSUM.*"),
        content=Path(
            BASE_PATH_TO_MOCK, "PUBLIC_ARCHIVE_DISPATCHREGIONSUM_202607010000.zip"
        ).read_bytes(),
    )

    events = fetch_consumption(
        "AU-VIC", session, target_datetime=datetime(2026, 7, 8, tzinfo=AEST)
    )

    assert [event["datetime"] for event in events] == [
        datetime(2026, 7, 1, 0, 0, tzinfo=AEST),
        datetime(2026, 7, 1, 0, 5, tzinfo=AEST),
        datetime(2026, 7, 1, 0, 10, tzinfo=AEST),
    ]


def test_consumption_rejects_zones_outside_the_nem(session):
    # WEM is a separate market whose data AEMO publishes elsewhere.
    with pytest.raises(ParserException, match="AU-WA"):
        fetch_consumption("AU-WA", session)


def test_unknown_exchange_raises(session):
    with pytest.raises(ParserException, match="AU-NSW->AU-SA"):
        fetch_exchange("AU-NSW", "AU-SA", session)
