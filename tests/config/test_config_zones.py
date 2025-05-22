import unittest
from pathlib import Path
from typing import Any

from electricitymap.contrib.config import (
    generate_all_neighbours,
    generate_zone_neighbours,
    zone_bounding_boxes,
    zone_parents,
)
from electricitymap.contrib.lib.types import ZoneKey

CONFIG_DIR = Path(__file__).parent.parent.joinpath("config").resolve()


class TestConfigZones(unittest.TestCase):
    def test_bounding_boxes_basic(self):
        zones: dict[ZoneKey, Any] = {
            ZoneKey("AD"): {
                "bounding_box": [[0.906, 41.928], [2.265, 43.149]],
            },
            ZoneKey("XX"): {},
        }
        self.assertDictEqual(
            zone_bounding_boxes(zones),
            {
                ZoneKey("AD"): [[0.906, 41.928], [2.265, 43.149]],
            },
        )

    def test_zone_parents_basic(self):
        zones: dict[ZoneKey, Any] = {
            ZoneKey("DE"): {},
            ZoneKey("SE"): {
                "subZoneNames": ["SE-SE1", "SE-SE2"],
            },
            ZoneKey("SE-SE1"): {},
            ZoneKey("SE-SE2"): {},
        }
        self.assertDictEqual(zone_parents(zones), {"SE-SE1": "SE", "SE-SE2": "SE"})

    def test_generate_all_neighbours_basic(self):
        # generate_all_neighbours returns all neighbours regardless of
        # granularity, i.e. it doesn't matter whether zones have subzones.
        exchanges = {
            "DE->SE": {"parsers": {"exchange": "source"}},
            "SE->DE": {"parsers": {"exchange": "source"}},
        }
        self.assertDictEqual(
            generate_all_neighbours(exchanges), {"DE": ["SE"], "SE": ["DE"]}
        )

    def test_generate_zone_neighbours_two_countries(self):
        exchanges = {
            "DE->FR": {"parsers": {"exchange": "source"}},
        }
        zones = {
            ZoneKey("DE"): {},
            ZoneKey("FR"): {},
        }
        zone_neighbours = generate_zone_neighbours(zones, exchanges)
        self.assertDictEqual(
            zone_neighbours, {ZoneKey("DE"): ["FR"], ZoneKey("FR"): ["DE"]}
        )

    def test_generate_zone_neighbours_one_country_one_subzone(self):
        exchanges = {
            "DE->SE-SE4": {"parsers": {"exchange": "source"}},
        }
        zones: dict[ZoneKey, Any] = {
            ZoneKey("DE"): {},
            ZoneKey("SE"): {
                "subZoneNames": ["SE-SE4"],
            },
            ZoneKey("SE-SE4"): {},
        }
        zone_neighbours = generate_zone_neighbours(zones, exchanges)
        self.assertDictEqual(zone_neighbours, {"DE": ["SE-SE4"], "SE-SE4": ["DE"]})

    def test_generate_zone_neighbours_two_subzones(self):
        exchanges = {
            "NO-NO1->SE-SE3": {"parsers": {"exchange": "source"}},
            "NO-NO3->SE-SE2": {"parsers": {"exchange": "source"}},
            "NO-NO4->SE-SE1": {"parsers": {"exchange": "source"}},
            "NO-NO4->SE-SE2": {"parsers": {"exchange": "source"}},
        }
        zones = {
            ZoneKey("NO"): {
                "subZoneNames": ["NO-NO1", "NO-NO2", "NO-NO3", "NO-NO4", "NO-NO5"],
            },
            ZoneKey("NO-NO1"): {},
            ZoneKey("NO-NO2"): {},
            ZoneKey("NO-NO3"): {},
            ZoneKey("NO-NO4"): {},
            ZoneKey("NO-NO5"): {},
            ZoneKey("SE"): {
                "subZoneNames": ["SE-SE1", "SE-SE2", "SE-SE3", "SE-SE4"],
            },
            ZoneKey("SE-SE1"): {},
            ZoneKey("SE-SE2"): {},
            ZoneKey("SE-SE3"): {},
            ZoneKey("SE-SE4"): {},
        }
        zone_neighbours = generate_zone_neighbours(zones, exchanges)
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
            ZoneKey("SE"): {
                "subZoneNames": ["SE-SE1", "SE-SE2", "SE-SE3", "SE-SE4"],
            },
            ZoneKey("SE-SE1"): {},
            ZoneKey("SE-SE2"): {},
            ZoneKey("SE-SE3"): {},
            ZoneKey("SE-SE4"): {},
        }
        zone_neighbours = generate_zone_neighbours(zones, exchanges)
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
        zones: dict[ZoneKey, Any] = {
            ZoneKey("GB"): {},
            ZoneKey("GB-NIR"): {},
            ZoneKey("GB-ORK"): {},
        }
        zone_neighbours = generate_zone_neighbours(zones, exchanges)
        self.assertDictEqual(
            zone_neighbours,
            {"GB": ["GB-NIR", "GB-ORK"], "GB-NIR": ["GB"], "GB-ORK": ["GB"]},
        )

    def test_generate_zone_neighbours_no_exchange_parser(self):
        exchanges = {
            "DE->FR": {"parsers": {}},
        }
        zones: dict[ZoneKey, Any] = {
            ZoneKey("DE"): {},
            ZoneKey("FR"): {},
        }
        zone_neighbours = generate_zone_neighbours(zones, exchanges)
        self.assertDictEqual(zone_neighbours, {})
