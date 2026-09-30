import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import freezegun
import pytest
from requests_mock import GET, POST

from electricitymap.contrib.lib.models.events import EventSourceType
from electricitymap.contrib.parsers.CENACE import (
    MX_EXCHANGE_URL,
    MX_GENERATION_FORECAST_URL,
    fetch_consumption,
    fetch_generation_forecast,
)
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.types import ZoneKey

MOCKS = Path(__file__).parent / "mocks" / "CENACE"
TIMEZONE = ZoneInfo("America/Mexico_City")


@pytest.fixture(autouse=True)
def mock_response(requests_mock):
    with open(
        "electricitymap/contrib/parsers/tests/mocks/CENACE/DemandaRegional.html", "rb"
    ) as data:
        requests_mock.register_uri(GET, MX_EXCHANGE_URL, content=data.read())


@pytest.fixture
def mock_generation_forecast(requests_mock):
    """Registers a forecast payload. The filename is always explicit, since the
    two windows this parser has to handle differ only by which mock is used."""

    def _register(filename: str):
        requests_mock.register_uri(
            POST,
            MX_GENERATION_FORECAST_URL,
            json=json.loads(MOCKS.joinpath(filename).read_text()),
        )

    return _register


@freezegun.freeze_time("2021-01-01 00:00:00")
def test_fetch_consumption_MX_OC(session):
    data = fetch_consumption(ZoneKey("MX-OC"), session)
    assert data[0]["zoneKey"] == "MX-OC"
    assert data[0]["datetime"] == datetime.now(ZoneInfo("America/Mexico_City"))
    assert data[0]["consumption"] == 8519.0


@freezegun.freeze_time("2021-01-01 00:00:00")
def test_fetch_consumption_MX_BC(session):
    data = fetch_consumption(ZoneKey("MX-BC"), session)
    assert data[0]["zoneKey"] == "MX-BC"
    assert data[0]["datetime"] == datetime.now(ZoneInfo("America/Tijuana"))
    assert data[0]["consumption"] == 1587.0


@freezegun.freeze_time("2021-01-01 00:00:00")
def test_fetch_consumption_BCS(session):
    data = fetch_consumption(ZoneKey("MX-BCS"), session)
    assert len(data) == 0


# CENACE labels hours 1-24, where hour N starts at N-1. 2026-08-12 14:00 UTC is
# 08:00 in Mexico City, partway through the day the mocks were captured on.
@freezegun.freeze_time("2026-08-12 14:00:00")
def test_fetch_generation_forecast(session, mock_generation_forecast):
    mock_generation_forecast("GraficaDemanda.json")

    data = fetch_generation_forecast(ZoneKey("MX"), session)

    assert len(data) == 24
    assert data[0]["zoneKey"] == "MX"
    assert data[0]["source"] == "cenace.gob.mx"
    assert data[0]["sourceType"] == EventSourceType.forecasted
    # hora 1 is midnight, not 01:00 — the mapping this parser exists to get right.
    assert data[0]["datetime"] == datetime(2026, 8, 12, 0, tzinfo=TIMEZONE)
    assert data[0]["value"] == 46721.0
    # hora 24 is 23:00 of the same day, not midnight of the next.
    assert data[-1]["datetime"] == datetime(2026, 8, 12, 23, tzinfo=TIMEZONE)
    assert data[-1]["value"] == 48502.0


@freezegun.freeze_time("2026-08-12 14:00:00")
def test_fetch_generation_forecast_with_previous_day_row(
    session, mock_generation_forecast
):
    """The window is not a fixed length.

    The dashboard sometimes prepends hour 24 of the previous day, so the same
    request returns 24 or 25 rows minutes apart. The extra row must land on
    yesterday and must not shift the rest of the window.
    """
    mock_generation_forecast("GraficaDemanda_previous_day_row.json")

    data = fetch_generation_forecast(ZoneKey("MX"), session)

    assert len(data) == 25
    assert data[0]["datetime"] == datetime(2026, 8, 11, 23, tzinfo=TIMEZONE)
    assert data[0]["value"] == 48450.0
    # Every other row keeps the timestamp it had in the 24-row window.
    assert data[1]["datetime"] == datetime(2026, 8, 12, 0, tzinfo=TIMEZONE)
    assert data[1]["value"] == 46721.0
    assert data[-1]["datetime"] == datetime(2026, 8, 12, 23, tzinfo=TIMEZONE)


@freezegun.freeze_time("2026-08-12 14:00:00")
def test_fetch_generation_forecast_skips_blank_values(session, requests_mock):
    """Future hours arrive as ' ' rather than null once the forecast is absent."""
    rows = [
        {"hora": "1", "valorPronostico": "46721"},
        {"hora": "2", "valorPronostico": " "},
        {"hora": "3", "valorPronostico": "43631"},
    ]
    requests_mock.register_uri(
        POST, MX_GENERATION_FORECAST_URL, json={"d": json.dumps(rows)}
    )

    data = fetch_generation_forecast(ZoneKey("MX"), session)

    assert [event["datetime"].hour for event in data] == [0, 2]


@freezegun.freeze_time("2026-08-12 14:00:00")
def test_fetch_generation_forecast_rejects_non_contiguous_hours(session, requests_mock):
    """A gap would silently shift every later timestamp, so it must raise."""
    rows = [
        {"hora": "1", "valorPronostico": "46721"},
        {"hora": "3", "valorPronostico": "43631"},
    ]
    requests_mock.register_uri(
        POST, MX_GENERATION_FORECAST_URL, json={"d": json.dumps(rows)}
    )

    with pytest.raises(ParserException, match="Unexpected hour ordering"):
        fetch_generation_forecast(ZoneKey("MX"), session)


@freezegun.freeze_time("2026-08-12 14:00:00")
def test_fetch_generation_forecast_requires_an_anchor(session, requests_mock):
    """Without a row for hour 1 the window cannot be dated at all."""
    rows = [{"hora": "23", "valorPronostico": "49994"}]
    requests_mock.register_uri(
        POST, MX_GENERATION_FORECAST_URL, json={"d": json.dumps(rows)}
    )

    with pytest.raises(ParserException, match="no row reports hora 1"):
        fetch_generation_forecast(ZoneKey("MX"), session)


def test_fetch_generation_forecast_rejects_other_zones(session):
    with pytest.raises(ValueError):
        fetch_generation_forecast(ZoneKey("MX-OC"), session)


def test_fetch_generation_forecast_rejects_past_dates(session):
    with pytest.raises(NotImplementedError):
        fetch_generation_forecast(
            ZoneKey("MX"),
            session,
            target_datetime=datetime(2026, 8, 1, tzinfo=TIMEZONE),
        )
