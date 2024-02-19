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

    production = fetch_production(
        zone_key=ZoneKey("FR"),
        session=session,
    )
    snapshot.assert_match(
        [
            {
                "datetime": element["datetime"].isoformat(),
                "production": element["production"],
                "storage": element["storage"],
                "source": element["source"],
                "zoneKey": element["zoneKey"],
                "sourceType": "measured",
            }
            for element in production
        ]
    )
