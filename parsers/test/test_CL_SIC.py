#!/usr/bin/env python3

"""Tests for CL_SIC.py"""

import unittest
import arrow
from datetime import datetime
from parsers import CL_SIC


class TestCLSIC(unittest.TestCase):
    """Patches in a fake response from the data source to allow repeatable testing."""

    def test_cleaner(self):
        fake_chunk = {'fecha': '2018-12-01',
                      'potencia_sum': 434.894898,
                      'intervalos': 0,
                      'tramo_nombre': 'Alto Jahuel - Ancoa 500 kV C1 / Alto Jahuel 500 kV'}

        clean_fake_chunk = CL_SIC.cleaner(fake_chunk)
        expected_dt = arrow.get(datetime(2018, 12, 1), 'Chile/Continental').datetime
        # We expect to have to reverse this exchange.
        expected_flow = -434.894898
        self.assertEqual(clean_fake_chunk, (expected_dt, expected_flow))

    def test_group_and_consolidate(self):
        d1 = arrow.get(datetime(2018, 12, 1, 0, 0), 'Chile/Continental').datetime
        d2 = arrow.get(datetime(2018, 12, 1, 5, 0), 'Chile/Continental').datetime
        fake_mess = [(d1, -434.894898), (d2, -439.572313), (d1, -336.491192), (d2, -530.588313)]

        clean_fake_mess = CL_SIC.group_and_consolidate(fake_mess)
        expected_result = [(d1, -771.38609),
                           (d2, -970.160626)]
        self.assertEqual(clean_fake_mess, expected_result)


if __name__ == '__main__':
    unittest.main(buffer=True)
