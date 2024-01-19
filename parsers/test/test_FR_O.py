import json
import unittest
from datetime import datetime
from importlib import resources

from requests import Session
from requests_mock import ANY, Adapter

from electricitymap.contrib.lib.types import ZoneKey
from parsers import FR_O


class TestFR_O(unittest.TestCase):
    def setUp(self):
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)

    def test_fetch_exchange(self):
        self.adapter.register_uri(
            ANY,
            ANY,
            json=json.loads(
                resources.files("parsers.test.mocks.FR_O")
                .joinpath("FR_GP.json")
                .read_text()
            ),
        )
        data_list = FR_O.fetch_production("GP", self.session)
        self.assertIsNotNone(data_list)
        expected_data = [
            {
                "zoneKey": "GP",
                "production": {
                    "gas": 1,
                    "coal": 2,
                    "oil": 3,
                    "hydro": 4,
                    "geothermal": 5,
                    "wind": 6,
                    "solar": 7,
                    "biomass": 8,
                },
                "storage": {},
            },
            {
                "zoneKey": "GP",
                "production": {
                    "gas": 10,
                    "coal": 11,
                    "oil": 12,
                    "hydro": 13,
                    "geothermal": 14,
                    "wind": 15,
                    "solar": 16,
                    "biomass": 17,
                },
                "storage": {},
            },
        ]
        self.assertEqual(len(data_list), len(expected_data))
        for index, actual in enumerate(data_list):
            self.assertEqual(actual["zoneKey"], "GP")
            self.assertEqual(actual["source"], "opendata-guadeloupe.edf.fr")
            for production_type, production in actual["production"].items():
                self.assertEqual(
                    production, expected_data[index]["production"][production_type]
                )

    def test_fetch_price(self):
        self.adapter.register_uri(
            ANY,
            ANY,
            json=json.loads(
                resources.files("parsers.test.mocks.FR_O")
                .joinpath("FR_RE.json")
                .read_text()
            ),
        )
        data_list = FR_O.fetch_price(ZoneKey("RE"), self.session, datetime(2018, 1, 1))
        self.assertIsNotNone(data_list)
        expected_data = [
            {
                "zoneKey": "RE",
                "currency": "EUR",
                "datetime": datetime.fromisoformat("2018-01-01T00:00:00+00:00"),
                "source": "opendata.edf.fr",
                "price": 193.7,
            },
            {
                "zoneKey": "RE",
                "currency": "EUR",
                "datetime": datetime.fromisoformat("2018-01-01T01:00:00+00:00"),
                "source": "opendata.edf.fr",
                "price": 195.8,
            },
        ]
        self.assertEqual(len(data_list), len(expected_data))
        for index, actual in enumerate(data_list):
            self.assertEqual(actual["zoneKey"], expected_data[index]["zoneKey"])
            self.assertEqual(actual["currency"], expected_data[index]["currency"])
            self.assertEqual(actual["datetime"], expected_data[index]["datetime"])
            self.assertEqual(actual["source"], expected_data[index]["source"])
            self.assertEqual(actual["price"], expected_data[index]["price"])

    def test_fetch_production(self):
        self.adapter.register_uri(
            ANY,
            ANY,
            json=json.loads(
                resources.files("parsers.test.mocks.FR_O")
                .joinpath("FR_COR.json")
                .read_text()
            ),
        )
        data_list = FR_O.fetch_production(ZoneKey("FR-COR"), self.session)
        self.assertIsNotNone(data_list)
        expected_production_data = [
            {
                "correctedModes": [],
                "datetime": datetime.fromisoformat("2023-07-02T15:26:00+00:00"),
                "zoneKey": "FR-COR",
                "production": {
                    "biomass": 0.38,
                    "hydro": 5.472,
                    "oil": 108.956,
                    "solar": 73.23,
                    "wind": 2.386,
                },
                "storage": {"battery": 0.32},
                "source": "opendata-corse.edf.fr",
                "sourceType": "estimated",
            },
            {
                "correctedModes": [],
                "datetime": datetime.fromisoformat("2023-07-02T15:31:00+00:00"),
                "production": {
                    "biomass": 0.38,
                    "hydro": 5.426,
                    "oil": 110.232,
                    "solar": 74.562,
                    "wind": 2.348,
                },
                "source": "opendata-corse.edf.fr",
                "sourceType": "estimated",
                "storage": {"battery": -0.0},
                "zoneKey": "FR-COR",
            },
        ]
        self.assertEqual(len(data_list), len(expected_production_data))
        for index, actual in enumerate(data_list):
            self.assertEqual(
                actual["zoneKey"], expected_production_data[index]["zoneKey"]
            )
            self.assertEqual(
                actual["source"], expected_production_data[index]["source"]
            )
            self.assertEqual(
                actual["sourceType"], expected_production_data[index]["sourceType"]
            )
            self.assertEqual(
                actual["datetime"], expected_production_data[index]["datetime"]
            )
            self.assertEqual(
                actual["production"], expected_production_data[index]["production"]
            )
            self.assertEqual(
                actual["storage"], expected_production_data[index]["storage"]
            )
            self.assertEqual(
                actual["correctedModes"],
                expected_production_data[index]["correctedModes"],
            )


if __name__ == "__main__":
    unittest.main()
