#!/usr/bin/env python3

"""Tests for US_HI.py"""

import logging
import unittest
from datetime import datetime

import arrow
from freezegun import freeze_time
from pkg_resources import resource_string
from requests import Session
from requests_mock import Adapter

from parsers import US_HI


class TestUSHI(unittest.TestCase):
    def setUp(self):
        """Make a session containing mocked input data."""
        self.logger = logging.getLogger("test")
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)

        realtime_response_data = resource_string("parsers.test.mocks", "US_HI.htm")
        self.adapter.register_uri(
            "GET", US_HI.BASE_URL + "limit=1", content=realtime_response_data
        )

        hist_response_data = resource_string("parsers.test.mocks", "US_HI_hist.htm")
        hist_dt = arrow.get("2013/12/04 16:30").format("YYYY-MM-DD")
        self.adapter.register_uri(
            "GET", US_HI.BASE_URL + f"date={hist_dt}", content=hist_response_data
        )

    @freeze_time("2021-11-16 00:30:00")
    def test_fetch_production_realtime(self):
        data = US_HI.fetch_production(session=self.session, logger=self.logger)
        self.assertIsInstance(data, dict)
        self.assertEqual(data["zoneKey"], "US-HI-OA")
        self.assertEqual(data["production"]["coal"], 179.2)
        expected_dt = arrow.get(datetime(2021, 11, 15, 14, 30), "US/Hawaii").datetime
        self.assertEqual(data["datetime"], expected_dt)
        # The production values (MW) should never be negative:
        smallest_prod_mw = min(data["production"].values())
        self.assertTrue(smallest_prod_mw >= 0)

    @freeze_time("2021-11-16 00:30:00")
    def test_fetch_production_historical(self):
        """Testing historical data with request for 2013-12-04, 6:30am HST. This is the earliest valid target_datetime for the API."""
        test_target_dt = arrow.get("2013/12/04 16:30").datetime
        data = US_HI.fetch_production(
            session=self.session, logger=self.logger, target_datetime=test_target_dt
        )
        self.assertIsInstance(data, dict)
        self.assertEqual(data["zoneKey"], "US-HI-OA")
        self.assertEqual(data["production"]["oil"], 694.3)
        # the datetime returned should be within 2 hours after hist_dt (in HST)
        expected_dt = arrow.get("2013/12/04 08:30", tzinfo="US/Hawaii").datetime
        self.assertEqual(data["datetime"], expected_dt)
        smallest_prod_mw = min(data["production"].values())
        self.assertTrue(smallest_prod_mw >= 0)

    @freeze_time("2021-11-16 00:30:00")
    def test_fetch_production_outdated(self):
        """Testing historical data with request for 2013-12-04, 6:29am HST. The closest data found is > 2 hours later, so
        this request returns None."""
        test_target_dt = arrow.get("2013/12/04 16:29").datetime
        old_data = US_HI.fetch_production(
            session=self.session, logger=self.logger, target_datetime=test_target_dt
        )
        self.assertIsNone(old_data)


if __name__ == "__main__":
    unittest.main()
