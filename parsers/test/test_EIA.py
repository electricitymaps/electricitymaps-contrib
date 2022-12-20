import os
import unittest
from datetime import datetime
from json import loads
from typing import Dict, List, Union

from pkg_resources import resource_string
from pytz import utc
from requests import Session
from requests_mock import ANY, GET, Adapter

from parsers import EIA


class TestEIA(unittest.TestCase):
    def setUp(self):
        os.environ["EIA_KEY"] = "token"
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)

    def test_fetch_production_mix(self):
        wind_avrn_data = resource_string(
            "parsers.test.mocks.EIA", "US_NW_AVRN-wind.json"
        )
        self.adapter.register_uri(GET, ANY, json=loads(wind_avrn_data.decode("utf-8")))
        data_list = EIA.fetch_production_mix("US-NW-PGE", self.session)
        expected = [
            {
                "zoneKey": "US-NW-PGE",
                "source": "eia.gov",
                "production": {
                    "gas": 1,
                    "coal": 1,
                    "wind": 1,
                    "hydro": 1,
                    "nuclear": 1,
                    "oil": 1,
                    "unknown": 1,
                    "solar": 1,
                },
            },
            {
                "zoneKey": "US-NW-PGE",
                "source": "eia.gov",
                "production": {
                    "gas": 2,
                    "coal": 2,
                    "wind": 2,
                    "hydro": 2,
                    "nuclear": 2,
                    "oil": 2,
                    "unknown": 2,
                    "solar": 2,
                },
            },
        ]
        self.check_production_matches(data_list, expected)

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
                "production": {"gas": 330},
            },
            {"zoneKey": "US-NW-PACW", "source": "eia.gov", "production": {"gas": 450}},
        ]
        self.check_production_matches(data_list, expected)
        data_list = EIA.fetch_production_mix("US-NW-BPAT", self.session)
        expected = [
            {
                "zoneKey": "US-NW-BPAT",
                "source": "eia.gov",
                "production": {"wind": 21},
            },
            {
                "zoneKey": "US-NW-BPAT",
                "source": "eia.gov",
                "production": {"wind": 42},
            },
        ]
        self.check_production_matches(data_list, expected)

    def test_US_CAR_SC_nuclear_split(self):
        nuclear_sc_data = resource_string(
            "parsers.test.mocks.EIA", "US_CAR_SC-nuclear.json"
        )
        nuclear_sceg_data = resource_string(
            "parsers.test.mocks.EIA", "US_CAR_SCEG-nuclear.json"
        )
        other_data = resource_string("parsers.test.mocks.EIA", "US_NW_AVRN-other.json")
        nuclear_sc_url = EIA.PRODUCTION_MIX.format("SC", "NUC")
        nuclear_sceg_url = EIA.PRODUCTION_MIX.format("SCEG", "NUC")
        self.adapter.register_uri(GET, ANY, json=loads(other_data.decode("utf-8")))
        self.adapter.register_uri(
            GET, nuclear_sceg_url, json=loads(nuclear_sceg_data.decode("utf-8"))
        )
        self.adapter.register_uri(
            GET, nuclear_sc_url, json=loads(nuclear_sc_data.decode("utf-8"))
        )

        data_list = EIA.fetch_production_mix("US-CAR-SC", self.session)
        expected = [
            {
                "zoneKey": "US-CAR-SC",
                "source": "eia.gov",
                "production": {"nuclear": 330.6666336},
            },
            {
                "zoneKey": "US-CAR-SC",
                "source": "eia.gov",
                "production": {"nuclear": 330.3333003},
            },
        ]
        self.check_production_matches(data_list, expected)
        data_list = EIA.fetch_production_mix("US-CAR-SCEG", self.session)
        expected = [
            {
                "zoneKey": "US-CAR-SCEG",
                "source": "eia.gov",
                "production": {"nuclear": 661.3333663999999},
            },
            {
                "zoneKey": "US-CAR-SCEG",
                "source": "eia.gov",
                "production": {"nuclear": 660.6666997},
            },
        ]
        self.check_production_matches(data_list, expected)

    def test_check_transfer_mixes(self):
        for supplied_zone, production in EIA.PRODUCTION_ZONES_TRANSFERS.items():
            all_production = production.pop("all", {})
            for type, supplying_zones in production.items():
                for zone in supplying_zones:
                    if zone in all_production:
                        raise Exception(
                            f"{zone} is both in the all production export\
                            and exporting its {type} production. \
                            This is not possible please fix this ambiguity."
                        )

    def check_production_matches(
        self,
        actual: List[Dict[str, Union[str, Dict]]],
        expected: List[Dict[str, Union[str, Dict]]],
    ):
        self.assertIsNotNone(actual)
        self.assertEqual(len(expected), len(actual))
        for i, data in enumerate(actual):
            print(data)
            self.assertEqual(data["zoneKey"], expected[i]["zoneKey"])
            self.assertEqual(data["source"], expected[i]["source"])
            self.assertIsNotNone(data["datetime"])
            for key, value in data["production"].items():
                self.assertEqual(value, expected[i]["production"][key])

    def test_fetch_production_mix_discards_null(self):
        null_avrn_data = resource_string(
            "parsers.test.mocks.EIA", "US-NW-PGE-with-nulls.json"
        )
        self.adapter.register_uri(GET, ANY, json=loads(null_avrn_data.decode("utf-8")))
        data_list = EIA.fetch_production_mix("US-NW-PGE", self.session)
        expected = [
            {
                "zoneKey": "US-NW-PGE",
                "source": "eia.gov",
                "production": {
                    "gas": 400,
                    "coal": 400,
                    "wind": 400,
                    "hydro": 400,
                    "nuclear": 400,
                    "oil": 400,
                    "unknown": 400,
                    "solar": 400,
                },
            },
        ]
        self.assertEqual(
            datetime(2022, 10, 31, 11, 0, tzinfo=utc), data_list[0]["datetime"]
        )
        self.check_production_matches(data_list, expected)


if __name__ == "__main__":
    unittest.main()
