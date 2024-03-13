import json
from importlib import resources

from requests import Session
from requests_mock import GET, Adapter
from snapshottest import TestCase

from electricitymap.contrib.lib.types import ZoneKey
from parsers.amper_landsnet import SOURCE_URL, fetch_production


class TestLandsnet(TestCase):
    def setUp(self) -> None:
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)

    def test_fetch_production(self):
        self.adapter.register_uri(
            GET,
            SOURCE_URL,
            json=json.loads(
                resources.files("parsers.test.mocks.amper_landsnet")
                .joinpath("production.json")
                .read_text()
            ),
        )
        production = fetch_production(
            zone_key=ZoneKey("IS"),
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
