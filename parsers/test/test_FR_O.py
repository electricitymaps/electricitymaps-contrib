import unittest
from json import loads

from pkg_resources import resource_string
from requests import Session
from requests_mock import ANY, Adapter

from parsers import FR_O


class TestFR_O(unittest.TestCase):
    def setUp(self):
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)

    def test_fetch_exchange(self):
        json_data = resource_string("parsers.test.mocks.FR_O", "FR_GP.json")
        self.adapter.register_uri(ANY, ANY, json=loads(json_data.decode("utf-8")))
        data_list = FR_O.fetch_production("GP", self.session)
        self.assertIsNotNone(data_list)
        expected_data = [
            {
                "zoneKey": "GP",
                "production": {
                    "unknown": 1,
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
                    "unknown": 10,
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
            self.assertEqual(actual["source"], "edf.fr")
            for production_type, production in actual["production"].items():
                self.assertEqual(
                    production, expected_data[index]["production"][production_type]
                )


if __name__ == "__main__":
    unittest.main()
