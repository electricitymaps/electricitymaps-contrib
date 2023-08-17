from json import loads

from pkg_resources import resource_string
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
        hydroquebec_production = resource_string(
            "parsers.test.mocks.Hydroquebec", "production.json"
        )
        self.adapter.register_uri(
            GET, ANY, json=loads(hydroquebec_production.decode("utf-8"))
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
        hydroquebec_consumption = resource_string(
            "parsers.test.mocks.Hydroquebec", "consumption.json"
        )
        self.adapter.register_uri(
            GET, ANY, json=loads(hydroquebec_consumption.decode("utf-8"))
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
