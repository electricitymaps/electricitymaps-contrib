import os
import unittest
from json import loads
from typing import Dict, List, Union

from pkg_resources import resource_string
from requests import Session
from requests_mock import ANY, GET, Adapter

from parsers import EIA


class TestEIA(unittest.TestCase):
    def setUp(self):
        os.environ["EIA_KEY"] = "token"
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)

    def test_US_NW_AVRN_rerouting(self):
        gas_avrn_data = resource_string("parsers.test.mocks.EIA", "US_NW_AVRN-gas.json")
        wind_avrn_data = resource_string(
            "parsers.test.mocks.EIA", "US_NW_AVRN-wind.json"
        )
        other_avrn_data = resource_string(
            "parsers.test.mocks.EIA", "US_NW_AVRN-other.json"
        )
        gas_pacw_data = resource_string("parsers.test.mocks.EIA", "US_NW_PACW-gas.json")
        wind_bpat_data = resource_string(
            "parsers.test.mocks.EIA", "US_NW_BPAT-wind.json"
        )
        gas_avrn_url = EIA.PRODUCTION_MIX.format("AVRN", "NG")
        wind_avrn_url = EIA.PRODUCTION_MIX.format("AVRN", "WND")
        gas_pacw_url = EIA.PRODUCTION_MIX.format("PACW", "NG")
        wind_bpat_url = EIA.PRODUCTION_MIX.format("BPAT", "WND")
        self.adapter.register_uri(GET, ANY, json=loads(other_avrn_data.decode("utf-8")))
        self.adapter.register_uri(
            GET, wind_avrn_url, json=loads(wind_avrn_data.decode("utf-8"))
        )
        self.adapter.register_uri(
            GET, gas_pacw_url, json=loads(gas_pacw_data.decode("utf-8"))
        )
        self.adapter.register_uri(
            GET, wind_bpat_url, json=loads(wind_bpat_data.decode("utf-8"))
        )
        self.adapter.register_uri(
            GET, gas_avrn_url, json=loads(gas_avrn_data.decode("utf-8"))
        )

        data_list = EIA.fetch_production_mix("US-NW-PACW", self.session)
        expected = [
            {
                "zoneKey": "US-NW-PACW",
                "source": "eia.gov",
                "production": {"gas": 30},
            },
            {
                "zoneKey": "US-NW-PACW",
                "source": "eia.gov",
                "production": {"gas": 50},
            },
            {
                "zoneKey": "US-NW-PACW",
                "source": "eia.gov",
                "production": {"gas": 300},
            },
            {"zoneKey": "US-NW-PACW", "source": "eia.gov", "production": {"gas": 400}},
        ]
        self.check_production_matches(data_list, expected)
        data_list = EIA.fetch_production_mix("US-NW-BPAT", self.session)
        expected = [
            {
                "zoneKey": "US-NW-BPAT",
                "source": "eia.gov",
                "production": {"wind": 20},
            },
            {
                "zoneKey": "US-NW-BPAT",
                "source": "eia.gov",
                "production": {"wind": 40},
            },
            {
                "zoneKey": "US-NW-BPAT",
                "source": "eia.gov",
                "production": {"wind": 1},
            },
            {
                "zoneKey": "US-NW-BPAT",
                "source": "eia.gov",
                "production": {"wind": 2},
            },
        ]
        self.check_production_matches(data_list, expected)

    def check_production_matches(
        self,
        actual: List[Dict[str, Union[str, Dict]]],
        expected: List[Dict[str, Union[str, Dict]]],
    ):
        self.assertIsNotNone(actual)
        self.assertEqual(len(expected), len(actual))
        for i, data in enumerate(actual):
            self.assertEqual(data["zoneKey"], expected[i]["zoneKey"])
            self.assertEqual(data["source"], expected[i]["source"])
            self.assertIsNotNone(data["datetime"])
            for key, value in data["production"].items():
                self.assertEqual(value, expected[i]["production"][key])


if __name__ == "__main__":
    unittest.main()
