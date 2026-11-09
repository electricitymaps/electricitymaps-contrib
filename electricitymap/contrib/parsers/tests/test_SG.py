from datetime import datetime
from importlib import resources
from json import loads

import pytest
from requests_mock import GET

from electricitymap.contrib.parsers import SG
from electricitymap.contrib.types import ZoneKey

TARGET_DATETIME = datetime(2026, 11, 9, 12, tzinfo=SG.TIMEZONE)


@pytest.fixture(autouse=True)
def mock_response(requests_mock):
    for value in (SG.DAILY_GENERATION_SHARE, SG.HALF_HOURLY_PRICE_DEMAND):
        requests_mock.register_uri(
            GET,
            f"{SG.DATASYNC_URL}?value={value}&fromDate=2026-11-10&toDate=2026-11-10",
            json=loads(
                resources.files("electricitymap.contrib.parsers.tests.mocks.SG")
                .joinpath(f"datasync_{value}_20261110.json")
                .read_text()
            ),
        )


def test_fetch_production(session, snapshot):
    assert snapshot == SG.fetch_production(
        ZoneKey("SG"), session=session, target_datetime=TARGET_DATETIME
    )


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
