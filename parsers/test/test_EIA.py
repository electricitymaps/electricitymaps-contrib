import json
import os
import unittest
from datetime import datetime, timezone
from importlib import resources

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
        self.adapter.register_uri(
            GET,
            ANY,
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_NW_AVRN-wind.json")
                .read_text()
            ),
        )
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
        self.adapter.register_uri(
            GET,
            ANY,
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_NW_AVRN-other.json")
                .read_text()
            ),
        )
        self.adapter.register_uri(
            GET,
            EIA.PRODUCTION_MIX.format("AVRN", "WND"),
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_NW_AVRN-wind.json")
                .read_text()
            ),
        )
        self.adapter.register_uri(
            GET,
            EIA.PRODUCTION_MIX.format("PACW", "NG"),
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_NW_PACW-gas.json")
                .read_text()
            ),
        )
        self.adapter.register_uri(
            GET,
            EIA.PRODUCTION_MIX.format("PACW", "WAT"),
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_SMTH-coal.json")
                .read_text()
            ),
        )
        self.adapter.register_uri(
            GET,
            EIA.PRODUCTION_MIX.format("PACW", "SUN"),
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_SMTH-coal.json")
                .read_text()
            ),
        )
        self.adapter.register_uri(
            GET,
            EIA.PRODUCTION_MIX.format("PACW", "WND"),
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_SMTH-coal.json")
                .read_text()
            ),
        )
        self.adapter.register_uri(
            GET,
            EIA.PRODUCTION_MIX.format("BPAT", "WND"),
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_NW_BPAT-wind.json")
                .read_text()
            ),
        )
        self.adapter.register_uri(
            GET,
            EIA.PRODUCTION_MIX.format("BPAT", "NG"),
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_SMTH-coal.json")
                .read_text()
            ),
        )
        self.adapter.register_uri(
            GET,
            EIA.PRODUCTION_MIX.format("BPAT", "WAT"),
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_SMTH-coal.json")
                .read_text()
            ),
        )
        self.adapter.register_uri(
            GET,
            EIA.PRODUCTION_MIX.format("BPAT", "NUC"),
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_SMTH-coal.json")
                .read_text()
            ),
        )
        self.adapter.register_uri(
            GET,
            EIA.PRODUCTION_MIX.format("BPAT", "SUN"),
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_SMTH-coal.json")
                .read_text()
            ),
        )
        self.adapter.register_uri(
            GET,
            EIA.PRODUCTION_MIX.format("AVRN", "NG"),
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_NW_AVRN-gas.json")
                .read_text()
            ),
        )

        data_list = EIA.fetch_production_mix(ZoneKey("US-NW-PACW"), self.session)
        expected = [
            {
                "zoneKey": "US-NW-PACW",
                "source": "eia.gov",
                "production": {"gas": 330, "hydro": 300, "solar": 300, "wind": 300},
                "storage": {},
            },
            {
                "zoneKey": "US-NW-PACW",
                "source": "eia.gov",
                "production": {"gas": 450, "hydro": 400, "solar": 400, "wind": 400},
                "storage": {},
            },
        ]
        self.check_production_matches(data_list, expected)
        data_list = EIA.fetch_production_mix(ZoneKey("US-NW-BPAT"), self.session)
        expected = [
            {
                "zoneKey": "US-NW-BPAT",
                "source": "eia.gov",
                "production": {
                    "wind": 21,
                    "gas": 300,
                    "hydro": 300,
                    "nuclear": 300,
                    "solar": 300,
                },
                "storage": {},
            },
            {
                "zoneKey": "US-NW-BPAT",
                "source": "eia.gov",
                "production": {
                    "wind": 42,
                    "gas": 400,
                    "hydro": 400,
                    "nuclear": 400,
                    "solar": 400,
                },
                "storage": {},
            },
        ]
        self.check_production_matches(data_list, expected)

    def test_US_CAR_SC_nuclear_split(self):
        self.adapter.register_uri(
            GET,
            ANY,
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_NW_AVRN-other.json")
                .read_text()
            ),
        )
        self.adapter.register_uri(
            GET,
            EIA.PRODUCTION_MIX.format("SC", "COL"),
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_SMTH-coal.json")
                .read_text()
            ),
        )
        self.adapter.register_uri(
            GET,
            EIA.PRODUCTION_MIX.format("SC", "NG"),
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_SMTH-coal.json")
                .read_text()
            ),
        )
        self.adapter.register_uri(
            GET,
            EIA.PRODUCTION_MIX.format("SC", "WAT"),
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_SMTH-coal.json")
                .read_text()
            ),
        )
        self.adapter.register_uri(
            GET,
            EIA.PRODUCTION_MIX.format("SC", "OIL"),
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_SMTH-coal.json")
                .read_text()
            ),
        )
        self.adapter.register_uri(
            GET,
            EIA.PRODUCTION_MIX.format("SC", "SUN"),
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_SMTH-coal.json")
                .read_text()
            ),
        )
        self.adapter.register_uri(
            GET,
            EIA.PRODUCTION_MIX.format("SC", "NUC"),
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_CAR_SC-nuclear.json")
                .read_text()
            ),
        )
        self.adapter.register_uri(
            GET,
            EIA.PRODUCTION_MIX.format("SCEG", "NUC"),
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_CAR_SCEG-nuclear.json")
                .read_text()
            ),
        )
        self.adapter.register_uri(
            GET,
            EIA.PRODUCTION_MIX.format("SCEG", "COL"),
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_SMTH-coal.json")
                .read_text()
            ),
        )
        self.adapter.register_uri(
            GET,
            EIA.PRODUCTION_MIX.format("SCEG", "NG"),
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_SMTH-coal.json")
                .read_text()
            ),
        )
        self.adapter.register_uri(
            GET,
            EIA.PRODUCTION_MIX.format("SCEG", "WAT"),
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_SMTH-coal.json")
                .read_text()
            ),
        )
        self.adapter.register_uri(
            GET,
            EIA.PRODUCTION_MIX.format("SCEG", "OIL"),
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_SMTH-coal.json")
                .read_text()
            ),
        )
        self.adapter.register_uri(
            GET,
            EIA.PRODUCTION_MIX.format("SCEG", "SUN"),
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_SMTH-coal.json")
                .read_text()
            ),
        )

        data_list = EIA.fetch_production_mix(ZoneKey("US-CAR-SC"), self.session)
        expected = [
            {
                "zoneKey": "US-CAR-SC",
                "source": "eia.gov",
                "production": {
                    "nuclear": 330.666634,
                    "coal": 300,
                    "gas": 300,
                    "oil": 300,
                    "solar": 300,
                    "hydro": 300,
                },
                "storage": {},
            },
            {
                "zoneKey": "US-CAR-SC",
                "source": "eia.gov",
                "production": {
                    "nuclear": 330.3333,
                    "coal": 400,
                    "gas": 400,
                    "oil": 400,
                    "solar": 400,
                    "hydro": 400,
                },
                "storage": {},
            },
        ]
        self.check_production_matches(data_list, expected)
        data_list = EIA.fetch_production_mix(ZoneKey("US-CAR-SCEG"), self.session)
        expected = [
            {
                "zoneKey": "US-CAR-SCEG",
                "source": "eia.gov",
                "production": {
                    "nuclear": 661.333366,
                    "coal": 300,
                    "gas": 300,
                    "oil": 300,
                    "solar": 300,
                    "hydro": 300,
                },
                "storage": {},
            },
            {
                "zoneKey": "US-CAR-SCEG",
                "source": "eia.gov",
                "production": {
                    "nuclear": 660.6667,
                    "coal": 400,
                    "gas": 400,
                    "oil": 400,
                    "solar": 400,
                    "hydro": 400,
                },
                "storage": {},
            },
        ]
        self.check_production_matches(data_list, expected)

    def test_check_transfer_mixes(self):
        for production in EIA.PRODUCTION_ZONES_TRANSFERS.values():
            all_production = production.get("all", {})
            for production_type, supplying_zones in production.items():
                if production_type == "all":
                    continue
                for zone in supplying_zones:
                    if zone in all_production:
                        raise Exception(
                            f"{zone} is both in the all production export\
                            and exporting its {production_type} production. \
                            This is not possible please fix this ambiguity."
                        )

    def test_hydro_transfer_mix(self):
        """
        Make sure that with zones that integrate production only zones
        the hydro production events are properly handled and the storage
        is accounted for on a zone by zone basis.
        """
        self.adapter.register_uri(
            GET,
            ANY,
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_NW_AVRN-other.json")
                .read_text()
            ),
        )
        self.adapter.register_uri(
            GET,
            EIA.PRODUCTION_MIX.format("SRP", "COL"),
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_SMTH-coal.json")
                .read_text()
            ),
        )
        self.adapter.register_uri(
            GET,
            EIA.PRODUCTION_MIX.format("SRP", "NG"),
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_SMTH-coal.json")
                .read_text()
            ),
        )
        self.adapter.register_uri(
            GET,
            EIA.PRODUCTION_MIX.format("SRP", "NUC"),
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_SMTH-coal.json")
                .read_text()
            ),
        )
        self.adapter.register_uri(
            GET,
            EIA.PRODUCTION_MIX.format("SRP", "SUN"),
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_SMTH-coal.json")
                .read_text()
            ),
        )
        self.adapter.register_uri(
            GET,
            EIA.PRODUCTION_MIX.format("SRP", "WND"),
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_SMTH-coal.json")
                .read_text()
            ),
        )
        self.adapter.register_uri(
            GET,
            EIA.PRODUCTION_MIX.format("DEAA", "WAT"),
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_SW_DEAA-hydro.json")
                .read_text()
            ),
        )
        self.adapter.register_uri(
            GET,
            EIA.PRODUCTION_MIX.format("HGMA", "WAT"),
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_SW_HGMA-hydro.json")
                .read_text()
            ),
        )
        self.adapter.register_uri(
            GET,
            EIA.PRODUCTION_MIX.format("SRP", "WAT"),
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_SW_SRP-hydro.json")
                .read_text()
            ),
        )

        data = EIA.fetch_production_mix(ZoneKey("US-SW-SRP"), self.session)
        expected = [
            {
                "zoneKey": "US-SW-SRP",
                "source": "eia.gov",
                "production": {
                    "hydro": 7.0,
                    "coal": 300,
                    "gas": 300,
                    "nuclear": 300,
                    "solar": 300,
                    "wind": 300,
                },  # hydro 4 from HGMA, 3 from DEAA
                "storage": {"hydro": 5.0},  # 5 from SRP
            },
            {
                "zoneKey": "US-SW-SRP",
                "source": "eia.gov",
                "production": {
                    "hydro": 800.0,
                    "coal": 400,
                    "gas": 400,
                    "nuclear": 400,
                    "solar": 400,
                    "wind": 400,
                },  # hydro 400 from SRP, 400 from HGMA
                "storage": {"hydro": 900.0},  # 900 from DEAA
            },
        ]
        self.check_production_matches(data, expected)

    def test_exchange_transfer(self):
        exchange_key = "US-FLA-FPC->US-FLA-FPL"
        remapped_exchange_key = "US-FLA-FPC->US-FLA-NSB"
        # target_datetime = (
        #     "2020-01-07T05:00:00+00:00"  # Last datapoint before decommissioning of NSB
        # )
        # 1. Get data directly from EIA for both
        fpl_exchange_data = json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US-FLA-FPC_US-FLA-FPL_exchange.json")
            .read_text()
        )
        self.adapter.register_uri(
            GET,
            # For example:
            # https://api.eia.gov/v2/electricity/rto/interchange-data/data/?data[]=value&facets[fromba][]=FPC&facets[toba][]=FPL&frequency=hourly&api_key=token&sort[0][column]=period&sort[0][direction]=desc&length=24
            EIA.EXCHANGE.format(EIA.EXCHANGES[exchange_key]),
            json=fpl_exchange_data,
        )
        nsb_exchange_data = json.loads(
            resources.files("parsers.test.mocks.EIA")
            .joinpath("US-FLA-FPC_US-FLA-NSB_exchange.json")
            .read_text()
        )
        self.adapter.register_uri(
            GET,
            # For example:
            # https://api.eia.gov/v2/electricity/rto/interchange-data/data/?data[]=value&facets[fromba][]=FPC&facets[toba][]=NSB&frequency=hourly&api_key=token&sort[0][column]=period&sort[0][direction]=desc&length=24
            EIA.EXCHANGE.format(EIA.EXCHANGES[remapped_exchange_key]),
            json=nsb_exchange_data,
        )

        # 2. Get data from the EIA parser fetch_exchange for
        # US-FLA-FPC->US-FLA-FPL
        z_k_1, z_k_2 = exchange_key.split("->")
        data_list = EIA.fetch_exchange(ZoneKey(z_k_1), ZoneKey(z_k_2), self.session)

        # Verify that the sum of the data directly fetched matches the data
        # from the parser.
        for fpl, nsb, parser in zip(
            fpl_exchange_data["response"]["data"],
            nsb_exchange_data["response"]["data"],
            data_list,
            strict=True,
        ):
            assert fpl["value"] + nsb["value"] == parser["netFlow"]

    def check_production_matches(
        self,
        actual: list[dict[str, str | dict]],
        expected: list[dict[str, str | dict]],
    ):
        self.assertIsNotNone(actual)
        self.assertEqual(len(expected), len(actual))
        for i, data in enumerate(actual):
            self.assertEqual(data["zoneKey"], expected[i]["zoneKey"])
            self.assertEqual(data["source"], expected[i]["source"])
            self.assertIsNotNone(data["datetime"])
            for key, value in data["production"].items():
                self.assertEqual(value, expected[i]["production"][key])
            self.assertEqual(data.get("storage"), expected[i].get("storage"))
            for key, value in data.get("storage", {}).items():
                self.assertEqual(value, expected[i]["storage"][key])

    def test_fetch_production_mix_discards_null(self):
        self.adapter.register_uri(
            GET,
            ANY,
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US-NW-PGE-with-nulls.json")
                .read_text()
            ),
        )
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
            datetime(2022, 10, 31, 11, 0, tzinfo=timezone.utc), data_list[0]["datetime"]
        )
        self.check_production_matches(data_list, expected)


