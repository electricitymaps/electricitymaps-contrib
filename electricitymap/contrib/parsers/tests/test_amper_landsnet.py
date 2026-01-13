import json
from importlib import resources

from requests_mock import GET

from electricitymap.contrib.parsers.amper_landsnet import SOURCE_URL, fetch_production
from electricitymap.types import ZoneKey


def test_fetch_production(adapter, session, snapshot):
    adapter.register_uri(
        GET,
        SOURCE_URL,
        json=json.loads(
            resources.files("electricitymap.contrib.parsers.tests.mocks.amper_landsnet")
            .joinpath("production.json")
            .read_text()
        ),
    )
    assert snapshot == fetch_production(
        zone_key=ZoneKey("IS"),
        session=session,
    )
