from importlib import resources
from json import loads

from requests import Session
from requests_mock import GET, Adapter
from snapshottest import TestCase

from parsers.NZ import PRICE_URL, PRODUCTION_URL, fetch_price, fetch_production


class TestFetchProduction(TestCase):
    def setUp(self):
        self.adapter = Adapter()
        self.session = Session()
        self.session.mount("https://", self.adapter)

    def test_snapshot_production_data(self):
        url = PRODUCTION_URL
        production = []

        with open(
            resources.files("parsers.test.mocks.NZ").joinpath(
                "response_2024_04_24_17_30.html"
            )
        ) as f:
            self.adapter.register_uri(
                GET,
                url,
                text=f.read(),
            )

        production.append(fetch_production(zone_key="NZ", session=self.session))

        with open(
            resources.files("parsers.test.mocks.NZ").joinpath(
                "response_2024_04_24_18_00.html"
            )
        ) as f:
            self.adapter.register_uri(
                GET,
                url,
                text=f.read(),
            )

        production.append(fetch_production(zone_key="NZ", session=self.session))

        self.assertMatchSnapshot(
            [
                {
                    "datetime": element["datetime"].isoformat(),
                    "zoneKey": element["zoneKey"],
                    "production": element["production"],
                    "storage": element["storage"],
                    "capacity": element["capacity"],
                    "source": element["source"],
                }
                for element in production
            ]
        )

    def test_snapshot_price_data(self):
        url = PRICE_URL
        price = []

        self.adapter.register_uri(
            GET,
            url,
            json=loads(
                resources.files("parsers.test.mocks.NZ")
                .joinpath("response_2024_04_24_18_00.json")
                .read_text()
            ),
        )

        price.append(fetch_price(zone_key="NZ", session=self.session))

        self.adapter.register_uri(
            GET,
            url,
            json=loads(
                resources.files("parsers.test.mocks.NZ")
                .joinpath("response_2024_04_24_18_30.json")
                .read_text()
            ),
        )

        price.append(fetch_price(zone_key="NZ", session=self.session))

        self.assertMatchSnapshot(
            [
                {
                    "datetime": element["datetime"].isoformat(),
                    "zoneKey": element["zoneKey"],
                    "source": element["source"],
                    "price": element["price"],
                    "currency": element["currency"],
                }
                for element in price
            ]
        )
