import logging
import unittest

from freezegun import freeze_time
from pkg_resources import resource_string
from requests import Session
from requests_mock import Adapter
from testfixtures import LogCapture

from parsers import SG


class TestSolar(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger("test")
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)
        response_data = resource_string(
            "parsers.test.mocks", "SG_ema_gov_sg_solar_map.png"
        )
        self.adapter.register_uri("GET", SG.SOLAR_URL, content=response_data)

    @freeze_time("2021-12-23 03:21:00")
    def test_works_when_nonzero(self):
        response_data = resource_string(
            "parsers.test.mocks", "SG_ema_gov_sg_solar_map_nonzero.png"
        )
        self.adapter.register_uri("GET", SG.SOLAR_URL, content=response_data)
        power = SG.get_solar(self.session, logger=self.logger)
        self.assertEqual(power, 69.64)

    @freeze_time("2021-12-23 15:12:00")
    def test_works_when_zero(self):
        power = SG.get_solar(self.session, logger=self.logger)
        self.assertEqual(power, 0.0)

    @freeze_time("2021-12-24 15:12:00")
    def test_ignore_data_older_than_one_hour(self):
        with LogCapture() as log:
            power = SG.get_solar(self.session, logger=self.logger)
        self.assertIsNone(power)

    @freeze_time("2021-12-23 15:06:00")
    def test_allow_remote_clock_to_be_slightly_ahead(self):
        power = SG.get_solar(self.session, logger=self.logger)
        self.assertEqual(power, 0.0)


if __name__ == "__main__":
    unittest.main()
