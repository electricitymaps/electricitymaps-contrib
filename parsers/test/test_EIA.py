import os
import unittest
from datetime import datetime
from json import loads
from typing import Dict, List, Union

from pkg_resources import resource_string
from pytz import utc
from requests import Session
from requests_mock import ANY, GET, Adapter

from electricitymap.contrib.lib.models.events import EventSourceType
from electricitymap.contrib.lib.types import ZoneKey
from parsers import EIA


class TestEIA(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["EIA_KEY"] = "token"
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)


class TestEIAProduction(TestEIA):
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
                "storage": {},
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
                "storage": {},
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

        data_list = EIA.fetch_production_mix(ZoneKey("US-NW-PACW"), self.session)
        expected = [
            {
                "zoneKey": "US-NW-PACW",
                "source": "eia.gov",
                "production": {"gas": 330},
                "storage": {},
            },
            {
                "zoneKey": "US-NW-PACW",
                "source": "eia.gov",
                "production": {"gas": 450},
                "storage": {},
            },
        ]
        self.check_production_matches(data_list, expected)
        data_list = EIA.fetch_production_mix(ZoneKey("US-NW-BPAT"), self.session)
        expected = [
            {
                "zoneKey": "US-NW-BPAT",
                "source": "eia.gov",
                "production": {"wind": 21},
                "storage": {},
            },
            {
                "zoneKey": "US-NW-BPAT",
                "source": "eia.gov",
                "production": {"wind": 42},
                "storage": {},
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

        data_list = EIA.fetch_production_mix(ZoneKey("US-CAR-SC"), self.session)
        expected = [
            {
                "zoneKey": "US-CAR-SC",
                "source": "eia.gov",
                "production": {"nuclear": 330.6666336},
                "storage": {},
            },
            {
                "zoneKey": "US-CAR-SC",
                "source": "eia.gov",
                "production": {"nuclear": 330.3333003},
                "storage": {},
            },
        ]
        self.check_production_matches(data_list, expected)
        data_list = EIA.fetch_production_mix(ZoneKey("US-CAR-SCEG"), self.session)
        expected = [
            {
                "zoneKey": "US-CAR-SCEG",
                "source": "eia.gov",
                "production": {"nuclear": 661.3333663999999},
                "storage": {},
            },
            {
                "zoneKey": "US-CAR-SCEG",
                "source": "eia.gov",
                "production": {"nuclear": 660.6666997},
                "storage": {},
            },
        ]
        self.check_production_matches(data_list, expected)

    def test_check_transfer_mixes(self):
        for supplied_zone, production in EIA.PRODUCTION_ZONES_TRANSFERS.items():
            all_production = production.get("all", {})
            for type, supplying_zones in production.items():
                if type == "all":
                    continue
                for zone in supplying_zones:
                    if zone in all_production:
                        raise Exception(
                            f"{zone} is both in the all production export\
                            and exporting its {type} production. \
                            This is not possible please fix this ambiguity."
                        )

    def test_hydro_transfer_mix(self):
        """
        Make sure that with zones that integrate production only zones
        the hydro production events are properly handled and the storage
        is accounted for on a zone by zone basis.
        """
        other_data = resource_string("parsers.test.mocks.EIA", "US_NW_AVRN-other.json")
        self.adapter.register_uri(GET, ANY, json=loads(other_data.decode("utf-8")))
        hydro_deaa = resource_string("parsers.test.mocks.EIA", "US_SW_DEAA-hydro.json")
        hydro_deaa_url = EIA.PRODUCTION_MIX.format("DEAA", "WAT")
        self.adapter.register_uri(
            GET, hydro_deaa_url, json=loads(hydro_deaa.decode("utf-8"))
        )

        hydro_hgma = resource_string("parsers.test.mocks.EIA", "US_SW_HGMA-hydro.json")
        hydro_hgma_url = EIA.PRODUCTION_MIX.format("HGMA", "WAT")
        self.adapter.register_uri(
            GET, hydro_hgma_url, json=loads(hydro_hgma.decode("utf-8"))
        )

        hydro_srp = resource_string("parsers.test.mocks.EIA", "US_SW_SRP-hydro.json")
        hydro_srp_url = EIA.PRODUCTION_MIX.format("SRP", "WAT")
        self.adapter.register_uri(
            GET, hydro_srp_url, json=loads(hydro_srp.decode("utf-8"))
        )
        data = EIA.fetch_production_mix(ZoneKey("US-SW-SRP"), self.session)
        expected = [
            {
                "zoneKey": "US-SW-SRP",
                "source": "eia.gov",
                "production": {"hydro": 7.0},  # 4 from HGMA, 3 from DEAA
                "storage": {"hydro": 5.0},  # 5 from SRP
            },
            {
                "zoneKey": "US-SW-SRP",
                "source": "eia.gov",
                "production": {"hydro": 800.0},  # 400 from SRP, 400 from HGMA
                "storage": {"hydro": 900.0},  # 900 from DEAA
            },
        ]
        self.check_production_matches(data, expected)

    def test_exchange_transfer(self):
        exchange_key = "US-FLA-FPC->US-FLA-FPL"
        remapped_exchange_key = "US-FLA-FPC->US-FLA-NSB"
        target_datetime = (
            "2020-01-07T05:00:00+00:00"  # Last datapoint before decommissioning of NSB
        )
        # 1. Get data directly from EIA for both
        FPL_exchange_data = resource_string(
            "parsers.test.mocks.EIA", "US-FLA-FPC_US-FLA-FPL_exchange.json"
        )
        FPL_exchange_data_url = EIA.EXCHANGE.format(EIA.EXCHANGES[exchange_key])
        # FPL_exchange_data_url = "https://api.eia.gov/v2/electricity/rto/interchange-data/data/?data[]=value&facets[fromba][]=FPC&facets[toba][]=FPL&frequency=hourly&api_key=token&sort[0][column]=period&sort[0][direction]=desc&length=24"
        self.adapter.register_uri(
            GET, FPL_exchange_data_url, json=loads(FPL_exchange_data.decode("utf-8"))
        )

        NSB_exchange_data = resource_string(
            "parsers.test.mocks.EIA", "US-FLA-FPC_US-FLA-NSB_exchange.json"
        )
        NSB_exchange_data_url = EIA.EXCHANGE.format(
            EIA.EXCHANGES[remapped_exchange_key]
        )
        # NSB_exchange_data_url = "https://api.eia.gov/v2/electricity/rto/interchange-data/data/?data[]=value&facets[fromba][]=FPC&facets[toba][]=NSB&frequency=hourly&api_key=token&sort[0][column]=period&sort[0][direction]=desc&length=24"
        self.adapter.register_uri(
            GET, NSB_exchange_data_url, json=loads(NSB_exchange_data.decode("utf-8"))
        )

        # 2. Get data from the EIA parser fetch_exchange for US-FLA-FPC->US-FLA-FPL
        z_k_1, z_k_2 = exchange_key.split("->")
        data_list = EIA.fetch_exchange(ZoneKey(z_k_1), ZoneKey(z_k_2), self.session)

        # Verify that the sum of the data directly fetched matches the data from the parser
        # Read both json and sum the values
        FPL_exchange_data_json = loads(FPL_exchange_data.decode("utf-8"))
        NSB_exchange_data_json = loads(NSB_exchange_data.decode("utf-8"))

        for idx in range(len(data_list)):
            FPL_raw_value = FPL_exchange_data_json["response"]["data"][idx]["value"]
            NSB_raw_value = NSB_exchange_data_json["response"]["data"][idx]["value"]
            assert FPL_raw_value + NSB_raw_value == data_list[idx]["netFlow"]

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
            self.assertEqual(data.get("storage"), expected[i].get("storage"))
            for key, value in data.get("storage", {}).items():
                self.assertEqual(value, expected[i]["storage"][key])

    def test_fetch_production_mix_discards_null(self):
        null_avrn_data = resource_string(
            "parsers.test.mocks.EIA", "US-NW-PGE-with-nulls.json"
        )
        self.adapter.register_uri(GET, ANY, json=loads(null_avrn_data.decode("utf-8")))
        data_list = EIA.fetch_production_mix(ZoneKey("US-NW-PGE"), self.session)
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
                "storage": {},
            },
        ]
        self.assertEqual(
            datetime(2022, 10, 31, 11, 0, tzinfo=utc), data_list[0]["datetime"]
        )
        self.check_production_matches(data_list, expected)


