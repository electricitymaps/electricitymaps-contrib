import logging
from datetime import datetime
from importlib import resources
from json import loads

import pytest
from requests_mock import GET

from electricitymap.contrib.lib.models.events import EventSourceType
from electricitymap.contrib.parsers import SG
from electricitymap.contrib.types import ZoneKey

MOCKS = resources.files("electricitymap.contrib.parsers.tests.mocks.SG")
TARGET_DATETIME = datetime(2026, 11, 9, 12, tzinfo=SG.TIMEZONE)


@pytest.fixture(autouse=True)
def mock_response(requests_mock):
    # Metered generation is published up to 2026-10-25, 2 weeks before the target day.
    requests_mock.register_uri(
        GET,
        f"{SG.DATA_DOWNLOAD_URL}?value={SG.METERED_GENERATION}"
        "&fromDate=2026-10-11&toDate=2026-11-09",
        text=MOCKS.joinpath("metered_generation_20261011_20261109.csv").read_text(),
    )
    for from_date in ("2026-11-10", "2026-11-03", "2026-10-27"):
        for value in (SG.DAILY_GENERATION_SHARE, SG.HALF_HOURLY_PRICE_DEMAND):
            requests_mock.register_uri(
                GET,
                f"{SG.DATASYNC_URL}?value={value}&fromDate={from_date}&toDate={from_date}",
                json=loads(
                    MOCKS.joinpath(
                        f"datasync_{value}_{from_date.replace('-', '')}.json"
                    ).read_text()
                ),
            )


def test_fetch_production(session, snapshot):
    assert snapshot == SG.fetch_production(
        ZoneKey("SG"), session=session, target_datetime=TARGET_DATETIME
    )


def test_fetch_production_estimates_after_last_metered_day(session):
    production = SG.fetch_production(
        ZoneKey("SG"), session=session, target_datetime=TARGET_DATETIME
    )
    last_metered = max(
        event["datetime"]
        for event in production
        if event["sourceType"] == EventSourceType.measured
    )
    estimated = [
        event
        for event in production
        if event["sourceType"] == EventSourceType.estimated
    ]
    assert last_metered.date().isoformat() == "2026-10-25"
    # The 2026-10-20 periods of the oldest weekly window are already metered.
    assert min(event["datetime"] for event in estimated).date().isoformat() == (
        "2026-10-26"
    )
    # Solar comes from the metered 12:00 period, and there is none at 00:00.
    noon = [event for event in estimated if event["datetime"].hour == 12]
    assert {event["production"]["solar"] for event in noon} == {2 * 492.963}


def test_fetch_production_keeps_metered_data_when_estimation_fails(
    session, requests_mock
):
    requests_mock.register_uri(
        GET,
        f"{SG.DATASYNC_URL}?value={SG.DAILY_GENERATION_SHARE}"
        "&fromDate=2026-11-10&toDate=2026-11-10",
        json={"success": True, "data": {"data": []}},
    )
    production = SG.fetch_production(
        ZoneKey("SG"),
        session=session,
        target_datetime=TARGET_DATETIME,
        logger=logging.getLogger("test"),
    )
    assert {event["sourceType"] for event in production} == {EventSourceType.measured}


def test_fetch_price(session, snapshot):
    assert snapshot == SG.fetch_price(
        ZoneKey("SG"), session=session, target_datetime=TARGET_DATETIME
    )


@pytest.mark.parametrize(
    "label, end, expected",
    [
        ("03 Nov 00:30-01:00", "2026-11-09", datetime(2026, 11, 3, 0, 30)),
        ("03 Nov", "2026-11-09", datetime(2026, 11, 3)),
        ("31 Dec 23:30-00:00", "2027-01-04", datetime(2026, 12, 31, 23, 30)),
    ],
)
def test_parse_label_infers_year(label, end, expected):
    assert SG._parse_label(
        label, datetime.fromisoformat(end).date()
    ) == expected.replace(tzinfo=SG.TIMEZONE)
