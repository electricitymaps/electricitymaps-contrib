import json
from datetime import datetime
from importlib import resources

from requests import Session
from requests_mock import GET, Adapter
from snapshottest import TestCase

from electricitymap.contrib.lib.types import ZoneKey
from parsers.CNDC import (
    DATA_URL,
    INDEX_URL,
    fetch_generation_forecast,
    fetch_production,
    tz_bo,
)


class TestCNDC(TestCase):
    target_datetime: datetime

    def setUp(self) -> None:
        self.target_datetime = datetime(2023, 12, 20, tzinfo=tz_bo)
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)
        self.adapter.register_uri(
            GET,
            INDEX_URL,
            text=resources.files("parsers.test.mocks.CNDC")
            .joinpath("index.html")
            .read_text(),
        )
        formatted_datetime = self.target_datetime.strftime("%Y-%m-%d")
        self.adapter.register_uri(
            GET,
            DATA_URL.format(formatted_datetime),
            json=json.loads(
                resources.files("parsers.test.mocks.CNDC")
                .joinpath("data.json")
                .read_text()
            ),
        )

    def test_fetch_generation_forecast(self):
        generation_forecast = fetch_generation_forecast(
            zone_key=ZoneKey("BO"),
            session=self.session,
            target_datetime=self.target_datetime,
        )

        self.assertMatchSnapshot(
            [
                {
                    "datetime": element["datetime"].isoformat(),
                    "generation": element["generation"],
                    "zoneKey": element["zoneKey"],
                    "source": element["source"],
                }
                for element in generation_forecast
            ]
        )

    def test_fetch_production(self):
        production = fetch_production(
            zone_key=ZoneKey("BO"),
            session=self.session,
            target_datetime=self.target_datetime,
        )

        self.assertMatchSnapshot(
            [
                {
                    "datetime": element["datetime"].isoformat(),
                    "production": element["production"],
                    "storage": element["storage"],
                    "source": element["source"],
                    "zoneKey": element["zoneKey"],
                }
                for element in production
            ]
        )
