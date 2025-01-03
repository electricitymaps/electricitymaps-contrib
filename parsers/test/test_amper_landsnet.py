import json
from importlib import resources

from requests_mock import GET

from electricitymap.contrib.lib.types import ZoneKey
from parsers.amper_landsnet import SOURCE_URL, fetch_production


def test_fetch_production(adapter, session, snapshot):
    adapter.register_uri(
        GET,
        SOURCE_URL,
        json=json.loads(
            resources.files("parsers.test.mocks.amper_landsnet")
            .joinpath("production.json")
            .read_text()
        ),
    )
    production = fetch_production(
        zone_key=ZoneKey("IS"),
        session=session,
    )

    assert snapshot == [
        {
            "datetime": element["datetime"].isoformat(),
            "production": element["production"],
            "storage": element["storage"],
            "source": element["source"],
            "zoneKey": element["zoneKey"],
            "sourceType": element["sourceType"].value,
        }
        for element in production
    ]
