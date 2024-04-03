from importlib import resources

from requests import Session
from requests_mock import ANY, GET, Adapter
from snapshottest import TestCase

from electricitymap.contrib.lib.types import ZoneKey
from parsers.ERP_PGCB import fetch_consumption, fetch_exchange, fetch_production


class TestERP_PGCB(TestCase):
    def setUp(self) -> None:
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)

    def test_fetch_consumption(self):
        self.adapter.register_uri(
            GET,
            ANY,
            text=resources.files("parsers.test.mocks.ERP_PGCB")
            .joinpath("latest.html")
            .read_text(),
        )

        consumption = fetch_consumption(zone_key=ZoneKey("BD"), session=self.session)

        self.assertMatchSnapshot(
            [
                {
                    "datetime": element["datetime"].isoformat(),
                    "consumption": element["consumption"],
                    "source": element["source"],
                }
                for element in consumption
            ]
        )

    def test_exchanges(self):
        self.adapter.register_uri(
            GET,
            ANY,
            text=resources.files("parsers.test.mocks.ERP_PGCB")
            .joinpath("latest.html")
            .read_text(),
        )

        exchange = fetch_exchange(
            zone_key1=ZoneKey("BD"),
            zone_key2=ZoneKey("IN-NE"),
            session=self.session,
        )

        self.assertMatchSnapshot(
            [
                {
                    "datetime": element["datetime"].isoformat(),
                    "netFlow": element["netFlow"],
                    "source": element["source"],
                    "sortedZoneKeys": element["sortedZoneKeys"],
                }
                for element in exchange
            ]
        )

    def test_fetch_production(self):
        self.adapter.register_uri(
            GET,
            ANY,
            text=resources.files("parsers.test.mocks.ERP_PGCB")
            .joinpath("latest.html")
            .read_text(),
        )
        production = fetch_production(
            zone_key=ZoneKey("BD"),
            session=self.session,
        )

        self.assertMatchSnapshot(
            [
                {
                    "datetime": element["datetime"].isoformat(),
                    "zoneKey": element["zoneKey"],
                    "production": element["production"],
                    "storage": element["storage"],
                    "source": element["source"],
                    "sourceType": element["sourceType"].value,
                    "correctedModes": element["correctedModes"],
                }
                for element in production
            ]
        )
