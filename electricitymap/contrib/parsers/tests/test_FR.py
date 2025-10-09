import os

from requests_mock import GET

from electricitymap.contrib.lib.types import ZoneKey
from electricitymap.contrib.parsers.FR import API_ENDPOINT, fetch_production


def test_production(adapter, session, snapshot):
    os.environ["RESEAUX_ENERGIES_TOKEN"] = "test_token"
    with open(
        "electricitymap/contrib/parsers/tests/mocks/FR/response.json", "rb"
    ) as mock_file:
        adapter.register_uri(
            GET,
            API_ENDPOINT,
            content=mock_file.read(),
        )

    assert snapshot == fetch_production(
        zone_key=ZoneKey("FR"),
        session=session,
    )