class TestEIAExchanges(TestEIA):
    def test_fetch_exchange(self):
        data = resource_string(
            "parsers.test.mocks.EIA", "US-NW-BPAT-US-NW-NWMT-exchange.json"
        )
        self.adapter.register_uri(GET, ANY, json=loads(data.decode("utf-8")))
        data_list = EIA.fetch_exchange(
            ZoneKey("US-NW-BPAT"), ZoneKey("US-NW-NWMT"), self.session
        )
        expected = [
            {
                "source": "eia.gov",
                "datetime": datetime(2022, 2, 28, 22, 0, tzinfo=utc),
                "sortedZoneKeys": "US-NW-BPAT->US-NW-NWMT",
                "netFlow": -12,
            },
            {
                "source": "eia.gov",
                "datetime": datetime(2022, 2, 28, 23, 0, tzinfo=utc),
                "sortedZoneKeys": "US-NW-BPAT->US-NW-NWMT",
                "netFlow": -11,
            },
            {
                "source": "eia.gov",
                "datetime": datetime(2022, 3, 1, 0, 0, tzinfo=utc),
                "sortedZoneKeys": "US-NW-BPAT->US-NW-NWMT",
                "netFlow": -2,
            },
        ]
        self.assertEqual(len(data_list), len(expected))
        for i, data in enumerate(data_list):
            self.assertEqual(data["source"], expected[i]["source"])
            self.assertEqual(data["datetime"], expected[i]["datetime"])
            self.assertEqual(data["sortedZoneKeys"], expected[i]["sortedZoneKeys"])
            self.assertEqual(data["netFlow"], expected[i]["netFlow"])


