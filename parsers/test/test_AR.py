from json import loads

from pkg_resources import resource_string
from requests import Session
from requests_mock import ANY, GET, Adapter
from snapshottest import TestCase

from electricitymap.contrib.lib.types import ZoneKey
from parsers.AR import (
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
        cammesa_exchanges = resource_string(
            "parsers.test.mocks.Cammesa", "exchanges.json"
        )
        self.adapter.register_uri(
            GET, ANY, json=loads(cammesa_exchanges.decode("utf-8"))
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
        cammesa_exchanges = resource_string(
            "parsers.test.mocks.Cammesa", "exchanges.json"
        )
        self.adapter.register_uri(
            GET, ANY, json=loads(cammesa_exchanges.decode("utf-8"))
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
        cammesa_conventional_production = resource_string(
            "parsers.test.mocks.Cammesa", "conventional_production.json"
        )
        cammesa_renewable_production = resource_string(
            "parsers.test.mocks.Cammesa", "renewable_production.json"
        )
        self.adapter.register_uri(
            GET,
            CAMMESA_DEMANDA_ENDPOINT,
            json=loads(cammesa_conventional_production.decode("utf-8")),
        )
        self.adapter.register_uri(
            GET,
            CAMMESA_RENEWABLES_ENDPOINT,
            json=loads(cammesa_renewable_production.decode("utf-8")),
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
