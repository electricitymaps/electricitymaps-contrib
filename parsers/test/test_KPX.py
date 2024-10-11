from datetime import datetime, timezone

from requests import Session
from requests_mock import GET, POST, Adapter
from snapshottest import TestCase

from electricitymap.contrib.lib.types import ZoneKey
from parsers.KPX import (
    HISTORICAL_PRODUCTION_URL,
    REAL_TIME_URL,
    fetch_consumption,
    fetch_production,
)


class TestKPX(TestCase):
    def setUp(self) -> None:
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)

    def test_fetch_consumption(self):
        with open("parsers/test/mocks/KPX/realtime.html", "rb") as consumption:
            self.adapter.register_uri(
                GET,
                REAL_TIME_URL,
                content=consumption.read(),
            )
            production = fetch_consumption(
                zone_key=ZoneKey("KR"),
                session=self.session,
            )
        self.assertMatchSnapshot(
            [
                {
                    "datetime": element["datetime"].isoformat(),
                    "consumption": element["consumption"],
                    "source": element["source"],
                    "zoneKey": element["zoneKey"],
                    "sourceType": element["sourceType"].value,
                }
                for element in production
            ]
        )

    def test_production_realtime(self):
        with open("parsers/test/mocks/KPX/realtime.html", "rb") as production:
            self.adapter.register_uri(
                GET,
                REAL_TIME_URL,
                content=production.read(),
            )
            production = fetch_production(
                zone_key=ZoneKey("KR"),
                session=self.session,
            )
        self.assertMatchSnapshot(
            [
                {
                    "datetime": element["datetime"].isoformat(),
                    "production": element["production"],
                    "storage": element["storage"],
                    "source": element["source"],
                    "zoneKey": element["zoneKey"],
                    "sourceType": element["sourceType"].value,
                }
                for element in production
            ]
        )

    def test_production_historical(self):
        with open("parsers/test/mocks/KPX/historical.html", "rb") as production:
            self.adapter.register_uri(
                POST,
                HISTORICAL_PRODUCTION_URL,
                content=production.read(),
            )
            self.adapter.register_uri(
                GET,
                HISTORICAL_PRODUCTION_URL,
                content=None,
            )
        production = fetch_production(
            zone_key=ZoneKey("KR"),
            session=self.session,
            target_datetime=datetime(2023, 9, 1, 0, 0, 0, tzinfo=timezone.utc),
        )
        self.assertMatchSnapshot(
            [
                {
                    "datetime": element["datetime"].isoformat(),
                    "production": element["production"],
                    "storage": element["storage"],
                    "source": element["source"],
                    "zoneKey": element["zoneKey"],
                    "sourceType": element["sourceType"].value,
                }
                for element in production
            ]
        )
