#!/usr/bin/env python3

"""Tests for US_HI.py"""

import arrow
import unittest
from arrow import get
from datetime import datetime
from parsers import US_HI
from pkg_resources import resource_string
from requests import Session
from requests_mock import Adapter
import logging
from testfixtures import LogCapture
from freezegun import freeze_time


class TestUSHI(unittest.TestCase):
    def setUp(self):
        """ Make a session containing mocked input data. """
        self.logger = logging.getLogger('test')
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount('https://', self.adapter)
        response_data = resource_string('parsers.test.mocks', 'US_HI.htm')
        self.adapter.register_uri('GET', US_HI.URL, content=response_data)

    @freeze_time('2021-11-16 00:30:00')
    def test_fetch_production_realtime(self):
        data = US_HI.fetch_production(session=self.session, logger=self.logger)
        self.assertIsInstance(data, dict)
        self.assertEqual(data['zoneKey'], 'US-HI-OA')
        self.assertEqual(data['production']['coal'], 179.2)
        expected_dt = get(datetime(2021, 11, 15, 14, 30), 'US/Hawaii').datetime
        self.assertEqual(data['datetime'], expected_dt)
        # parser doesn't cover historic data yet:
        self.assertRaises(NotImplementedError, US_HI.fetch_production, target_datetime=arrow.get().shift(hours=-4))
        # The production values (MW) should never be negative:
        smallest_prod_mw = min(data['production'].values())
        self.assertTrue(smallest_prod_mw >= 0)

    @freeze_time('2021-11-16 02:30:01')
    def test_fetch_production_outdated(self):
        # raise a log warning and return None if data retrieved is more than 2 hours old:
        with LogCapture() as log:
            old_data = US_HI.fetch_production(session=self.session, logger=self.logger)
        self.assertIsNone(old_data)
        self.assertEqual(len(log.records), 1)


if __name__ == '__main__':
    unittest.main()