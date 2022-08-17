import unittest
from pathlib import Path

from electricitymap.contrib import config


class ConfigTestcase(unittest.TestCase):
    def test_generate_zone_neighbours_two_countries(self):
        exchanges = {
            "DE->FR": {},
        }
        zones = {
            "DE": {},
            "FR": {},
        }
        zone_neighbours = config.generate_zone_neighbours(exchanges, zones)
        self.assertDictEqual(zone_neighbours, {"DE": ["FR"], "FR": ["DE"]})

    def test_generate_zone_neighbours_one_country_one_subzone(self):
        exchanges = {
            "DE->SE-SE4": {},
        }
        zones = {
            "DE": {},
            "SE": {
                "subZoneNames": ["SE-SE4"],
            },
            "SE-SE4": {},
        }
        zone_neighbours = config.generate_zone_neighbours(exchanges, zones)
        self.assertDictEqual(
            zone_neighbours, {"DE": ["SE", "SE-SE4"], "SE": ["DE"], "SE-SE4": ["DE"]}
        )

    def test_generate_zone_neighbours_two_subzones(self):
        exchanges = {
            "NO-NO1->SE-SE3": {},
            "NO-NO3->SE-SE2": {},
            "NO-NO4->SE-SE1": {},
            "NO-NO4->SE-SE2": {},
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
        zone_neighbours = config.generate_zone_neighbours(exchanges, zones)
        self.assertDictEqual(
            zone_neighbours,
            {
                "NO": ["SE", "SE-SE1", "SE-SE2", "SE-SE3"],
                "NO-NO1": ["SE", "SE-SE3"],
                "NO-NO3": ["SE", "SE-SE2"],
                "NO-NO4": ["SE", "SE-SE1", "SE-SE2"],
                "SE": ["NO", "NO-NO1", "NO-NO3", "NO-NO4"],
                "SE-SE1": ["NO", "NO-NO4"],
                "SE-SE2": ["NO", "NO-NO3", "NO-NO4"],
                "SE-SE3": ["NO", "NO-NO1"],
            },
        )

    def test_generate_zone_neighbours_two_subzones_from_same(self):
        exchanges = {
            "SE-SE1->SE-SE2": {},
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
        zone_neighbours = config.generate_zone_neighbours(exchanges, zones)
        self.assertDictEqual(
            zone_neighbours,
            {"SE-SE1": ["SE-SE2"], "SE-SE2": ["SE-SE1"]},
        )

    def test_ZONE_NEIGHBOURS(self):
        self.assertIn("DK-DK1", config.ZONE_NEIGHBOURS.keys())
        dk_neighbours = config.ZONE_NEIGHBOURS["DK-DK1"]

        self.assertGreater(
            len(dk_neighbours), 1, "expected a few neighbours for DK-DK1"
        )
        self.assertEqual(
            sorted(dk_neighbours), dk_neighbours, "neighbours should be sorted"
        )


if __name__ == "__main__":
    unittest.main(buffer=True)
