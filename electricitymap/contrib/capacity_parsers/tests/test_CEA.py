from datetime import datetime, timezone
from pathlib import Path

import pytest
from requests_mock import GET

from electricitymap.contrib.capacity_parsers.CEA import (
    MNRE_URL,
    REPORTS_URL,
    fetch_production_capacity_for_all_zones,
)
from electricitymap.contrib.parsers.lib.exceptions import ParserException

base_path_to_mock = Path("electricitymap/contrib/capacity_parsers/tests/mocks/CEA")
CEA_REPORT_URL = "https://cea.nic.in/api/dashboardReports/download-pdf/en/5a762fd0-c972-42f1-9167-a1eb64e804db"
TARGET_DATETIME = datetime(2026, 8, 1, tzinfo=timezone.utc)
MNRE_REPORT_URL = "https://cdnbbsr.s3waas.gov.in/s3716e1b8c6cd17b771da77391355749f3/uploads/2026/10/20261008207003538.pdf"


@pytest.fixture
def cea_mocks(adapter):
    adapter.register_uri(
        GET,
        REPORTS_URL,
        text=(base_path_to_mock / "reports_page.html").read_text(),
    )
    adapter.register_uri(
        GET,
        CEA_REPORT_URL,
        content=(base_path_to_mock / "installed_capacity_2026-08.pdf").read_bytes(),
    )
    adapter.register_uri(
        GET,
        MNRE_URL,
        text=(base_path_to_mock / "mnre_physical_progress.html").read_text(),
    )
    adapter.register_uri(
        GET,
        MNRE_REPORT_URL,
        content=(base_path_to_mock / "mnre_state_wise_2026-09.pdf").read_bytes(),
    )


def test_fetch_production_capacity_for_all_zones(session, cea_mocks, snapshot):
    assert fetch_production_capacity_for_all_zones(TARGET_DATETIME, session) == snapshot


def test_coal_includes_lignite(session, cea_mocks):
    capacity = fetch_production_capacity_for_all_zones(TARGET_DATETIME, session)
    # Northern Region: 61821.04 MW coal + 1330.00 MW lignite
    assert capacity["IN-NO"]["coal"]["value"] == 63151.04


def test_hydro_includes_small_hydro(session, cea_mocks):
    capacity = fetch_production_capacity_for_all_zones(TARGET_DATETIME, session)
    # Southern Region: 13676.48 MW large hydro (CEA) + 1938.48 MW small hydro (MNRE)
    assert capacity["IN-SO"]["hydro"]["value"] == 15614.96


def test_renewables_use_mnre_date(session, cea_mocks):
    capacity = fetch_production_capacity_for_all_zones(TARGET_DATETIME, session)
    assert capacity["IN-SO"]["solar"]["datetime"] == "2026-09-30"


def test_cea_uses_target_month(session, cea_mocks):
    capacity = fetch_production_capacity_for_all_zones(TARGET_DATETIME, session)
    assert capacity["IN-SO"]["coal"]["datetime"] == "2026-08-01"
    assert capacity["IN-SO"]["hydro"]["datetime"] == "2026-08-01"


def test_mnre_does_not_use_target_datetime(session, cea_mocks, caplog):
    fetch_production_capacity_for_all_zones(TARGET_DATETIME, session)
    assert "MNRE does not use target_datetime 2026-08-01" in caplog.text
    assert "latest MNRE report as on 2026-09-30" in caplog.text


def test_missing_cea_month_raises(session, cea_mocks):
    with pytest.raises(ParserException, match="2026-09"):
        fetch_production_capacity_for_all_zones(
            datetime(2026, 9, 1, tzinfo=timezone.utc), session
        )


def test_hydro_skipped_when_mnre_is_far_from_target(
    session, cea_mocks, adapter, caplog
):
    # CEA report for 2026-06, MNRE as on 2026-09-30: 3 months apart
    adapter.register_uri(
        GET,
        REPORTS_URL,
        text=(base_path_to_mock / "reports_page.html")
        .read_text()
        .replace('data-date="2026-08"', 'data-date="2026-06"'),
    )
    capacity = fetch_production_capacity_for_all_zones(
        datetime(2026, 6, 1, tzinfo=timezone.utc), session
    )
    assert "hydro" not in capacity["IN-SO"]
    assert "solar" in capacity["IN-SO"]
    assert "skipping hydro capacity" in caplog.text


def test_hydro_included_when_mnre_is_close_to_target(session, cea_mocks, adapter):
    # CEA report for 2026-07, MNRE as on 2026-09-30: 2 months apart. The first row
    # matching the month is used, which is the mocked report.
    adapter.register_uri(
        GET,
        REPORTS_URL,
        text=(base_path_to_mock / "reports_page.html")
        .read_text()
        .replace('data-date="2026-08"', 'data-date="2026-07"'),
    )
    capacity = fetch_production_capacity_for_all_zones(
        datetime(2026, 7, 1, tzinfo=timezone.utc), session
    )
    assert capacity["IN-SO"]["hydro"]["datetime"] == "2026-07-01"
