import logging
import unittest
from importlib import resources

from freezegun import freeze_time
from requests import Session
from requests_mock import GET, Adapter
from testfixtures import LogCapture

from parsers import SG


class TestSolar(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger("test")
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)
        self.adapter.register_uri(
            GET,
            SG.SOLAR_URL,
            content=resources.files("parsers.test.mocks")
            .joinpath("SG_ema_gov_sg_solar_map.png")
            .read_bytes(),
        )

    @freeze_time("2021-12-23 03:21:00")
    def test_works_when_nonzero(self):
        self.adapter.register_uri(
            GET,
            SG.SOLAR_URL,
            content=resources.files("parsers.test.mocks")
            .joinpath("SG_ema_gov_sg_solar_map_nonzero.png")
            .read_bytes(),
        )
        power = SG.get_solar(self.session, logger=self.logger)
        self.assertEqual(power, 350.55)

    @freeze_time("2021-12-23 15:12:00")
    def test_works_when_zero(self):
        power = SG.get_solar(self.session, logger=self.logger)
        self.assertEqual(power, 0.0)

    @freeze_time("2024-08-06 15:12:00")
    def test_ignore_data_older_than_one_hour(self):
        with LogCapture():
            power = SG.get_solar(self.session, logger=self.logger)
        self.assertIsNone(power)

    @freeze_time("2021-12-23 15:06:00")
    def test_allow_remote_clock_to_be_slightly_ahead(self):
        power = SG.get_solar(self.session, logger=self.logger)
        self.assertEqual(power, 0.0)


if __name__ == "__main__":
    unittest.main()
