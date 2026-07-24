import json
from datetime import datetime
from importlib import resources
from unittest.mock import MagicMock

import pytest
from requests_mock import ANY
from syrupy.extensions.single_file import SingleFileAmberSnapshotExtension

from electricitymap.contrib.parsers import FR_O
from electricitymap.contrib.types import ZoneKey

# Each production zone has a real sample of its live dataset saved as a mock.
# Snapshotting the parsed output guards against silent regressions when the
# upstream APIs add, rename or remove fields.
PRODUCTION_MOCKS = {
    "FR-COR": "FR_COR_live.json",
    "GP": "FR_GP_live.json",
    "RE": "FR_RE_live.json",
    "GF": "FR_GF_live.json",
    "MQ": "FR_MQ_live.json",
}


@pytest.fixture
def snapshot(snapshot):
    # Store each snapshot in its own file rather than a single shared .ambr.
    return snapshot.use_extension(SingleFileAmberSnapshotExtension)


def _load_mock(filename: str):
    return json.loads(
        resources.files("electricitymap.contrib.parsers.tests.mocks.FR_O")
        .joinpath(filename)
        .read_text(encoding="utf-8")
    )


@pytest.mark.parametrize("zone_key", PRODUCTION_MOCKS)
def test_fetch_production(requests_mock, session, snapshot, zone_key):
    requests_mock.register_uri(ANY, ANY, json=_load_mock(PRODUCTION_MOCKS[zone_key]))
    logger = MagicMock()
    data_list = FR_O.fetch_production(ZoneKey(zone_key), session, logger=logger)
    assert data_list is not None
    # Every field returned by the API must be either mapped to a mode, mapped to
    # storage or explicitly ignored. A warning means an unhandled key slipped
    # through (e.g. a new aggregate/share field or an unmapped generation mode).
    logger.warning.assert_not_called()
    assert snapshot == data_list


def test_fetch_production_historical(requests_mock, session, snapshot):
    # Historical data comes from the national dataset, which uses a different,
    # more aggregated schema (*_mw suffixes) than the live feeds. Every field it
    # returns must be mapped or ignored - no warnings - and thermal/bagasse must
    # collapse to the 'unknown' mode since they cannot be split.
    requests_mock.register_uri(ANY, ANY, json=_load_mock("FR_COR_historical.json"))
    logger = MagicMock()
    data_list = FR_O.fetch_production(
        ZoneKey("FR-COR"), session, datetime(2024, 1, 1), logger=logger
    )
    assert data_list is not None
    logger.warning.assert_not_called()
    assert snapshot == data_list


def test_fetch_price(requests_mock, session, snapshot):
    requests_mock.register_uri(ANY, ANY, json=_load_mock("FR_RE.json"))
    data_list = FR_O.fetch_price(ZoneKey("RE"), session, datetime(2018, 1, 1))
    assert data_list is not None
    assert snapshot == data_list
