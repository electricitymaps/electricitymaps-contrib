import json
import unittest
from pathlib import Path

from deepdiff import DeepDiff

from electricitymap.contrib import config

CONFIG_DIR = Path(__file__).parent.parent.joinpath("config").resolve()


class ConfigTestcase(unittest.TestCase):
    def test_generate_zone_neighbours_two_countries(self):
        exchanges = {
            "DE->FR": {"parsers": {"exchange": "source"}},
        }
        zones = {
            "DE": {},
            "FR": {},
        }
        zone_neighbours = config.generate_zone_neighbours(zones, exchanges)
        self.assertDictEqual(zone_neighbours, {"DE": ["FR"], "FR": ["DE"]})

    def test_generate_zone_neighbours_one_country_one_subzone(self):
        exchanges = {
            "DE->SE-SE4": {"parsers": {"exchange": "source"}},
        }
        zones = {
            "DE": {},
            "SE": {
                "subZoneNames": ["SE-SE4"],
            },
            "SE-SE4": {},
        }
        zone_neighbours = config.generate_zone_neighbours(zones, exchanges)
        self.assertDictEqual(zone_neighbours, {"DE": ["SE-SE4"], "SE-SE4": ["DE"]})

    def test_generate_zone_neighbours_two_subzones(self):
        exchanges = {
            "NO-NO1->SE-SE3": {"parsers": {"exchange": "source"}},
            "NO-NO3->SE-SE2": {"parsers": {"exchange": "source"}},
            "NO-NO4->SE-SE1": {"parsers": {"exchange": "source"}},
            "NO-NO4->SE-SE2": {"parsers": {"exchange": "source"}},
        }
        zones = {
            "NO": {
                "subZoneNames": ["NO-NO1", "NO-NO2", "NO-NO3", "NO-NO4", "NO-NO5"],
            },
            "NO-NO1": {},
            "NO-NO2": {},
            "NO-NO3": {},
            "NO-NO4": {},
            "NO-NO5": {},
            "SE": {
                "subZoneNames": ["SE-SE1", "SE-SE2", "SE-SE3", "SE-SE4"],
            },
            "SE-SE1": {},
            "SE-SE2": {},
            "SE-SE3": {},
            "SE-SE4": {},
        }
        zone_neighbours = config.generate_zone_neighbours(zones, exchanges)
        self.assertDictEqual(
            zone_neighbours,
            {
                "NO-NO1": ["SE-SE3"],
                "NO-NO3": ["SE-SE2"],
                "NO-NO4": ["SE-SE1", "SE-SE2"],
                "SE-SE1": ["NO-NO4"],
                "SE-SE2": ["NO-NO3", "NO-NO4"],
                "SE-SE3": ["NO-NO1"],
            },
        )

    def test_generate_zone_neighbours_two_subzones_from_same(self):
        exchanges = {
            "SE-SE1->SE-SE2": {"parsers": {"exchange": "source"}},
        }
        zones = {
            "SE": {
                "subZoneNames": ["SE-SE1", "SE-SE2", "SE-SE3", "SE-SE4"],
            },
            "SE-SE1": {},
            "SE-SE2": {},
            "SE-SE3": {},
            "SE-SE4": {},
        }
        zone_neighbours = config.generate_zone_neighbours(zones, exchanges)
        self.assertDictEqual(
            zone_neighbours,
            {"SE-SE1": ["SE-SE2"], "SE-SE2": ["SE-SE1"]},
        )

    def test_generate_zone_neighbours_GB(self):
        # That's an interesting case as GB has islands, which are not subzones
        # It means that GB->GB-NIR are valid exchanges and that
        # GB and GB-NIR are neighbours
        exchanges = {
            "GB->GB-NIR": {"parsers": {"exchange": "source"}},
            "GB->GB-ORK": {"parsers": {"exchange": "source"}},
        }
        zones = {
            "GB": {},
            "GB-NIR": {},
            "GB-ORK": {},
        }
        zone_neighbours = config.generate_zone_neighbours(zones, exchanges)
        self.assertDictEqual(
            zone_neighbours,
            {"GB": ["GB-NIR", "GB-ORK"], "GB-NIR": ["GB"], "GB-ORK": ["GB"]},
        )

    def test_generate_zone_neighbours_no_exchange_parser(self):
        exchanges = {
            "DE->FR": {"parsers": {}},
        }
        zones = {
            "DE": {},
            "FR": {},
        }
        zone_neighbours = config.generate_zone_neighbours(zones, exchanges)
        self.assertDictEqual(zone_neighbours, {})

    def test_ZONE_NEIGHBOURS(self):
        zone_neighbours = config.generate_zone_neighbours(config.ZONES_CONFIG, config.EXCHANGES_CONFIG)
        self.assertIn("DK-DK1", zone_neighbours.keys())
        dk_neighbours = zone_neighbours["DK-DK1"]

        self.assertGreater(
            len(dk_neighbours), 1, "expected a few neighbours for DK-DK1"
        )

    # This is temporary until we definitely remove the zones.json file
    def test_ZONES(self):
        zones = json.load(open(CONFIG_DIR.joinpath("zones.json"), encoding="utf-8"))
        # Not comparing against ZONE_CONFIG as pydantic adds "key" to each zone
        zone_diff = DeepDiff(zones, config.zones_config)
        assert (
            zone_diff == {}
        ), f"Zones config does not match: {list(zone_diff.values())[0]}"

    # Same for exchanges.json
    def test_EXCHANGES(self):
        exchanges = json.load(
            open(CONFIG_DIR.joinpath("exchanges.json"), encoding="utf-8")
        )
        exchange_diff = DeepDiff(exchanges, config.exchanges_config)
        assert (
            exchange_diff == {}
        ), f"Exchanges config does not match: {list(exchange_diff.values())[0]}"

    # Same for co2eq_parameters.json
    def test_CO2EQ_PARAMETERS(self):
        co2eq_parameters_all = json.load(
            open(CONFIG_DIR.joinpath("co2eq_parameters_all.json"), encoding="utf-8")
        )
        co2eq_parameters_lifecycle = {
            **co2eq_parameters_all,
            **json.load(
                open(
                    CONFIG_DIR.joinpath("co2eq_parameters_lifecycle.json"),
                    encoding="utf-8",
                )
            ),
        }
        co2eq_parameters_direct = {
            **co2eq_parameters_all,
            **json.load(
                open(
                    CONFIG_DIR.joinpath("co2eq_parameters_direct.json"),
                    encoding="utf-8",
                )
            ),
        }
        co2eq_parameters_direct_diff = DeepDiff(
            co2eq_parameters_direct, config.CO2EQ_PARAMETERS_DIRECT
        )
        assert (
            co2eq_parameters_direct_diff == {}
        ), f"CO2EQ parameters direct config does not match: {list(co2eq_parameters_direct_diff.values())[0]}"
        co2eq_parameters_lifecycle_diff = DeepDiff(
            co2eq_parameters_lifecycle, config.CO2EQ_PARAMETERS_LIFECYCLE
        )
        assert (
            co2eq_parameters_lifecycle_diff == {}
        ), f"CO2EQ parameters lifecycle config does not match: {list(co2eq_parameters_lifecycle_diff.values())[0]}"


if __name__ == "__main__":
    unittest.main(buffer=True)
