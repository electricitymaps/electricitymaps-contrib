import os

from requests import Session
from requests_mock import GET, Adapter

from electricitymap.contrib.lib.types import ZoneKey
from parsers.FR import API_ENDPOINT, fetch_production


def test_production(snapshot):
    session = Session()
    adapter = Adapter()
    os.environ["RESEAUX_ENERGIES_TOKEN"] = "test_token"
    session.mount("https://", adapter)
    with open("parsers/test/mocks/FR/response.json", "rb") as mock_file:
        adapter.register_uri(
            GET,
            API_ENDPOINT,
            content=mock_file.read(),
        )

    assert snapshot == fetch_production(
        zone_key=ZoneKey("FR"),
        session=session,
    )
