import json
from importlib import resources

from requests import Session
from requests_mock import ANY, GET, Adapter
from snapshottest import TestCase

from parsers.CA_QC import fetch_consumption, fetch_production


class TestHydroquebec(TestCase):
    def setUp(self) -> None:
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)

    def test_production(self):
        self.adapter.register_uri(
            GET,
            ANY,
            json=json.loads(
                resources.files("parsers.test.mocks.Hydroquebec")
                .joinpath("production.json")
                .read_text()
            ),
        )

        production = fetch_production(session=self.session)

        self.assertMatchSnapshot(
            [
                {
                    "datetime": element["datetime"].isoformat(),
                    "production": element["production"],
                    "source": element["source"],
                    "zoneKey": element["zoneKey"],
                    "storage": element["storage"],
                    "sourceType": element["sourceType"].value,
                }
                for element in production
            ]
        )

    def test_consumption(self):
        self.adapter.register_uri(
            GET,
            ANY,
            json=json.loads(
                resources.files("parsers.test.mocks.Hydroquebec")
                .joinpath("consumption.json")
                .read_text()
            ),
        )

        consumption = fetch_consumption(session=self.session)
        self.assertMatchSnapshot(
            [
                {
                    "datetime": element["datetime"].isoformat(),
                    "consumption": element["consumption"],
                    "source": element["source"],
                    "zoneKey": element["zoneKey"],
                    "sourceType": element["sourceType"].value,
                }
                for element in consumption
            ]
        )
