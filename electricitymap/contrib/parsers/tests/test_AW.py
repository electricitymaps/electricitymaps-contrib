import json
from importlib import resources

from requests_mock import GET

from electricitymap.contrib.parsers.AW import PRODUCTION_URL, fetch_production
from electricitymap.contrib.types import ZoneKey


def test_fetch_production(adapter, session, snapshot):
    adapter.register_uri(
        GET,
        PRODUCTION_URL,
        json=json.loads(
            resources.files("electricitymap.contrib.parsers.tests.mocks.AW")
            .joinpath("production.json")
            .read_text()
        ),
    )
    assert snapshot == fetch_production(
        zone_key=ZoneKey("AW"),
        session=session,
    )
