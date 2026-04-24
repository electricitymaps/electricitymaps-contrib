from importlib import resources

import pytest
from freezegun import freeze_time
from requests_mock import GET

from electricitymap.contrib.parsers.TH import (
    MEA_BASEPRICE_URL,
    MEA_FT_URL,
    fetch_price,
)
from electricitymap.contrib.types import ZoneKey


@pytest.fixture(autouse=True)
def mock_response(adapter):
    adapter.register_uri(
        GET,
        MEA_BASEPRICE_URL,
        content=resources.files("electricitymap.contrib.parsers.tests.mocks.TH")
        .joinpath("mea_baseprice.html")
        .read_bytes(),
    )
    adapter.register_uri(
        GET,
        MEA_FT_URL,
        content=resources.files("electricitymap.contrib.parsers.tests.mocks.TH")
        .joinpath("mea_ft.html")
        .read_bytes(),
    )


@freeze_time("2024-04-15 12:00:00+07:00")
def test_snapshot_fetch_price(session, snapshot):
    """Snapshot the full fetch_price output. Exercises BeautifulSoup(lxml)
    parsing over both MEA HTML pages."""
    assert snapshot == fetch_price(zone_key=ZoneKey("TH"), session=session)
