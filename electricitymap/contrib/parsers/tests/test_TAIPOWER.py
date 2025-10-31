from requests_mock import GET

from electricitymap.contrib.lib.types import ZoneKey
from electricitymap.contrib.parsers.TAIPOWER import PRODUCTION_URL, fetch_production


def test_production(adapter, session, snapshot):
    with open(
        "electricitymap/contrib/parsers/tests/mocks/TAIPOWER/genary.json", "rb"
    ) as mock_file:
        adapter.register_uri(
            GET,
            PRODUCTION_URL,
            content=mock_file.read(),
        )

    assert snapshot == fetch_production(
        zone_key=ZoneKey("TW"),
        session=session,
    )
