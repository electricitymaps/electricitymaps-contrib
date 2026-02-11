import json
from datetime import datetime, timezone
from importlib import resources

import pytest
from freezegun import freeze_time
from requests_mock import ANY, GET
from syrupy.extensions.single_file import SingleFileAmberSnapshotExtension

from electricitymap.contrib.parsers.MD import (
    fetch_consumption,
    fetch_exchange,
    fetch_exchange_forecast,
    fetch_price,
    fetch_production,
)
from electricitymap.contrib.types import ZoneKey

# the datetime corresponding to our mock live API response
frozen_live_time = freeze_time("2024-04-11 06:32:00")

# the target datetime corresponding to our mock historical API response
historical_datetime = datetime(2021, 7, 25, 12, tzinfo=timezone.utc)


@frozen_live_time
def test_fetch_consumption_live(adapter, session, snapshot):
    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("electricitymap.contrib.parsers.tests.mocks.MD")
            .joinpath("moldoelectrica_api_live.json")
            .read_text()
        ),
    )

    assert snapshot == fetch_consumption(session=session)


def test_fetch_consumption_historical(adapter, session, snapshot):
    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("electricitymap.contrib.parsers.tests.mocks.MD")
            .joinpath("moldoelectrica_api_historical_20210725.json")
            .read_text()
        ),
    )

    assert snapshot == fetch_consumption(
        target_datetime=historical_datetime, session=session
    )


@pytest.mark.parametrize("neighbor", ["RO", "UA"])
@frozen_live_time
def test_fetch_exchange_live(adapter, session, snapshot, neighbor):
    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("electricitymap.contrib.parsers.tests.mocks.MD")
            .joinpath("moldoelectrica_api_live.json")
            .read_text()
        ),
    )

    assert snapshot(extension_class=SingleFileAmberSnapshotExtension) == fetch_exchange(ZoneKey("MD"), ZoneKey(neighbor), session=session)


@pytest.mark.parametrize("neighbor", ["RO", "UA"])
def test_fetch_exchange_historical(adapter, session, snapshot, neighbor):
    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("electricitymap.contrib.parsers.tests.mocks.MD")
            .joinpath("moldoelectrica_api_historical_20210725.json")
            .read_text()
        ),
    )

    assert snapshot(
        extension_class=SingleFileAmberSnapshotExtension
    ) == fetch_exchange(
        ZoneKey("MD"),
        ZoneKey(neighbor),
        target_datetime=historical_datetime,
        session=session,
    )


@pytest.mark.parametrize("neighbor", ["RO", "UA"])
@frozen_live_time
def test_fetch_exchange_forecast_live(adapter, session, snapshot, neighbor):
    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("electricitymap.contrib.parsers.tests.mocks.MD")
            .joinpath("moldoelectrica_api_live.json")
            .read_text()
        ),
    )

    assert snapshot(
        extension_class=SingleFileAmberSnapshotExtension
    ) == fetch_exchange_forecast(
        ZoneKey("MD"), ZoneKey(neighbor), session=session
    )


@pytest.mark.parametrize("neighbor", ["RO", "UA"])
def test_fetch_exchange_forecast_historical(adapter, session, snapshot, neighbor):
    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("electricitymap.contrib.parsers.tests.mocks.MD")
            .joinpath("moldoelectrica_api_historical_20210725.json")
            .read_text()
        ),
    )

    assert snapshot(
        extension_class=SingleFileAmberSnapshotExtension
    ) == fetch_exchange_forecast(
        ZoneKey("MD"),
        ZoneKey(neighbor),
        target_datetime=historical_datetime,
        session=session,
    )


@frozen_live_time
def test_fetch_price_live(snapshot):
    assert snapshot == fetch_price()


@pytest.mark.parametrize(
    "historical_datetime",
    [
        datetime(2000, 1, 1, tzinfo=timezone.utc),
        datetime(2000, 4, 1, tzinfo=timezone.utc),
        datetime(2001, 10, 1, tzinfo=timezone.utc),
        datetime(2002, 9, 1, tzinfo=timezone.utc),
        datetime(2005, 9, 1, tzinfo=timezone.utc),
        datetime(2007, 8, 3, tzinfo=timezone.utc),
        datetime(2010, 1, 19, tzinfo=timezone.utc),
        datetime(2012, 5, 11, tzinfo=timezone.utc),
        datetime(2015, 7, 31, tzinfo=timezone.utc),
        datetime(2023, 12, 31, tzinfo=timezone.utc),
        datetime(2024, 3, 21, tzinfo=timezone.utc),
    ],
)
def test_fetch_price_historical(snapshot, historical_datetime):
    assert snapshot(extension_class=SingleFileAmberSnapshotExtension) == fetch_price(target_datetime=historical_datetime)


@frozen_live_time
def test_fetch_production_live(adapter, session, snapshot):
    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("electricitymap.contrib.parsers.tests.mocks.MD")
            .joinpath("moldoelectrica_api_live.json")
            .read_text()
        ),
    )

    assert snapshot == fetch_production(session=session)


def test_fetch_production_historical(adapter, session, snapshot):
    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("electricitymap.contrib.parsers.tests.mocks.MD")
            .joinpath("moldoelectrica_api_historical_20210725.json")
            .read_text()
        ),
    )

    assert snapshot == fetch_production(
        target_datetime=historical_datetime, session=session
    )
