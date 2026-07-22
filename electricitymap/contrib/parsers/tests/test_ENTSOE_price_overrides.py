import os
from pathlib import Path

import pytest
from requests_mock import ANY, GET

from electricitymap.contrib.parsers.ENTSOE_price_overrides import fetch_price
from electricitymap.contrib.types import ZoneKey

base_path_to_mock = Path("electricitymap/contrib/parsers/tests/mocks/ENTSOE")


@pytest.fixture(autouse=True)
def entsoe_token_env():
    os.environ["ENTSOE_TOKEN"] = "token"


@pytest.mark.parametrize("zone", ["AX", "LU"])
def test_fetch_price(requests_mock, session, snapshot, zone):
    data = base_path_to_mock / "FR_prices.xml"
    requests_mock.register_uri(
        GET,
        ANY,
        content=data.read_bytes(),
    )
    assert snapshot == fetch_price(ZoneKey(zone), session)
