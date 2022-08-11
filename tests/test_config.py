import json
import unittest
from pathlib import Path

from deepdiff import DeepDiff

from electricitymap.contrib import config

CONFIG_DIR = Path(__file__).parent.parent.joinpath("config").resolve()


class ConfigTestcase(unittest.TestCase):
    def test_ZONE_NEIGHBOURS(self):
        self.assertIn("DK-DK1", config.ZONE_NEIGHBOURS.keys())
        dk_neighbours = config.ZONE_NEIGHBOURS["DK-DK1"]

        self.assertGreater(
            len(dk_neighbours), 1, "expected a few neighbours for DK-DK1"
        )
        self.assertEqual(
            sorted(dk_neighbours), dk_neighbours, "neighbours should be sorted"
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
