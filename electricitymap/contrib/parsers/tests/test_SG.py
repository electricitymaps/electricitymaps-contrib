from datetime import datetime
from importlib import resources
from json import loads

import pytest
from requests_mock import GET

from electricitymap.contrib.parsers import SG
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.types import ZoneKey

MOCKS = resources.files("electricitymap.contrib.parsers.tests.mocks.SG")
TARGET_DATETIME = datetime(2026, 11, 9, 12, tzinfo=SG.TIMEZONE)
METERED_URL = (
    f"{SG.DATA_DOWNLOAD_URL}?value={SG.METERED_GENERATION}"
    "&fromDate=2026-10-11&toDate=2026-11-09"
)


@pytest.fixture(autouse=True)
def mock_response(requests_mock):
    requests_mock.register_uri(
        GET,
        METERED_URL,
        text=MOCKS.joinpath("metered_generation_20261011_20261109.csv").read_text(),
    )
    requests_mock.register_uri(
        GET,
        f"{SG.DATASYNC_URL}?value={SG.HALF_HOURLY_PRICE_DEMAND}"
        "&fromDate=2026-11-10&toDate=2026-11-10",
        json=loads(MOCKS.joinpath("datasync_14_20261110.json").read_text()),
    )


def test_fetch_production(session, snapshot):
    assert snapshot == SG.fetch_production(
        ZoneKey("SG"), session=session, target_datetime=TARGET_DATETIME
    )


def test_fetch_production_raises_when_nothing_is_published(session, requests_mock):
    requests_mock.register_uri(GET, METERED_URL, status_code=204, text="")
    with pytest.raises(ParserException):
        SG.fetch_production(
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
        ("31 Dec 23:30-00:00", "2027-01-04", datetime(2026, 12, 31, 23, 30)),
    ],
)
def test_parse_label_infers_year(label, end, expected):
    assert SG._parse_label(
        label, datetime.fromisoformat(end).date()
    ) == expected.replace(tzinfo=SG.TIMEZONE)
