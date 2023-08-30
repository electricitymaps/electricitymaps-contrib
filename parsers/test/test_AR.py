import logging
from json import loads

from pkg_resources import resource_string
from requests import Session
from requests_mock import ANY, GET, Adapter
from snapshottest import TestCase

from electricitymap.contrib.lib.types import ZoneKey
from parsers.AR import fetch_exchange


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
