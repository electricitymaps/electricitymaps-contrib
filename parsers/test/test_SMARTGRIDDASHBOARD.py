from snapshottest import TestCase
import json
from importlib import resources

from requests import Session
from requests_mock import GET, Adapter

from electricitymap.contrib.lib.types import ZoneKey
from parsers.SMARTGRIDDASHBOARD import fetch_production, URL, fetch_consumption


class TestSmartGridDashboard(TestCase):
    def setUp(self) -> None:
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)

    def test_fetch_consumption(self):
        self.adapter.register_uri(
            GET,
            URL,
            json=json.loads(
                resources.files("parsers.test.mocks.SMARTGRIDDASHBOARD")
                .joinpath("consumption.json")
                .read_text()
            ),
        )
        consumption = fetch_consumption(
            zone_key=ZoneKey("GB-NIR"),
            session=self.session,
        )

        self.assertMatchSnapshot(
            [
                {
                    "datetime": element["datetime"].isoformat(),
                    "consumption": element["consumption"],
                    "source": element["source"],
                    "sourceType": element["sourceType"].value,
                    "zoneKey": element["zoneKey"],
                }
                for element in consumption
            ]
        )
