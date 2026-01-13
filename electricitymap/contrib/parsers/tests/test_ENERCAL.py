from importlib import resources

from requests_mock import ANY, GET

from electricitymap.contrib.parsers import ENERCAL
from electricitymap.types import ZoneKey


def test_production_with_snapshot(adapter, session, snapshot):
    raw_data = (
        resources.files("electricitymap.contrib.parsers.tests.mocks.ENERCAL")
        .joinpath("production.json")
        .read_bytes()
    )
    adapter.register_uri(
        GET,
        ANY,
        content=raw_data,
    )
    assert snapshot == ENERCAL.fetch_production(ZoneKey("NC"), session)
