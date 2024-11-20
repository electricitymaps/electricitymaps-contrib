import json
import os
import unittest
from importlib import resources

from requests import Session
from requests_mock import ANY, Adapter
from snapshottest import TestCase

from electricitymap.contrib.lib.types import ZoneKey
from parsers import ESIOS


class TestESIOS(TestCase):
    def setUp(self):
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)

    def test_fetch_exchange(self):
        self.adapter.register_uri(
            ANY,
            ANY,
            json=json.loads(
                resources.files("parsers.test.mocks")
                .joinpath("ESIOS_ES_MA.json")
                .read_text()
            ),
        )
        try:
            os.environ["ESIOS_TOKEN"] = "token"
            data_list = ESIOS.fetch_exchange(ZoneKey("ES"), ZoneKey("MA"), self.session)
            self.assertIsNotNone(data_list)
            for data in data_list:
                self.assertEqual(data["sortedZoneKeys"], "ES->MA")
                self.assertEqual(data["source"], "api.esios.ree.es")
                self.assertIsNotNone(data["datetime"])
                self.assertIsNotNone(data["netFlow"])
        except Exception as ex:
            self.fail(ex.message)

    def test_exchange_with_snapshot(self):
        self.adapter.register_uri(
            ANY,
            ANY,
            json=json.loads(
                resources.files("parsers.test.mocks")
                .joinpath("ESIOS_ES_MA.json")
                .read_text()
            ),
        )
        try:
            os.environ["ESIOS_TOKEN"] = "token"
            exchange = ESIOS.fetch_exchange(
                zone_key1=ZoneKey("ES"), zone_key2=ZoneKey("MA"), session=self.session
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
        except Exception as ex:
            self.fail(ex.message)


if __name__ == "__main__":
    unittest.main()
