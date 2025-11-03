from datetime import datetime
from pathlib import Path

import pytest
from requests_mock import POST

from electricitymap.contrib.lib.types import ZoneKey
from electricitymap.contrib.parsers import CZ
from electricitymap.contrib.parsers.lib.exceptions import ParserException

base_path_to_mock = Path("electricitymap/contrib/parsers/tests/mocks/CZ")

# Using a fixed date that exists in the mock XML data
TARGET_DATETIME = datetime(2025, 10, 31, 18, 0, 0)


@pytest.fixture
def mock_good_response(adapter):
    """
    Mocks the CEPS API with a "good" response containing expected data.
    """

    data = base_path_to_mock / "CrossborderPowerFlows.xml"
    adapter.register_uri(
        POST,
        CZ.url,
        content=data.read_bytes(),
    )


@pytest.fixture
def mock_no_data_response(adapter):
    """
    Mocks the CEPS API with a "bad" response that is missing the <data> tag.
    (This fixture is requested by the exception test)
    """

    mock_xml_content = (
        '<root xmlns="https://www.ceps.cz/CepsData/StructuredData/1.0">'
        "<information><name>Cross-border power flows</name></information>"
        '<series><serie id="value1" name="PSE Actual [MW]" /></series>'
        "</root>"
    )

    adapter.register_uri(POST, CZ.url, text=mock_xml_content)


@pytest.mark.parametrize(
    "zone_key2",
    [
        ZoneKey("PL"),
        ZoneKey("DE"),
        ZoneKey("AT"),
    ],
)
def test_fetch_exchange(session, snapshot, mock_good_response, zone_key2):
    result = CZ.fetch_exchange(
        zone_key1=ZoneKey("CZ"),
        zone_key2=zone_key2,
        session=session,
        target_datetime=TARGET_DATETIME,
    )

    assert snapshot == result


def test_fetch_exchange_forecast_pl(session, snapshot, mock_good_response):
    result = CZ.fetch_exchange_forecast(
        zone_key1=ZoneKey("CZ"),
        zone_key2=ZoneKey("PL"),
        session=session,
        target_datetime=TARGET_DATETIME,
    )

    assert snapshot == result


def test_fetch_exchange_raises_exception_on_no_data(session, mock_no_data_response):
    with pytest.raises(ParserException):
        CZ.fetch_exchange(
            zone_key1=ZoneKey("CZ"),
            zone_key2=ZoneKey("PL"),
            session=session,
            target_datetime=TARGET_DATETIME,
        )
