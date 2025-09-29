from datetime import datetime, timedelta, timezone
from importlib import resources

import pytest
from freezegun import freeze_time
from requests_mock import ANY, GET

from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.parsers.PF import fetch_production


@pytest.fixture(autouse=True)
def mock_response(adapter):
    adapter.register_uri(
        GET,
        ANY,
        text=resources.files("electricitymap.contrib.parsers.tests.mocks.PF")
        .joinpath("production_live.html")
        .read_text(),
    )


@freeze_time("2024-01-01 12:00:00")
def test_fetch_production_live(session, snapshot):
    """That we can fetch the production mix at the current time."""
    assert snapshot == fetch_production(session=session)


def test_fetch_production_raises_parser_exception_on_historical_data(adapter, session):
    """That a ParserException is raised if requesting historical data (not supported yet)."""
    adapter.register_uri(GET, ANY, json=[])

    with pytest.raises(
        ParserException, match="This parser is not yet able to parse historical data"
    ):
        historical_datetime = datetime.now(timezone.utc) - timedelta(days=1)
        fetch_production(target_datetime=historical_datetime, session=session)
