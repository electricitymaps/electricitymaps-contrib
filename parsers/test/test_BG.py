import json
from datetime import UTC, datetime, timedelta
from importlib import resources

import pytest
from freezegun import freeze_time
from requests_mock import ANY, GET

from parsers.BG import fetch_production
from parsers.lib.exceptions import ParserException


@freeze_time("2024-01-01 12:00:00")
def test_fetch_production(adapter, session, snapshot):
    """That we can fetch the production mix at the current time."""
    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("parsers.test.mocks.BG")
            .joinpath("production_live.json")
            .read_text()
        ),
    )

    assert snapshot == fetch_production(session=session)


def test_fetch_production_raises_parser_exception_on_historical_data(adapter, session):
    """That a ParserException is raised if requesting historical data (not supported yet)."""
    adapter.register_uri(GET, ANY, json=[])

    with pytest.raises(
        ParserException, match="This parser is not yet able to parse historical data"
    ):
        historical_datetime = datetime.now(UTC) - timedelta(days=1)
        fetch_production(target_datetime=historical_datetime, session=session)
