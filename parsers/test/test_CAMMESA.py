import json
from importlib import resources

from requests import Session
from requests_mock import ANY, GET, Adapter
from snapshottest import TestCase

from electricitymap.contrib.lib.types import ZoneKey
from parsers.CAMMESA import (
    CAMMESA_DEMANDA_ENDPOINT,
    CAMMESA_RENEWABLES_ENDPOINT,
    fetch_exchange,
    fetch_production,
)


class TestCammesaweb(TestCase):
    def setUp(self) -> None:
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)

    def test_exchanges_AR_CL_SEN(self):
        self.adapter.register_uri(
            GET,
            ANY,
            json=json.loads(
                resources.files("parsers.test.mocks.Cammesa")
                .joinpath("exchanges.json")
                .read_text()
            ),
        )

        exchange = fetch_exchange(
            zone_key1=ZoneKey("AR"), zone_key2=ZoneKey("CL-SEN"), session=self.session
        )

        self.assertMatchSnapshot(
            [
                {
                    "datetime": element["datetime"].isoformat(),
                    "netFlow": element["netFlow"],
                    "source": element["source"],
                    "sortedZoneKeys": element["sortedZoneKeys"],
                    "sourceType": element["sourceType"].value,
                }
                for element in exchange
            ]
        )

    def test_exchanges_AR_BAS_AR_COM(self):
        self.adapter.register_uri(
            GET,
            ANY,
            json=json.loads(
                resources.files("parsers.test.mocks.Cammesa")
                .joinpath("exchanges.json")
                .read_text()
            ),
        )

        exchange = fetch_exchange(
            zone_key1=ZoneKey("AR-BAS"),
            zone_key2=ZoneKey("AR-COM"),
            session=self.session,
        )

        self.assertMatchSnapshot(
            [
                {
                    "datetime": element["datetime"].isoformat(),
                    "netFlow": element["netFlow"],
                    "source": element["source"],
                    "sortedZoneKeys": element["sortedZoneKeys"],
                    "sourceType": element["sourceType"].value,
                }
                for element in exchange
            ]
        )

    def test_fetch_production(self):
        self.adapter.register_uri(
            GET,
            CAMMESA_DEMANDA_ENDPOINT,
            json=json.loads(
                resources.files("parsers.test.mocks.Cammesa")
                .joinpath("conventional_production.json")
                .read_text()
            ),
        )
        self.adapter.register_uri(
            GET,
            CAMMESA_RENEWABLES_ENDPOINT,
            json=json.loads(
                resources.files("parsers.test.mocks.Cammesa")
                .joinpath("renewable_production.json")
                .read_text()
            ),
        )
        production = fetch_production(
            zone_key=ZoneKey("AR"),
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
