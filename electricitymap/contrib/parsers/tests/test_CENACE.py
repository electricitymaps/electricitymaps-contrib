#!/usr/bin/env python3
"""Tests for the CENACE parser."""

import json
import urllib
from datetime import datetime

import freezegun
import pytest
from bs4 import BeautifulSoup
from requests_mock import ANY, GET, POST
from zoneinfo import ZoneInfo

from electricitymap.contrib.lib.types import ZoneKey
from electricitymap.contrib.parsers.CENACE import (
    MX_PRODUCTION_URL,
    fetch_consumption,
    fetch_production,
    parse_month_from_html,
)


@pytest.fixture
def production_adapter():
    """Create a fresh adapter for production parser tests."""
    from requests_mock import Adapter
    return Adapter()


@pytest.fixture
def production_session(production_adapter):
    """Create a session with the production adapter."""
    from requests import Session
    session = Session()
    session.mount("http://", production_adapter)
    session.mount("https://", production_adapter)
    return session


@pytest.fixture(autouse=True)
def setup_production_mocks(production_adapter):
    """Setup mocks for production parser tests."""
    # Clear any previous request history
    production_adapter.request_history.clear()

    # Register GET request for initial page
    # The HTML contains "noviembre de 2025" (November 2025)
    with open(
        "electricitymap/contrib/parsers/tests/mocks/CENACE/EnergiaGeneradaTipoTec_current.html",
        "rb",
    ) as f:
        production_adapter.register_uri("GET", MX_PRODUCTION_URL, content=f.read())


@pytest.fixture(autouse=True)
def mock_response(adapter):
    with open(
        "electricitymap/contrib/parsers/tests/mocks/CENACE/DemandaRegional.html", "rb"
    ) as data:
        adapter.register_uri(ANY, ANY, content=data.read())


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


def test_fetch_production_current(production_session, production_adapter):
    """Test fetching production for current date (November 2025).

    Expected flow:
    1. GET initial page (shows November 2025)
    2. POST to download CSV (month matches)
    """
    production_adapter.request_history.clear()

    # Register POST request for CSV download (current month)
    # This request includes both date parameter and button parameters
    with open(
        "electricitymap/contrib/parsers/tests/mocks/CENACE/EnergiaGeneradaTipoTec_2025-11.csv",
        "rb",
    ) as f:
        production_adapter.register_uri(
            POST,
            MX_PRODUCTION_URL,
            content=f.read(),
            headers={"Content-Type": "text/plain"}
        )

    data = fetch_production(ZoneKey("MX"), production_session)

    # Assertions on response data
    assert len(data) > 0
    assert data[0]["zoneKey"] == "MX"
    assert "production" in data[0]

    # GET: initial page (shows November 2025), POST: download CSV
    assert len(production_adapter.request_history) == 2
    assert production_adapter.request_history[0].method == "GET"
    assert production_adapter.request_history[1].method == "POST"


def test_fetch_production_historical(production_session, production_adapter):
    """Test fetching production for historical date (January 2025).

    Expected flow:
    1. GET initial page (shows November 2025)
    2. POST to refresh HTML to January 2025 (month is before)
    3. POST to download CSV
    """
    production_adapter.request_history.clear()

    target_dt = datetime(2025, 1, 1, 12, 0, 0, tzinfo=ZoneInfo("America/Mexico_City"))

    # Register POST request handler that returns different responses based on request body
    def post_callback(request, context):
        # Check if request has date parameter (AD) but not button parameters
        # This indicates a month reload request for historical data
        request_body = request.body.decode('utf-8') if isinstance(request.body, bytes) else request.body
        has_ad = "ctl00_ContentPlaceHolder1_FechaConsulta_AD" in request_body
        has_button = "gbccolumn.x" in request_body

        if has_ad and not has_button:
            # Month reload request - return HTML
            with open(
                "electricitymap/contrib/parsers/tests/mocks/CENACE/EnergiaGeneradaTipoTec_2025-01.html",
                "rb",
            ) as f:
                context.status_code = 200
                context.headers["Content-Type"] = "text/html"
                return f.read()
        # Otherwise, return CSV (this handles both current month and historical month CSV download)
        else:
            with open(
                "electricitymap/contrib/parsers/tests/mocks/CENACE/EnergiaGeneradaTipoTec_2025-01.csv",
                "rb",
            ) as f:
                context.status_code = 200
                context.headers["Content-Type"] = "text/plain"
                return f.read()

    production_adapter.register_uri(POST, MX_PRODUCTION_URL, content=post_callback)

    data = fetch_production(ZoneKey("MX"), production_session, target_datetime=target_dt)

    # Assertions on response data
    assert len(data) > 0
    assert data[0]["zoneKey"] == "MX"
    assert data[0]["datetime"].date() == target_dt.date()

    # GET: initial page (shows November 2025),
    # POST: refresh to January 2025 (returns HTML), POST: download CSV
    assert len(production_adapter.request_history) == 3
    assert production_adapter.request_history[0].method == "GET"
    assert production_adapter.request_history[1].method == "POST"
    assert production_adapter.request_history[2].method == "POST"


def test_parse_month_from_html():
    """Test the parse_month_from_html function."""
    # Test with November 2025 HTML
    with open(
        "electricitymap/contrib/parsers/tests/mocks/CENACE/EnergiaGeneradaTipoTec_current.html",
        "r",
    ) as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    date = parse_month_from_html(soup)
    assert date.month == 11  # November
    assert date.year == 2025
    assert date.day == 1  # First day of month

    # Test with January 2025 HTML
    with open(
        "electricitymap/contrib/parsers/tests/mocks/CENACE/EnergiaGeneradaTipoTec_2025-01.html",
        "r",
    ) as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    date = parse_month_from_html(soup)
    assert date.month == 1  # January
    assert date.year == 2025
    assert date.day == 1  # First day of month


def test_fetch_production_future(production_session, production_adapter):
    """Test that fetching production for future date raises error.

    Expected flow:
    1. GET initial page (shows November 2025)
    2. Raise error (requested month is after current month)
    """
    production_adapter.request_history.clear()

    future_dt = datetime(2026, 1, 15, 12, 0, 0, tzinfo=ZoneInfo("America/Mexico_City"))

    with pytest.raises(Exception) as excinfo:
        fetch_production(ZoneKey("MX"), production_session, target_datetime=future_dt)

    assert " has no data yet, try " in str(excinfo.value)

    # Verify requests were made (1 GET only - error before POST)
    assert len(production_adapter.request_history) == 1
    assert production_adapter.request_history[0].method == "GET"
