import json
from datetime import datetime, timedelta, timezone
from importlib import resources

import pytest
from freezegun import freeze_time
from requests_mock import ANY, GET

from parsers.CR import fetch_exchange, fetch_production
from parsers.lib.exceptions import ParserException


@freeze_time("2024-01-01 12:00:00")
def test_fetch_production_live(adapter, session, snapshot):
    """That we can fetch the production mix at the current time."""
    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("parsers.test.mocks.CR")
            .joinpath("production_live.json")
            .read_text()
        ),
    )

    assert snapshot == fetch_production(session=session)


def test_fetch_production_historical(adapter, session, snapshot):
    """That we can fetch historical energy production values."""
    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("parsers.test.mocks.CR")
            .joinpath("production_20210716.json")
            .read_text()
        ),
    )

    historical_datetime = datetime(2021, 7, 16, 16, 20, 30, tzinfo=timezone.utc)
    assert snapshot == fetch_production(
        target_datetime=historical_datetime.astimezone(timezone.utc),
        session=session,
    )


@freeze_time("2024-01-01 12:00:00")
def test_fetch_exchange_live(adapter, session, snapshot):
    """That we can fetch the last known power exchanges."""
    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("parsers.test.mocks.CR")
            .joinpath("exchange_live.json")
            .read_text()
        ),
    )

    assert snapshot == fetch_exchange(session=session)


def test_fetch_exchange_raises_parser_exception_on_historical_data(adapter, session):
    """That a ParserException is raised if requesting historical data (not supported yet)."""
    adapter.register_uri(GET, ANY, json=[])

    with pytest.raises(
        ParserException, match="This parser is not yet able to parse historical data"
    ):
        historical_datetime = datetime.now(timezone.utc) - timedelta(days=1)
        fetch_exchange(target_datetime=historical_datetime, session=session)
