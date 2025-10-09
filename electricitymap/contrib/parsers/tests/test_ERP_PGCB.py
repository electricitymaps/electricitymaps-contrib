from datetime import datetime
from importlib import resources

import pytest
from requests_mock import ANY, GET

from electricitymap.contrib.lib.types import ZoneKey
from electricitymap.contrib.parsers.ERP_PGCB import (
    fetch_consumption,
    fetch_exchange,
    fetch_production,
)

historical_dt = datetime.fromisoformat("2025-01-01 00:00:00 +06:00")


def _load_mock_response(adapter, target_datetime):
    mock_data_file = "latest.html"
    if target_datetime:
        mock_data_file = "historical.html"

    adapter.register_uri(
        GET,
        ANY,
        text=resources.files("electricitymap.contrib.parsers.tests.mocks.ERP_PGCB")
        .joinpath(mock_data_file)
        .read_text(),
    )


@pytest.mark.parametrize("target_datetime", [None, historical_dt])
def test_fetch_consumption(adapter, session, snapshot, target_datetime):
    _load_mock_response(adapter, target_datetime)
    assert snapshot == fetch_consumption(session=session)


@pytest.mark.parametrize("target_datetime", [None, historical_dt])
def test_exchanges(adapter, session, snapshot, target_datetime):
    _load_mock_response(adapter, target_datetime)
    assert snapshot == fetch_exchange(ZoneKey("BD"), ZoneKey("IN-NE"), session=session)


@pytest.mark.parametrize("target_datetime", [None, historical_dt])
def test_fetch_production(adapter, session, snapshot, target_datetime):
    _load_mock_response(adapter, target_datetime)
    assert snapshot == fetch_production(session=session)
