from requests_mock import GET

from electricitymap.contrib.parsers.TAIPOWER import PRODUCTION_URL, fetch_production
from electricitymap.contrib.types import ZoneKey


def test_production(requests_mock, session, snapshot):
    with open(
        "electricitymap/contrib/parsers/tests/mocks/TAIPOWER/genary.json", "rb"
    ) as mock_file:
        requests_mock.register_uri(
            GET,
            PRODUCTION_URL,
            content=mock_file.read(),
        )

    assert snapshot == fetch_production(
        zone_key=ZoneKey("TW"),
        session=session,
    )
