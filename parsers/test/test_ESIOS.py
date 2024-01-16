import json
import os
import unittest
from importlib import resources

from requests import Session
from requests_mock import ANY, Adapter

from parsers import ESIOS


class TestESIOS(unittest.TestCase):
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
            data_list = ESIOS.fetch_exchange("ES", "MA", self.session)
            self.assertIsNotNone(data_list)
            for data in data_list:
                self.assertEqual(data["sortedZoneKeys"], "ES->MA")
                self.assertEqual(data["source"], "api.esios.ree.es")
                self.assertIsNotNone(data["datetime"])
                self.assertIsNotNone(data["netFlow"])
        except Exception as ex:
            self.fail(ex.message)


if __name__ == "__main__":
    unittest.main()
