from datetime import datetime, timezone

from requests import Session
from requests_mock import GET, Adapter
from snapshottest import TestCase

from electricitymap.contrib.lib.types import ZoneKey
from parsers.CY import HISTORICAL_SOURCE, REALTIME_SOURCE, fetch_production


class TestFetchProduction(TestCase):
    def setUp(self):
        self.adapter = Adapter()
        self.session = Session()
        self.session.mount("https://", self.adapter)

    def test_snapshot_historical_source(self):
        target_datetime = datetime(2024, 3, 18, 0, 0, 0, tzinfo=timezone.utc)
        with open(
            "parsers/test/mocks/CY/response_historical_20240318.html", "rb"
        ) as response:
            self.adapter.register_uri(
                GET, HISTORICAL_SOURCE.format("18-03-2024"), content=response.read()
            )

        production = fetch_production(
            zone_key=ZoneKey("CY"),
            session=self.session,
            target_datetime=target_datetime,
        )

        self.assertMatchSnapshot(
            [
                {
                    "datetime": element["datetime"].isoformat(),
                    "zoneKey": element["zoneKey"],
                    "capacity": element["capacity"],
                    "production": element["production"],
                    "storage": element["storage"],
                    "source": element["source"],
                }
                for element in production
            ]
        )

    def test_snapshot_realtime_source(self):
        with open(
            "parsers/test/mocks/CY/response_realtime_20240401.html", "rb"
        ) as response:
            self.adapter.register_uri(GET, REALTIME_SOURCE, content=response.read())

        production = fetch_production(
            zone_key=ZoneKey("CY"),
            session=self.session,
        )

        self.assertMatchSnapshot(
            [
                {
                    "datetime": element["datetime"].isoformat(),
                    "zoneKey": element["zoneKey"],
                    "capacity": element["capacity"],
                    "production": element["production"],
                    "storage": element["storage"],
                    "source": element["source"],
                }
                for element in production
            ]
        )
