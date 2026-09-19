from datetime import datetime
from logging import getLogger
from pathlib import Path

import pytest
from requests_mock import POST
from syrupy.extensions.single_file import SingleFileAmberSnapshotExtension

from electricitymap.contrib.parsers import CZ
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.types import ZoneKey

base_path_to_mock = Path("electricitymap/contrib/parsers/tests/mocks/CZ")

# Using a fixed date that exists in the mock XML data
TARGET_DATETIME = datetime(2025, 10, 31, 18, 0, 0)

# Fixed date matching the Generation.xml and Load.xml mocks
PRODUCTION_TARGET_DATETIME = datetime(2026, 7, 1, 12, 0, 0)


def _is_generation_request(request) -> bool:
    return "<Generation" in request.text


def _is_load_request(request) -> bool:
    return "<Load" in request.text


@pytest.fixture
def mock_good_response(requests_mock):
    """
    Mocks the CEPS API with a "good" response containing expected data.
    """

    data = base_path_to_mock / "CrossborderPowerFlows.xml"
    requests_mock.register_uri(
        POST,
        CZ.url,
        content=data.read_bytes(),
    )


@pytest.fixture
def mock_no_data_response(requests_mock):
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

    requests_mock.register_uri(POST, CZ.url, text=mock_xml_content)


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

    assert snapshot(extension_class=SingleFileAmberSnapshotExtension) == result


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


@pytest.fixture
def mock_production_response(requests_mock):
    """
    Mocks the CEPS API for fetch_production. Generation and Load POST to the
    same endpoint, so the two responses are matched on the SOAP body.
    """

    requests_mock.register_uri(
        POST,
        CZ.url,
        additional_matcher=_is_generation_request,
        content=(base_path_to_mock / "Generation.xml").read_bytes(),
    )
    requests_mock.register_uri(
        POST,
        CZ.url,
        additional_matcher=_is_load_request,
        content=(base_path_to_mock / "Load.xml").read_bytes(),
    )


@pytest.fixture
def mock_production_response_without_load_data(requests_mock):
    """
    Mocks the CEPS API with a valid Generation response but a Load response
    that is missing the <data> tag.
    """

    requests_mock.register_uri(
        POST,
        CZ.url,
        additional_matcher=_is_generation_request,
        content=(base_path_to_mock / "Generation.xml").read_bytes(),
    )
    mock_load_content = (
        '<root xmlns="https://www.ceps.cz/CepsData/StructuredData/1.0">'
        "<information><name>Load</name></information>"
        '<series><serie id="value1" name="Load including pumping [MW]" />'
        '<serie id="value2" name="Load [MW]" /></series>'
        "</root>"
    )
    requests_mock.register_uri(
        POST,
        CZ.url,
        additional_matcher=_is_load_request,
        text=mock_load_content,
    )


def test_fetch_production(session, snapshot, mock_production_response):
    result = CZ.fetch_production(
        zone_key=ZoneKey("CZ"),
        session=session,
        target_datetime=PRODUCTION_TARGET_DATETIME,
    )

    assert snapshot(extension_class=SingleFileAmberSnapshotExtension) == result


def test_fetch_production_storage(session, mock_production_response):
    result = CZ.fetch_production(
        zone_key=ZoneKey("CZ"),
        session=session,
        target_datetime=PRODUCTION_TARGET_DATETIME,
    )

    by_datetime = {event["datetime"].isoformat(): event for event in result}

    # 06:30: pumped storage generating 162.5 MW, no pumping (both Load series equal)
    discharging = by_datetime["2026-07-01T06:30:00+02:00"]
    assert discharging["storage"]["hydro"] == -162.5

    # 12:00: no pumped storage generation, pumping 9777.6 - 9289.934 MW
    pumping = by_datetime["2026-07-01T12:00:00+02:00"]
    assert pumping["storage"]["hydro"] == pytest.approx(487.666)


def test_fetch_production_without_load_data(
    session, mock_production_response_without_load_data
):
    result = CZ.fetch_production(
        zone_key=ZoneKey("CZ"),
        session=session,
        target_datetime=PRODUCTION_TARGET_DATETIME,
    )

    # production events are still returned, with storage from generation only
    assert len(result) == 25
    assert result[2]["storage"]["hydro"] == -162.5


def test_fetch_production_with_load_error(session, requests_mock):
    requests_mock.register_uri(
        POST,
        CZ.url,
        additional_matcher=_is_generation_request,
        content=(base_path_to_mock / "Generation.xml").read_bytes(),
    )
    requests_mock.register_uri(
        POST,
        CZ.url,
        additional_matcher=_is_load_request,
        status_code=500,
    )

    result = CZ.fetch_production(
        zone_key=ZoneKey("CZ"),
        session=session,
        target_datetime=PRODUCTION_TARGET_DATETIME,
    )

    # a failing Load request only costs the pumping enrichment
    assert len(result) == 25
    assert result[2]["storage"]["hydro"] == -162.5


def test_fetch_production_raises_exception_on_no_data(session, requests_mock):
    mock_xml_content = (
        '<root xmlns="https://www.ceps.cz/CepsData/StructuredData/1.0">'
        "<information><name>Generation</name></information>"
        '<series><serie id="value1" name="TPP [MW]" /></series>'
        "</root>"
    )
    requests_mock.register_uri(POST, CZ.url, text=mock_xml_content)

    with pytest.raises(ParserException):
        CZ.fetch_production(
            zone_key=ZoneKey("CZ"),
            session=session,
            target_datetime=PRODUCTION_TARGET_DATETIME,
        )


def test_get_pumping_clamps_negative_diff(session, requests_mock):
    mock_load_content = (
        '<root xmlns="https://www.ceps.cz/CepsData/StructuredData/1.0">'
        "<information><name>Load</name></information>"
        '<series><serie id="value1" name="Load including pumping [MW]" />'
        '<serie id="value2" name="Load [MW]" /></series>'
        '<data><item date="2026-07-01T06:00:00+02:00" value1="7000" value2="7000.4" />'
        '<item date="2026-07-01T06:15:00+02:00" value1="7500" value2="7100" /></data>'
        "</root>"
    )
    requests_mock.register_uri(POST, CZ.url, text=mock_load_content)

    result = CZ.get_pumping_by_datetime(
        session=session,
        date_from=datetime(2026, 7, 1, 6, 0, 0),
        date_to=datetime(2026, 7, 1, 6, 15, 0),
        zone_key=ZoneKey("CZ"),
        logger=getLogger(__name__),
    )

    # negative rounding artifacts clamp to zero instead of reading as discharge
    assert result[datetime.fromisoformat("2026-07-01T06:00:00+02:00")] == 0.0
    assert result[datetime.fromisoformat("2026-07-01T06:15:00+02:00")] == 400.0


def test_get_pumping_returns_empty_on_missing_series(session, requests_mock):
    mock_load_content = (
        '<root xmlns="https://www.ceps.cz/CepsData/StructuredData/1.0">'
        "<information><name>Load</name></information>"
        '<series><serie id="value1" name="Load [MW]" /></series>'
        '<data><item date="2026-07-01T06:00:00+02:00" value1="7000" /></data>'
        "</root>"
    )
    requests_mock.register_uri(POST, CZ.url, text=mock_load_content)

    result = CZ.get_pumping_by_datetime(
        session=session,
        date_from=datetime(2026, 7, 1, 6, 0, 0),
        date_to=datetime(2026, 7, 1, 6, 15, 0),
        zone_key=ZoneKey("CZ"),
        logger=getLogger(__name__),
    )

    assert result == {}
