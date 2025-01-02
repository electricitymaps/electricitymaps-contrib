from datetime import datetime, timezone
from importlib import resources
from json import loads

import pytest
from requests_mock import GET

from electricitymap.contrib.lib.types import ZoneKey
from parsers.CL import API_BASE_URL, fetch_production


@pytest.fixture(autouse=True)
def mock_response(adapter):
    url = f"{API_BASE_URL}fecha__gte=2024-02-23&fecha__lte=2024-02-24"
    adapter.register_uri(
        GET,
        url,
        json=loads(
            resources.files("parsers.test.mocks.CL")
            .joinpath("response_historical_20240224.json")
            .read_text()
        ),
    )


def test_snapshot_historical_data(session, snapshot):
    target_datetime = datetime(2024, 2, 24, 0, 0, 0, tzinfo=timezone.utc)

    production = fetch_production(
        ZoneKey("CL-SEN"),
        session=session,
        target_datetime=target_datetime,
    )

    assert snapshot == [
        {
            "datetime": element["datetime"].isoformat(),
            "zoneKey": element["zoneKey"],
            "production": element["production"],
            "storage": element["storage"],
            "source": element["source"],
            "sourceType": element["sourceType"].value,
            "correctedModes": element["correctedModes"],
        }
        for element in production
    ]
