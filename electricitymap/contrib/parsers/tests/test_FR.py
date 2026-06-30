import os
from datetime import datetime, timezone

from requests_mock import GET

from electricitymap.contrib.parsers.FR import API_ENDPOINT, fetch_production
from electricitymap.contrib.types import ZoneKey


def test_production(requests_mock, session, snapshot):
    os.environ["RESEAUX_ENERGIES_TOKEN"] = "test_token"
    with open(
        "electricitymap/contrib/parsers/tests/mocks/FR/response.json", "rb"
    ) as mock_file:
        requests_mock.register_uri(
            GET,
            API_ENDPOINT,
            content=mock_file.read(),
        )

    # The mock spans Paris 2023-09-21T02:00 -> 2023-09-22T02:00 (1/4h granularity).
    # This target maps to a Paris window of [2023-09-21 01:00, 2023-09-22 01:00],
    # which sits inside the mock range so every kept 30-min bucket is averaged from
    # both of its quarter-hour points (no partial single-point bucket at the edges).
    assert snapshot == fetch_production(
        zone_key=ZoneKey("FR"),
        session=session,
        target_datetime=datetime(2023, 9, 21, 23, 0, tzinfo=timezone.utc),
    )
