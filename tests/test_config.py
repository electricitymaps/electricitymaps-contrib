import unittest
from pathlib import Path

from electricitymap.contrib.config import (
    EXCHANGES_CONFIG,
    ZONES_CONFIG,
    generate_zone_neighbours,
)


class ConfigTestcase(unittest.TestCase):
    def test_generate_zone_neighbours_two_countries(self):
        exchanges = {
            "DE->FR": {"parsers": {"exchange": "source"}},
        }
        zones = {
            "DE": {},
            "FR": {},
        }
        zone_neighbours = generate_zone_neighbours(zones, exchanges)
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
            "SE": {
                "subZoneNames": ["SE-SE1", "SE-SE2", "SE-SE3", "SE-SE4"],
            },
            "SE-SE1": {},
            "SE-SE2": {},
            "SE-SE3": {},
            "SE-SE4": {},
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
        zones = {
            "GB": {},
            "GB-NIR": {},
            "GB-ORK": {},
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
        zones = {
            "DE": {},
            "FR": {},
        }
        zone_neighbours = generate_zone_neighbours(zones, exchanges)
        self.assertDictEqual(zone_neighbours, {})

    def test_ZONE_NEIGHBOURS(self):
        zone_neighbours = generate_zone_neighbours(ZONES_CONFIG, EXCHANGES_CONFIG)
        self.assertIn("DK-DK1", zone_neighbours.keys())
        dk_neighbours = zone_neighbours["DK-DK1"]

        self.assertGreater(
            len(dk_neighbours), 1, "expected a few neighbours for DK-DK1"
        )


if __name__ == "__main__":
    unittest.main(buffer=True)
