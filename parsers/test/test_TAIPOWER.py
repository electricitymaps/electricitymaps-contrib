from requests import Session
from requests_mock import GET, Adapter

from electricitymap.contrib.lib.types import ZoneKey
from parsers.TAIPOWER import PRODUCTION_URL, fetch_production


def test_production(snapshot):
    session = Session()
    adapter = Adapter()
    session.mount("http://", adapter)
    with open("parsers/test/mocks/TAIPOWER/genary.json", "rb") as mock_file:
        adapter.register_uri(
            GET,
            PRODUCTION_URL,
            content=mock_file.read(),
        )

    assert snapshot == fetch_production(
        zone_key=ZoneKey("TW"),
        session=session,
    )