class TestEIAExchanges(TestEIA):
    def test_fetch_exchange(self):
        self.adapter.register_uri(
            GET,
            ANY,
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US-NW-BPAT-US-NW-NWMT-exchange.json")
                .read_text()
            ),
        )
        data_list = EIA.fetch_exchange(
            ZoneKey("US-NW-BPAT"), ZoneKey("US-NW-NWMT"), self.session
        )
        expected = [
            {
                "source": "eia.gov",
                "datetime": datetime(2022, 2, 28, 22, 0, tzinfo=timezone.utc),
                "sortedZoneKeys": "US-NW-BPAT->US-NW-NWMT",
                "netFlow": -12,
            },
            {
                "source": "eia.gov",
                "datetime": datetime(2022, 2, 28, 23, 0, tzinfo=timezone.utc),
                "sortedZoneKeys": "US-NW-BPAT->US-NW-NWMT",
                "netFlow": -11,
            },
            {
                "source": "eia.gov",
                "datetime": datetime(2022, 3, 1, 0, 0, tzinfo=timezone.utc),
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
        self.adapter.register_uri(
            GET,
            ANY,
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_NW_BPAT-consumption.json")
                .read_text()
            ),
        )
        data_list = EIA.fetch_consumption(ZoneKey("US-NW-BPAT"), self.session)
        expected = [
            {
                "source": "eia.gov",
                "datetime": datetime(2023, 5, 1, 9, 0, tzinfo=timezone.utc),
                "consumption": 4792,
            },
            {
                "source": "eia.gov",
                "datetime": datetime(2023, 5, 1, 10, 0, tzinfo=timezone.utc),
                "consumption": 6215,
            },
        ]
        self.assertEqual(len(data_list), len(expected))
        for i, data in enumerate(data_list):
            self.assertEqual(data["source"], expected[i]["source"])
            self.assertEqual(data["datetime"], expected[i]["datetime"])
            self.assertEqual(data["consumption"], expected[i]["consumption"])

    def test_fetch_forecasted_consumption(self):
        self.adapter.register_uri(
            GET,
            ANY,
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_NW_BPAT-consumption.json")
                .read_text()
            ),
        )
        data_list = EIA.fetch_consumption_forecast(ZoneKey("US-NW-BPAT"), self.session)
        expected = [
            {
                "source": "eia.gov",
                "datetime": datetime(2023, 5, 1, 9, 0, tzinfo=timezone.utc),
                "consumption": 4792,
            },
            {
                "source": "eia.gov",
                "datetime": datetime(2023, 5, 1, 10, 0, tzinfo=timezone.utc),
                "consumption": 6215,
            },
        ]
        self.assertEqual(len(data_list), len(expected))
        for i, data in enumerate(data_list):
            self.assertEqual(data["source"], expected[i]["source"])
            self.assertEqual(data["datetime"], expected[i]["datetime"])
            self.assertEqual(data["consumption"], expected[i]["consumption"])
            self.assertEqual(data["sourceType"], EventSourceType.forecasted)

    def test_texas_loses_one_mode(self):
        """A temporary test to make sure that if texas loses one of its modes we discard the datapoint."""
        # All modes are loaded with some data
        self.adapter.register_uri(
            GET,
            ANY,
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_SMTH-coal.json")
                .read_text()
            ),
        )
        # Nuclear is missing data
        self.adapter.register_uri(
            GET,
            EIA.PRODUCTION_MIX.format("ERCO", "NUC"),
            json=json.loads(
                resources.files("parsers.test.mocks.EIA")
                .joinpath("US_NW_AVRN-other.json")
                .read_text()
            ),
        )
        data = EIA.fetch_production_mix(ZoneKey("US-TEX-ERCO"), self.session)
        self.assertEqual(len(data), 0)


if __name__ == "__main__":
    unittest.main()
