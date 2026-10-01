import os
from pathlib import Path

import pytest
from requests_mock import ANY, GET

from electricitymap.contrib.lib.models.events import EventSourceType
from electricitymap.contrib.parsers import ENTSOE
from electricitymap.contrib.parsers.ENTSOE_price_overrides import (
    fetch_price,
    fetch_price_day_ahead,
)
from electricitymap.contrib.types import DayAheadAuction, ZoneKey

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


@pytest.mark.parametrize("zone", ["AX", "LU"])
def test_fetch_price_day_ahead(requests_mock, session, zone):
    data = base_path_to_mock / "FR_prices.xml"
    requests_mock.register_uri(GET, ANY, content=data.read_bytes())

    rows = fetch_price_day_ahead(ZoneKey(zone), session)

    assert rows
    assert {row["zoneKey"] for row in rows} == {zone}
    assert {row["auction"] for row in rows} == {DayAheadAuction.SDAC}
    assert {row["sourceType"] for row in rows} == {EventSourceType.published}
    assert {row["publishedAt"] for row in rows} == {None}
    # Same points as the old path.
    assert [(row["datetime"], row["price"]) for row in rows] == [
        (row["datetime"], row["price"]) for row in fetch_price(ZoneKey(zone), session)
    ]


def test_fetch_price_day_ahead_lu_queries_de_lu_domain(requests_mock, session):
    data = base_path_to_mock / "FR_prices.xml"
    requests_mock.register_uri(GET, ANY, content=data.read_bytes())

    fetch_price_day_ahead(ZoneKey("LU"), session)

    domain = ENTSOE.ENTSOE_DOMAIN_MAPPINGS["DE-LU"].lower()
    assert requests_mock.last_request.qs["in_domain"] == [domain]
    assert requests_mock.last_request.qs["out_domain"] == [domain]
