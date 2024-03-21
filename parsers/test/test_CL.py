from datetime import datetime, timezone
from importlib import resources
from json import loads

from requests import Session
from requests_mock import GET, Adapter
from snapshottest import TestCase

from electricitymap.contrib.lib.types import ZoneKey
from parsers.CL import API_BASE_URL, fetch_production


class TestFetchProduction(TestCase):
    def setUp(self):
        self.adapter = Adapter()
        self.session = Session()
        self.session.mount("https://", self.adapter)

    def test_snapshot_historical_data(self):
        target_datetime = datetime(2024, 2, 24, 0, 0, 0, tzinfo=timezone.utc)
        url = f"{API_BASE_URL}fecha__gte=2024-02-23&fecha__lte=2024-02-24"
        self.adapter.register_uri(
            GET,
            url,
            json=loads(
                resources.files("parsers.test.mocks.CL")
                .joinpath("response_historical_20240224.json")
                .read_text()
            ),
        )

        production = fetch_production(
            zone_key=ZoneKey("CL-SEN"),
            session=self.session,
            target_datetime=target_datetime,
        )

        self.assertMatchSnapshot(
            [
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
        )