class TestEIAConsumption(TestEIA):
    def test_fetch_consumption(self):
        data = resource_string("parsers.test.mocks.EIA", "US_NW_BPAT-consumption.json")
        self.adapter.register_uri(GET, ANY, json=loads(data.decode("utf-8")))
        data_list = EIA.fetch_consumption(ZoneKey("US-NW-BPAT"), self.session)
        expected = [
            {
                "source": "eia.gov",
                "datetime": datetime(2023, 5, 1, 9, 0, tzinfo=utc),
                "consumption": 4792,
            },
            {
                "source": "eia.gov",
                "datetime": datetime(2023, 5, 1, 10, 0, tzinfo=utc),
                "consumption": 6215,
            },
        ]
        self.assertEqual(len(data_list), len(expected))
        for i, data in enumerate(data_list):
            self.assertEqual(data["source"], expected[i]["source"])
            self.assertEqual(data["datetime"], expected[i]["datetime"])
            self.assertEqual(data["consumption"], expected[i]["consumption"])

    def test_fetch_forecasted_consumption(self):
        data = resource_string("parsers.test.mocks.EIA", "US_NW_BPAT-consumption.json")
        self.adapter.register_uri(GET, ANY, json=loads(data.decode("utf-8")))
        data_list = EIA.fetch_consumption_forecast(ZoneKey("US-NW-BPAT"), self.session)
        expected = [
            {
                "source": "eia.gov",
                "datetime": datetime(2023, 5, 1, 9, 0, tzinfo=utc),
                "consumption": 4792,
            },
            {
                "source": "eia.gov",
                "datetime": datetime(2023, 5, 1, 10, 0, tzinfo=utc),
                "consumption": 6215,
            },
        ]
        self.assertEqual(len(data_list), len(expected))
        for i, data in enumerate(data_list):
            self.assertEqual(data["source"], expected[i]["source"])
            self.assertEqual(data["datetime"], expected[i]["datetime"])
            self.assertEqual(data["consumption"], expected[i]["consumption"])
            self.assertEqual(data["sourceType"], EventSourceType.forecasted)


if __name__ == "__main__":
    unittest.main()
