#!/usr/bin/env python3

import json
import unittest

REQUIRED_FALLBACK_KEYS = [
    'powerOriginRatios',
    'carbonIntensity',
]


class Co2EqTestcase(unittest.TestCase):
    def setUp(self):
        with open('config/co2eq_parameters.json') as f:
            self.co2eq_parameters = json.load(f)

    def test_consistent_fallback_zone_mixes(self):
        for (zone_id, zone_obj) in self.co2eq_parameters['fallbackZoneMixes']['zoneOverrides'].items():
            for k in REQUIRED_FALLBACK_KEYS:
                self.assertIsNotNone(zone_obj.get(k), msg=f"zone={zone_id},key={k}")
