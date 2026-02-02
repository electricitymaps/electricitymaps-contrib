import json
from importlib import resources

from requests_mock import ANY, GET

from electricitymap.contrib.parsers.NESO import fetch_production
from electricitymap.contrib.types import ZoneKey


def test_fetch_production(adapter, session, snapshot):
    adapter.register_uri(
        GET,
        ANY,
        json=json.loads(
            resources.files("electricitymap.contrib.parsers.tests.mocks.NESO")
            .joinpath("production.json")
            .read_text()
        ),
    )

    assert snapshot == fetch_production(
        zone_key=ZoneKey("GB"),
        session=session,
    )
