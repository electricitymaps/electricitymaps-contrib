from datetime import datetime
from unittest import TestCase

import freezegun
from arrow import get
from requests import Session
from requests_mock import ANY, Adapter

from electricitymap.contrib.config import ZoneKey
from parsers import US_PREPA


class TestFetchProduction(TestCase):
    def setUp(self):
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)
        data = open("parsers/test/mocks/US_PREPA_dataSource.js", "rb")
        self.adapter.register_uri(ANY, ANY, content=data.read())

    @freezegun.freeze_time("2021-01-01 00:00:00")
    def test_fetch_production_PR(self):

        data = US_PREPA.fetch_production(ZoneKey("US-PR"), self.session)

        with self.subTest():
            self.assertEqual(data["zoneKey"], "US-PR")
        with self.subTest():
            self.assertEqual(data["source"], "aeepr.com")
        with self.subTest():
            expected_dt = get(
                datetime(2023, 4, 25, 15, 11, 5), "America/Puerto_Rico"
            ).datetime
            self.assertEqual(data["datetime"], expected_dt)
        # % information is rounded to nearest %, use delta of 1%
        total_gen = 2119
        with self.subTest():
            self.assertAlmostEqual(
                data["production"]["coal"], 395.0, delta=total_gen / 100
            )
        with self.subTest():
            self.assertAlmostEqual(
                data["production"]["gas"], 1017.12, delta=total_gen / 100
            )
        with self.subTest():
            self.assertAlmostEqual(
                data["production"]["solar"], 80.0, delta=total_gen / 100
            )
