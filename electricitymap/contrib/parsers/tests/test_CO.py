from datetime import datetime
from importlib import resources
from json import loads
from unittest.mock import patch

import pandas as pd
from requests_mock import ANY

from electricitymap.contrib.parsers.CO import (
    CO_DEMAND_URL,
    fetch_consumption,
    fetch_price,
    fetch_production,
)

mock_files = resources.files("electricitymap.contrib.parsers.tests.mocks.CO")


def test_fetch_consumption_live(adapter, session, snapshot):
    adapter.register_uri(
        ANY,
        CO_DEMAND_URL,
        json=loads(mock_files.joinpath("cons_live.json").read_text()),
    )
    assert snapshot == fetch_consumption(session=session)


@patch("pydataxm.pydataxm.ReadDB")
def test_fetch_consumption_dt(mock_readdb, snapshot):
    readdb = mock_readdb.return_value
    readdb.request_data.side_effect = [
        pd.read_json(mock_files.joinpath("cons_dt.json")),
    ]
    dt = datetime.fromisoformat("2025-01-01T00:00:00-05:00")
    assert snapshot == fetch_consumption(target_datetime=dt)


@patch("pydataxm.pydataxm.ReadDB")
def test_fetch_production_live(mock_readdb, snapshot):
    readdb = mock_readdb.return_value
    readdb.request_data.side_effect = [
        pd.read_json(mock_files.joinpath("prod1_live.json")),
        pd.read_json(mock_files.joinpath("prod2_live.json")),
    ]
    assert snapshot == fetch_production()


@patch("pydataxm.pydataxm.ReadDB")
def test_fetch_production_dt(mock_readdb, snapshot):
    readdb = mock_readdb.return_value
    readdb.request_data.side_effect = [
        pd.read_json(mock_files.joinpath("prod1_dt.json")),
        pd.read_json(mock_files.joinpath("prod2_dt.json")),
    ]
    dt = datetime.fromisoformat("2025-01-01T00:00:00-05:00")
    assert snapshot == fetch_production(target_datetime=dt)


@patch("pydataxm.pydataxm.ReadDB")
def test_fetch_price_live(mock_readdb, snapshot):
    readdb = mock_readdb.return_value
    readdb.request_data.side_effect = [
        pd.read_json(mock_files.joinpath("price_live.json")),
    ]
    assert snapshot == fetch_price()


@patch("pydataxm.pydataxm.ReadDB")
def test_fetch_price_dt(mock_readdb, snapshot):
    readdb = mock_readdb.return_value
    readdb.request_data.side_effect = [
        pd.read_json(mock_files.joinpath("price_dt.json")),
    ]
    dt = datetime.fromisoformat("2025-01-01T00:00:00-05:00")
    assert snapshot == fetch_price(target_datetime=dt)
