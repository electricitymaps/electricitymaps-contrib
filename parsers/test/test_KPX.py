from json import loads

from pkg_resources import resource_string
from requests import Session
from requests_mock import GET, Adapter
from snapshottest import TestCase
from datetime import datetime

from electricitymap.contrib.lib.types import ZoneKey
from parsers.KPX import REAL_TIME_URL, fetch_consumption, fetch_production


class TestKPX(TestCase):
    def setUp(self) -> None:
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)

    def test_fetch_consumption(self):
        consumption = open("parsers/test/mocks/KPX/realtime.html", "rb")
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
        production = open("parsers/test/mocks/KPX/realtime.html", "rb")
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
