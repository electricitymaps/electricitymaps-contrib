import json
from importlib import resources

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
        self.adapter.register_uri(
            GET,
            ANY,
            json=json.loads(
                resources.files("parsers.test.mocks.CEB")
                .joinpath("response.text")
                .read_text()
            ),
        )

        production = fetch_production(zone_key=ZoneKey("LK"), session=self.session)

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
