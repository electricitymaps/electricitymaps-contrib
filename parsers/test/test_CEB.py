from json import loads

from pkg_resources import resource_string
from requests import Session
from requests_mock import ANY, GET, Adapter
from snapshottest import TestCase

from electricitymap.contrib.lib.types import ZoneKey
from parsers.CEB import fetch_production


class TestCEB(TestCase):
    def setUp(self) -> None:
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)

    def test_production(self):
        data = resource_string("parsers.test.mocks.CEB", "response.text")

        self.adapter.register_uri(GET, ANY, json=loads(data.decode("utf-8")))

        production = fetch_production(zone_key=ZoneKey("LK"), session=self.session)

        self.assertMatchSnapshot(
            [
                {
                    "datetime": element["datetime"].isoformat(),
                    "source": element["source"],
                    "zoneKey": element["zoneKey"],
                    "production": element["production"],
                }
                for element in production
            ]
        )
